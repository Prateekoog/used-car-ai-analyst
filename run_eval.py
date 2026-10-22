"""
Step 2 — Ask an LLM each business question, run the SQL it writes,
and check the result against the answer from a hand-written gold query.

Run:  python run_eval.py                      (all 3 prompt versions, Gemini)
      python run_eval.py --versions v1 v3      (only some versions)
      python run_eval.py --provider mock       (pipeline check: model = gold SQL, expect 100%)
Out:  results/run_<time>.csv  and  results/summary_<time>.md
"""
import argparse
import csv
import json
import os
import re
import sqlite3
import time
from datetime import datetime

from prompts import build_prompt

DB_URI = "file:used_cars.db?mode=ro"   # read-only: generated SQL cannot change data
REL_TOL = 0.005                        # numbers within 0.5% count as equal


# ---------- calling the model ----------
def call_gemini(prompt, model):
    from google import genai           # pip install google-genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    for attempt in range(4):
        try:
            resp = client.models.generate_content(
                model=model, contents=prompt, config={"temperature": 0})
            return resp.text
        except Exception as err:       # rate limit etc. -> wait and retry
            if attempt == 3:
                raise
            print(f"   retrying after error: {str(err)[:80]}")
            time.sleep(20 * (attempt + 1))


def extract_sql(text):
    text = re.sub(r"```(?:sql)?", "", text, flags=re.I).strip()
    return text.split(";")[0].strip()


# ---------- running SQL safely ----------
def run_sql(conn, sql):
    if not re.match(r"^\s*(select|with)\b", sql, re.I):
        raise ValueError("only SELECT queries are allowed")
    deadline = time.time() + 10
    conn.set_progress_handler(lambda: time.time() > deadline, 10_000)  # 10 s timeout
    return conn.execute(sql).fetchall()


# ---------- comparing results ----------
def same_value(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= REL_TOL * max(1.0, abs(a), abs(b))
    return str(a).strip().lower() == str(b).strip().lower()


def row_contains(model_row, gold_row):
    """Every gold value must appear in the model row (extra columns are fine)."""
    pool = list(model_row)
    for g in gold_row:
        hit = next((i for i, v in enumerate(pool) if same_value(v, g)), None)
        if hit is None:
            return False
        pool.pop(hit)
    return True


def compare(model_rows, gold_rows):
    """Order-insensitive. Same number of rows, each gold row matched once."""
    if len(model_rows) != len(gold_rows):
        return "wrong_row_count"
    unused = list(model_rows)
    for g in gold_rows:
        hit = next((i for i, m in enumerate(unused) if row_contains(m, g)), None)
        if hit is None:
            return "wrong_values"
        unused.pop(hit)
    return "pass"


# ---------- main loop ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="gemini", choices=["gemini", "mock"])
    ap.add_argument("--model", default="gemini-2.5-flash")
    ap.add_argument("--versions", nargs="+", default=["v1", "v2", "v3"])
    ap.add_argument("--sleep", type=float, default=6, help="seconds between calls (free-tier limits)")
    args = ap.parse_args()

    questions = json.load(open("questions.json"))
    conn = sqlite3.connect(DB_URI, uri=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    os.makedirs("results", exist_ok=True)
    rows = []

    for version in args.versions:
        for q in questions:
            gold = run_sql(conn, q["gold_sql"])
            start = time.time()
            if args.provider == "mock":
                raw = q["gold_sql"]
            else:
                raw = call_gemini(build_prompt(version, q["question"]), args.model)
                time.sleep(args.sleep)
            latency = round(time.time() - start, 2)
            sql = extract_sql(raw)
            try:
                result = run_sql(conn, sql)
                status, error = compare(result, gold), ""
            except Exception as err:
                result, status, error = [], "sql_error", str(err)[:200]
            print(f"{version} Q{q['id']:>2} {status:16s} {q['question'][:60]}")
            rows.append({
                "version": version, "id": q["id"], "category": q["category"],
                "question": q["question"], "status": status, "latency_s": latency,
                "generated_sql": sql, "error": error,
                "model_result": str(result[:5]), "gold_result": str(gold[:5]),
                "root_cause": "",   # fill in by hand for every failure
            })

    csv_path = f"results/run_{stamp}.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    write_summary(rows, args, stamp)
    print(f"\nSaved {csv_path}")


def write_summary(rows, args, stamp):
    lines = [f"# Run {stamp} — provider: {args.provider}, model: {args.model}\n",
             "| Version | Accuracy | sql_error | wrong_row_count | wrong_values | Avg latency (s) |",
             "|---|---|---|---|---|---|"]
    cats = sorted({r["category"] for r in rows})
    by_cat = ["", "| Version | " + " | ".join(cats) + " |", "|---|" + "---|" * len(cats)]
    for v in args.versions:
        vr = [r for r in rows if r["version"] == v]
        n = len(vr)
        passed = sum(r["status"] == "pass" for r in vr)
        count = lambda s: sum(r["status"] == s for r in vr)
        avg_lat = sum(r["latency_s"] for r in vr) / n
        lines.append(f"| {v} | {passed}/{n} ({100 * passed / n:.0f}%) | {count('sql_error')} | "
                     f"{count('wrong_row_count')} | {count('wrong_values')} | {avg_lat:.1f} |")
        cells = []
        for c in cats:
            cr = [r for r in vr if r["category"] == c]
            cells.append(f"{sum(r['status'] == 'pass' for r in cr)}/{len(cr)}")
        by_cat.append(f"| {v} | " + " | ".join(cells) + " |")
    text = "\n".join(lines + by_cat) + "\n"
    with open(f"results/summary_{stamp}.md", "w") as f:
        f.write(text)
    print("\n" + text)


if __name__ == "__main__":
    main()

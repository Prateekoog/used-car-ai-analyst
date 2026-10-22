# Used-Car AI Analyst — can an LLM answer pricing questions correctly?

Business teams ask metric questions in plain English ("What share of premium cars are automatic?").
An LLM can write the SQL in seconds, but the real question is **whether the number is right**.
This project builds a small text-to-SQL analyst over Indian used-car listings and **measures** its accuracy,
then tests what context the model needs to get answers right.

## How it works
1. `build_db.py` cleans the raw CarDekho listings and loads them into SQLite.
2. `questions.json` holds 30 business questions, each with a **gold SQL** query checked by hand.
3. `run_eval.py` sends each question to an LLM (Gemini), runs the returned SQL **read-only**,
   and compares the result with the gold result (order-insensitive, 0.5% numeric tolerance, extra columns allowed).
4. Every run is logged to `results/` with the generated SQL, status and a hand-written root cause for each failure.

## Experiment: what context does the model need?
Each prompt version adds one layer of context, so the change in accuracy shows what that layer is worth.

| Version | Context given to the model |
|---|---|
| v1 | Table and column names only |
| v2 | + column descriptions and allowed values |
| v3 | + business definitions (premium, budget, high-mileage, car age, "dealers") |

Note: v3's definitions are the same rules the gold queries use. That is the point. v3 measures the value of
writing business definitions down, not the model's raw ability.

## Results  <!-- FILL from results/summary_*.md -->
| Version | Accuracy | SQL errors | Wrong row count | Wrong values |
|---|---|---|---|---|
| v1 | __/30 | | | |
| v2 | __/30 | | | |
| v3 | __/30 | | | |

Model: `______`  ·  Date: `______`

## What went wrong, and why  <!-- FILL: your own analysis of the failures -->
- ...
- ...

## Data cleaning
- Raw file: 8,128 rows. **1,202 exact duplicates removed** → 6,926 listings.
- Brand and model parsed from the listing title (fixed two-word brands such as "Land Rover").
- Unit text converted to numbers (`"23.4 kmpl"` → 23.4, `"1248 CC"` → 1248). Fuel efficiency is in kmpl for
  petrol/diesel and km/kg for CNG/LPG, so they are not compared directly.
- ~208 listings have no engine, power or seat data (kept as NULL).

Data: "Vehicle dataset from CarDekho" (Kaggle, nehalbirla), `Car details v3.csv`.

## Run it
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python build_db.py                    # builds used_cars.db
pytest -q                             # checks the answer checker
python run_eval.py --provider mock    # pipeline check: should be 30/30 for every version
export GEMINI_API_KEY=your_key        # free key from aistudio.google.com
python run_eval.py                    # real run: 3 versions x 30 questions
```

## Limitations
- 30 questions is a small test set; one question is ~3 percentage points.
- Auto-checking can't judge a question that has two reasonable readings — those are reviewed by hand in the root-cause column.
- Single model, temperature 0, one run per version.

## How I built this
Built with Claude as an AI pair-programmer, which drafted the code, questions and gold queries.
I reviewed and checked every gold query against the data, ran the experiment and wrote the failure analysis.

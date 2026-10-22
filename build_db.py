"""
Step 1 — Clean the raw CarDekho listings CSV and load it into SQLite.

Run:  python build_db.py
Out:  used_cars.db  (one table: listings)
"""
import sqlite3
import pandas as pd

RAW_CSV = "data/car_details_v3.csv"
DB_PATH = "used_cars.db"

# Brands whose name is two words in the raw "name" column
MULTI_WORD_BRANDS = {"Land": "Land Rover", "Ashok": "Ashok Leyland"}


def number_from(text):
    """'23.4 kmpl' -> 23.4, '1248 CC' -> 1248.0, ' bhp' or NaN -> None."""
    if pd.isna(text):
        return None
    first = str(text).strip().split(" ")[0]
    try:
        return float(first)
    except ValueError:
        return None


def main():
    raw = pd.read_csv(RAW_CSV)
    report = {"raw_rows": len(raw)}

    # 1. Exact duplicate rows add no information and inflate every count
    df = raw.drop_duplicates().copy()
    report["exact_duplicates_removed"] = len(raw) - len(df)

    # 2. Brand and model from the free-text name
    words = df["name"].str.split()
    first = words.str[0]
    df["brand"] = first.map(lambda w: MULTI_WORD_BRANDS.get(w, w))
    df["model"] = [w[2] if w[0] in MULTI_WORD_BRANDS else w[1] for w in words]

    # 3. Text-with-units columns -> numbers
    df["mileage_value"] = df["mileage"].map(number_from)
    df["mileage_unit"] = df["mileage"].str.split(" ").str[1]  # kmpl or km/kg
    df["engine_cc"] = df["engine"].map(number_from)
    df["max_power_bhp"] = df["max_power"].map(number_from)

    report["missing_engine"] = int(df["engine_cc"].isna().sum())
    report["missing_max_power"] = int(df["max_power_bhp"].isna().sum())
    report["km_per_kg_rows"] = int((df["mileage_unit"] == "km/kg").sum())

    out = df[[
        "name", "brand", "model", "year", "selling_price", "km_driven", "fuel",
        "seller_type", "transmission", "owner", "mileage_value", "mileage_unit",
        "engine_cc", "max_power_bhp", "seats",
    ]].reset_index(drop=True)
    out.insert(0, "listing_id", range(1, len(out) + 1))

    with sqlite3.connect(DB_PATH) as conn:
        out.to_sql("listings", conn, if_exists="replace", index=False)

    report["final_rows"] = len(out)
    print("Data-quality report")
    for key, value in report.items():
        print(f"  {key:26s} {value}")


if __name__ == "__main__":
    main()

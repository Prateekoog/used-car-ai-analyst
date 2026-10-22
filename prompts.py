"""
Three prompt versions = three layers of context given to the model.
Each version adds ONE layer, so the accuracy change between versions
shows what that layer is worth.

  v1  schema only (table + column names and types)
  v2  v1 + column descriptions and allowed values
  v3  v2 + business definitions (the "metric dictionary")
"""

SCHEMA = """Table: listings
Columns: listing_id INTEGER, name TEXT, brand TEXT, model TEXT, year INTEGER,
selling_price INTEGER, km_driven INTEGER, fuel TEXT, seller_type TEXT,
transmission TEXT, owner TEXT, mileage_value REAL, mileage_unit TEXT,
engine_cc REAL, max_power_bhp REAL, seats REAL"""

COLUMN_NOTES = """Column descriptions:
- name: full listing title, e.g. 'Maruti Swift Dzire VDI'
- brand: manufacturer, e.g. 'Maruti', 'Hyundai', 'Land Rover'
- model: model name, e.g. 'Swift', 'City', 'Innova'
- year: manufacturing year (1983-2020)
- selling_price: listed price in INR
- km_driven: kilometres the car has been driven (odometer reading)
- fuel: 'Diesel', 'Petrol', 'CNG', 'LPG'
- seller_type: 'Individual', 'Dealer', 'Trustmark Dealer'
- transmission: 'Manual', 'Automatic'
- owner: 'First Owner', 'Second Owner', 'Third Owner', 'Fourth & Above Owner', 'Test Drive Car'
- mileage_value: fuel efficiency; its unit is in mileage_unit
- mileage_unit: 'kmpl' (petrol/diesel) or 'km/kg' (CNG/LPG); NULL if missing
- engine_cc, max_power_bhp, seats: NULL if missing"""

DEFINITIONS = """Business definitions:
- All prices are in Indian rupees. 1 lakh = 100,000.
- The data is a 2020 snapshot. Car age = 2020 - year.
- Premium car: selling_price >= 1,000,000. Budget car: selling_price < 300,000.
- High-mileage car: km_driven > 100,000 (mileage_value is fuel efficiency, not distance).
- "Dealers" means seller_type 'Dealer' and 'Trustmark Dealer' combined.
- Compare fuel efficiency only on rows where mileage_unit = 'kmpl'.
- Return percentages as numbers from 0 to 100."""

INSTRUCTIONS = """You are a data analyst. Write ONE SQLite query that answers the question.
Return only the SQL. No explanation, no markdown."""

CONTEXT = {
    "v1": SCHEMA,
    "v2": SCHEMA + "\n\n" + COLUMN_NOTES,
    "v3": SCHEMA + "\n\n" + COLUMN_NOTES + "\n\n" + DEFINITIONS,
}


def build_prompt(version, question):
    return f"{INSTRUCTIONS}\n\n{CONTEXT[version]}\n\nQuestion: {question}\nSQL:"

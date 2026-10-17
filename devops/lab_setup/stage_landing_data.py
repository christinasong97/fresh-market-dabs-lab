# Databricks notebook source
# MAGIC %md
# MAGIC # Lab admin setup: stage landing data
# MAGIC
# MAGIC Run once per lab workspace **as an admin**, before attendees arrive. This stands in for the
# MAGIC upstream POS system: it is not part of the bundle, because source data is owned by the
# MAGIC source system, not by the team deploying the pipeline.
# MAGIC
# MAGIC For each target catalog it creates `<catalog>.landing.raw` and writes synthetic CSVs:
# MAGIC
# MAGIC | Path | Contents |
# MAGIC |---|---|
# MAGIC | `stores/stores.csv` | 40 stores across MI, OH, IN, IL, KY, WI |
# MAGIC | `products/products.csv` | ~150 products across 8 departments |
# MAGIC | `store_targets/store_targets.csv` | Daily sales target per store |
# MAGIC | `pos_transactions/<date>.csv` | ~60 days of POS line items, with ~0.5% deliberately bad rows |

# COMMAND ----------

dbutils.widgets.text("catalogs", "fresh_market_lab_int,fresh_market_lab_cert,fresh_market_lab_prod")
dbutils.widgets.text("days", "60")
dbutils.widgets.text("lines_per_store_per_day", "120")
dbutils.widgets.dropdown("targets_only", "false", ["false", "true"])

catalogs = [c.strip() for c in dbutils.widgets.get("catalogs").split(",") if c.strip()]
days = int(dbutils.widgets.get("days"))
lines_per_store_per_day = int(dbutils.widgets.get("lines_per_store_per_day"))

# COMMAND ----------

import csv
import io
import random
from datetime import date, datetime, timedelta

random.seed(42)

CITIES = [
    ("Grand Rapids", "MI", "West Michigan"), ("Holland", "MI", "West Michigan"),
    ("Kalamazoo", "MI", "West Michigan"), ("Muskegon", "MI", "West Michigan"),
    ("Lansing", "MI", "Central Michigan"), ("Flint", "MI", "Central Michigan"),
    ("Ann Arbor", "MI", "Southeast Michigan"), ("Detroit", "MI", "Southeast Michigan"),
    ("Troy", "MI", "Southeast Michigan"), ("Traverse City", "MI", "Northern Michigan"),
    ("Toledo", "OH", "Ohio"), ("Columbus", "OH", "Ohio"), ("Dayton", "OH", "Ohio"),
    ("Cincinnati", "OH", "Ohio"), ("Fort Wayne", "IN", "Indiana"),
    ("Indianapolis", "IN", "Indiana"), ("South Bend", "IN", "Indiana"),
    ("Joliet", "IL", "Illinois"), ("Naperville", "IL", "Illinois"),
    ("Louisville", "KY", "Kentucky"), ("Lexington", "KY", "Kentucky"),
    ("Milwaukee", "WI", "Wisconsin"),
]

DEPARTMENTS = {
    "Grocery": (["Cereal", "Pasta", "Snacks", "Canned Goods", "Coffee"], (1.5, 9.0)),
    "Produce": (["Fruit", "Vegetables", "Salad"], (0.8, 6.0)),
    "Dairy": (["Milk", "Cheese", "Yogurt", "Eggs"], (1.2, 7.0)),
    "Meat & Seafood": (["Beef", "Chicken", "Seafood"], (4.0, 22.0)),
    "Bakery": (["Bread", "Donuts", "Cakes"], (2.0, 15.0)),
    "Pharmacy": (["OTC", "Vitamins", "First Aid"], (4.0, 30.0)),
    "General Merchandise": (["Home", "Toys", "Apparel", "Electronics"], (5.0, 120.0)),
    "Garden Center": (["Plants", "Soil", "Tools"], (3.0, 60.0)),
}
PAYMENT_TYPES = ["credit", "debit", "cash", "ebt", "mobile"]


def to_csv(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


stores = []
for i in range(40):
    city, state, region = CITIES[i % len(CITIES)]
    fmt = "Express" if i % 7 == 6 else "Supercenter"
    stores.append([
        100 + i,
        f"Fresh Market {city}" + ("" if i < len(CITIES) else f" #{i // len(CITIES) + 1}"),
        city, state, region, fmt,
        40000 if fmt == "Express" else random.randint(150000, 250000),
        (date(1985, 1, 1) + timedelta(days=random.randint(0, 13000))).isoformat(),
    ])

products = []
pid = 10000
for dept, (cats, (lo, hi)) in DEPARTMENTS.items():
    for cat in cats:
        for n in range(random.randint(5, 7)):
            products.append([pid, f"{cat} item {n + 1}", dept, cat, round(random.uniform(lo, hi), 2)])
            pid += 1

# Each store gets a target near its expected daily sales; some stores are set up to underperform.
weights = {s[0]: (0.35 if s[5] == "Express" else 1.0) * random.uniform(0.8, 1.2) for s in stores}
underperformers = set(random.sample([s[0] for s in stores], 5))

# COMMAND ----------

start = date.today() - timedelta(days=days)
txn_files = {}
baseline_sales = {s[0]: 0.0 for s in stores}
baseline_days = days - 14
for d in range(days):
    day = start + timedelta(days=d)
    weekend = 1.25 if day.weekday() >= 5 else 1.0
    rows = []
    for s in stores:
        store_id = s[0]
        drag = 0.7 if store_id in underperformers and d >= days - 14 else 1.0
        n_lines = int(lines_per_store_per_day * weights[store_id] * weekend * drag)
        for k in range(n_lines):
            p = random.choice(products)
            qty = random.choices([1, 2, 3, 4, 6], [60, 20, 10, 6, 4])[0]
            discount = round(p[4] * qty * random.choice([0, 0, 0, 0.05, 0.1]), 2)
            total = round(p[4] * qty - discount, 2)
            ts = datetime(day.year, day.month, day.day, random.randint(7, 22), random.randint(0, 59), random.randint(0, 59))
            row = [
                f"T{day.strftime('%Y%m%d')}-{store_id}-{k:05d}", store_id, p[0], ts.isoformat(sep=" "),
                qty, p[4], discount, total, random.choice(PAYMENT_TYPES), random.random() < 0.62,
            ]
            r = random.random()
            if r < 0.002:
                row[1] = ""            # missing store_id -> dropped in silver
            elif r < 0.004:
                row[4] = -qty          # negative quantity -> dropped in silver
            elif r < 0.005:
                row[7] = ""            # missing amount -> dropped in silver
            rows.append(row)
            if d < baseline_days:
                baseline_sales[store_id] += total
    txn_files[day.isoformat()] = rows

# Targets: each store's average daily sales before the last two weeks, so the stores that slow
# down in the last two weeks fall below target and get flagged.
targets = [[sid, round(total / baseline_days, -1)] for sid, total in baseline_sales.items()]

TXN_HEADER = ["transaction_id", "store_id", "product_id", "transaction_ts", "quantity",
              "unit_price", "discount_amount", "total_amount", "payment_type", "rewards_member"]
print(f"{len(stores)} stores, {len(products)} products, {sum(len(v) for v in txn_files.values()):,} POS lines")

# COMMAND ----------

for catalog in catalogs:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.landing COMMENT 'Upstream source data (owned by the source system, not the bundle)'")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.landing.raw COMMENT 'POS landing zone'")
    root = f"/Volumes/{catalog}/landing/raw"
    dbutils.fs.put(f"{root}/stores/stores.csv",
                   to_csv(["store_id", "store_name", "city", "state", "region", "store_format", "square_feet", "open_date"], stores), True)
    dbutils.fs.put(f"{root}/products/products.csv",
                   to_csv(["product_id", "product_name", "department", "category", "list_price"], products), True)
    dbutils.fs.put(f"{root}/store_targets/store_targets.csv",
                   to_csv(["store_id", "daily_sales_target"], targets), True)
    if dbutils.widgets.get("targets_only") == "true":
        continue
    for day, rows in txn_files.items():
        dbutils.fs.put(f"{root}/pos_transactions/pos_{day}.csv", to_csv(TXN_HEADER, rows), True)
    print(f"staged {root}")

# step 3: load the storm days into postgres, run the sql files,
# and check the yearly totals against pandas
import sys

import pandas as pd
import psycopg2

import config

storm_days = pd.read_csv(config.CLEAN_FILE, parse_dates=["storm_date"])


def run_sql_file(cursor, name):
    cursor.execute((config.BASE / "sql" / name).read_text())


# make the database if it is not there yet (connect to "postgres" first)
try:
    admin = psycopg2.connect(host=config.DB_HOST, port=config.DB_PORT,
                             dbname="postgres", user=config.DB_USER)
except psycopg2.OperationalError as error:
    sys.exit("Could not connect to PostgreSQL. Is it running, and are the "
             "DB_ settings in config.py right?\n" + str(error))
admin.autocommit = True   # CREATE DATABASE does not work inside a transaction
cursor = admin.cursor()
cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (config.DB_NAME,))
if cursor.fetchone() is None:
    cursor.execute(f"CREATE DATABASE {config.DB_NAME}")
    print("Created database", config.DB_NAME)
admin.close()

connection = psycopg2.connect(host=config.DB_HOST, port=config.DB_PORT,
                              dbname=config.DB_NAME, user=config.DB_USER)
cursor = connection.cursor()

# fresh table, then one row per storm day
run_sql_file(cursor, "create_table.sql")
rows = [(row.storm_date.date(), int(row.year), float(row.damage_usd), int(row.n_records))
        for row in storm_days.itertuples()]
cursor.executemany("INSERT INTO storm_days (storm_date, year, damage_usd, n_records) "
                   "VALUES (%s, %s, %s, %s)", rows)
connection.commit()
print("Rows in the table:", len(rows))

# yearly totals in sql
run_sql_file(cursor, "yearly_totals.sql")
from_sql = pd.DataFrame(cursor.fetchall(),
                        columns=["year", "storm_days", "total_damage_usd"])
from_sql["total_damage_usd"] = from_sql["total_damage_usd"].astype(float)

# same thing in pandas
from_pandas = (storm_days.groupby("year")
               .agg(storm_days=("damage_usd", "size"),
                    total_damage_usd=("damage_usd", "sum"))
               .reset_index())

print("\nYearly totals from SQL:")
print(from_sql.to_string(index=False))

same_years = (from_sql["year"].values == from_pandas["year"].values).all()
same_days = (from_sql["storm_days"].values == from_pandas["storm_days"].values).all()
same_damage = abs(from_sql["total_damage_usd"].values
                  - from_pandas["total_damage_usd"].values).max() < 1

if same_years and same_days and same_damage:
    print("\nSQL and pandas agree.")
else:
    print("\nThey do not agree, something is wrong.")

# ten biggest storm days
run_sql_file(cursor, "top_storm_days.sql")
print("\nThe ten storm days with the most damage:")
for storm_date, damage, share in cursor.fetchall():
    print(storm_date, f"{float(damage):>16,.0f}", f"{float(share):>5} % of all damage")

connection.close()

# years without a storm day have no row in the sql result,
# the model step puts them back with a count of 0

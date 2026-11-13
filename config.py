# settings, change things here only
from pathlib import Path

PERIL = "Tornado"      # has to match the spelling in the NOAA data
STATE = "TEXAS"        # NOAA writes states in capitals
FIRST_YEAR = 2000
LAST_YEAR = 2024

N_SIMULATED_YEARS = 100000
RANDOM_SEED = 42       # same seed, same numbers every run

# folders and files
BASE = Path(__file__).resolve().parent
RAW_DIR = BASE / "data" / "raw"
CLEAN_FILE = BASE / "data" / "storm_days.csv"
RESULTS_DIR = BASE / "results"
PARAMS_FILE = RESULTS_DIR / "model_parameters.json"

# postgres (step 3), password is not stored here:
# psycopg2 reads it from the PGPASSWORD environment variable
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "storm_loss"   # step 3 creates it if it is missing
DB_USER = "postgres"

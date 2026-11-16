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

# language model part (steps 7 to 10), runs on my own Mac through Ollama
LLM_MODEL = "llama3.2:3b"          # small open model, about 2 GB
EMBED_MODEL = "nomic-embed-text"   # turns a text into numbers, about 270 MB
OLLAMA_URL = "http://localhost:11434"
N_LLM_SAMPLE = 500                 # reports the language model reads
N_CLUSTERS = None                  # None = pick from the silhouette score
NARRATIVES_FILE = BASE / "data" / "narratives.csv"
N_FALSE_ALARMS_TO_READ = 15        # false alarms of prompt 1 that step 9 picks for reading by hand
PROMPT_VERSION = 2                 # 1 = first prompt, 2 = stricter prompt (step 8 and 9)


def results_file(name):
    # results of steps 8 and 9 get the prompt version in the name, e.g. llm_answers_v2.csv
    return RESULTS_DIR / f"{name}_v{PROMPT_VERSION}.csv"
EMBEDDINGS_FILE = RAW_DIR / "embeddings.npy"   # big, so not on GitHub

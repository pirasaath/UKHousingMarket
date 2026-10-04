import os
import duckdb
from dotenv import load_dotenv

# Lokaal: leest MOTHERDUCK_TOKEN uit .env
# Streamlit Cloud: secrets zijn automatisch als environment variables beschikbaar
load_dotenv()

MOTHERDUCK_DB = "uk_housing"


def get_connection():
    token = os.environ["MOTHERDUCK_TOKEN"]
    return duckdb.connect(f"md:{MOTHERDUCK_DB}?motherduck_token={token}")

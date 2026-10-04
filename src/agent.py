import os
import duckdb
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "uk_housing.duckdb"

SCHEMA_DESCRIPTION = """
Database Engine: DuckDB

Table 1: clean_price_paid
Columns:
- transaction_id (VARCHAR): Unique transaction ID
- price (BIGINT): Sale price in GBP (filtered £10k - £10M)
- date_transfer (DATE): Transaction date (YYYY-MM-DD)
- postcode (VARCHAR): Full UK postcode (e.g. 'SW1A 1AA')
- postcode_district (VARCHAR): Outward code / Postcode district (e.g. 'SW1A', 'E14', 'CR0')
- property_type (VARCHAR): Property classification ('D'=Detached, 'S'=Semi-Detached, 'T'=Terraced, 'F'=Flat/Maisonette, 'O'=Other)
- new_build (VARCHAR): 'Y' for newly built property, 'N' for established/resale
- duration (VARCHAR): 'F'=Freehold, 'L'=Leasehold
- paon, saon, street, locality, town, district, county (VARCHAR): Location details
- ppd_category (VARCHAR): 'A'=Standard residential transaction, 'B'=Additional price paid
- record_status (VARCHAR): 'A'=Addition, 'C'=Change, 'D'=Delete

Table 2: onspd_lookup (Geography mapping)
Columns:
- postcode (VARCHAR): Full postcode
- local_authority_code (VARCHAR): ONS Local Authority District code (e.g. 'E09000001')

Key Guidelines for SQL generation:
- Always generate valid DuckDB SQL syntax.
- Prefer MEDIAN(price) over AVG(price) for price statistics to avoid outlier skew, unless 'average' is explicitly requested.
- Always handle case insensitivity using UPPER() for text filters (e.g., UPPER(district) = 'EALING' or UPPER(postcode_district) = 'E14').
- For quarterly trends, use date_trunc('quarter', date_transfer).
"""

def ask_agent(question: str, db_path: str = str(DB_PATH)) -> str:
    con = duckdb.connect(str(db_path), read_only=True)

    sql_prompt = (
        f"You are a DuckDB SQL expert. Given this database schema:\n{SCHEMA_DESCRIPTION}\n\n"
        f"Generate ONLY a valid, executable DuckDB SQL query for this question. "
        f"Do not include explanations, markdown code blocks (like ```sql), or any other text.\n\n"
        f"Question: {question}"
    )
    
    try:
        sql_response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=sql_prompt
        )
        sql_query = sql_response.text.strip().replace("```sql", "").replace("```", "").strip()

        result = con.sql(sql_query).df()
    except Exception as e:
        con.close()
        return f"Could not execute query. Error: {e}\n\nGenerated SQL: {sql_query if 'sql_query' in locals() else 'None'}"

    interpretation_prompt = (
        f"Question: {question}\n"
        f"Executed SQL Query: {sql_query}\n"
        f"SQL Result:\n{result.to_string()}\n\n"
        f"Provide a concise, clear, and professional answer in English based on these results. "
        f"Format all monetary values in British Pounds (£)."
    )
    
    try:
        interpretation = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=interpretation_prompt
        )
        answer = interpretation.text
    except Exception as e:
        answer = f"Data retrieved successfully, but could not generate the explanation: {e}"

    con.close()
    return answer

if __name__ == "__main__":
    print(ask_agent("What is the median price in postcode district E14?"))
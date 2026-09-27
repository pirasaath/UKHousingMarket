import os
import duckdb
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

SCHEMA_DESCRIPTION = """
Table: clean_transactions
Columns:
- price (BIGINT): sale price in GBP
- date_transfer (DATE): transaction date
- postcode (VARCHAR)
- property_type (VARCHAR): D=Detached, S=Semi-Detached, T=Terraced, F=Flat, O=Other
- new_build (VARCHAR): 'Y' or 'N'
- duration (VARCHAR): 'F'=Freehold, 'L'=Leasehold
- town, district, county (VARCHAR)
"""

def ask_agent(question: str, db_path: str = "data/london_housing.duckdb") -> str:
    con = duckdb.connect(db_path)

    # Step 1: have the model generate SQL based on the question
    sql_prompt = (
        f"You are a SQL expert. Given this schema:\n{SCHEMA_DESCRIPTION}\n"
        f"Generate ONLY a valid DuckDB SQL query for this question, "
        f"no explanation, no markdown backticks.\n\nQuestion: {question}"
    )
    sql_response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=sql_prompt
    )
    sql_query = sql_response.text.strip().strip("```sql").strip("```").strip()

    # Step 2: actually run the query against your database
    try:
        result = con.sql(sql_query).df()
    except Exception as e:
        return f"Could not run the query: {e}\n\nGenerated SQL: {sql_query}"

    # Step 3: have the model interpret the results in plain language
    interpretation_prompt = (
        f"Question: {question}\nSQL result:\n{result.to_string()}\n\n"
        f"Give a short, clear answer in plain language."
    )
    interpretation = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=interpretation_prompt
    )

    con.close()
    return interpretation.text


if __name__ == "__main__":
    print(ask_agent("What is the average selling price in Ealing?"))
    print(ask_agent("Which district has the highest average price?"))
    print(ask_agent("How many new-build properties were sold in Croydon?"))
    

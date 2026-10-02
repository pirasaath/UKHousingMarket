import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "processed" / "uk_housing.duckdb"

COLUMNS = {
    "transaction_id": "VARCHAR",
    "price": "BIGINT",
    "date_transfer": "DATE",
    "postcode": "VARCHAR",
    "property_type": "VARCHAR",
    "new_build": "VARCHAR",
    "duration": "VARCHAR",
    "paon": "VARCHAR",
    "saon": "VARCHAR",
    "street": "VARCHAR",
    "locality": "VARCHAR",
    "town": "VARCHAR",
    "district": "VARCHAR",
    "county": "VARCHAR",
    "ppd_category": "VARCHAR",
    "record_status": "VARCHAR",
}


def build_price_paid_table():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    pattern = str(RAW_DIR / "pp-*.csv")

    con.sql(f"""
        CREATE OR REPLACE TABLE price_paid AS
        SELECT *,
               split_part(postcode, ' ', 1) AS postcode_district
        FROM read_csv(
            '{pattern}',
            header = false,
            columns = {COLUMNS}
        )
    """)

    # Clean view: drop symbolic/non-market transfers, extreme outliers,
    # and rows without a usable postcode district (needed for later joins
    # with flood risk / crime / EPC data)
    con.sql("""
        CREATE OR REPLACE VIEW clean_price_paid AS
        SELECT *
        FROM price_paid
        WHERE price BETWEEN 10000 AND 10000000
          AND postcode_district IS NOT NULL
    """)

    row_count = con.sql("SELECT COUNT(*) FROM price_paid").fetchone()[0]
    print(f"Loaded {row_count:,} transactions into {DB_PATH}")

    con.close()


if __name__ == "__main__":
    build_price_paid_table()
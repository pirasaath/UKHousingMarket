import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA
import warnings

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "london_housing.duckdb"


def forecast_district(district: str, db_path: str = str(DB_PATH)):
    con = duckdb.connect(db_path, read_only=True)

    df = con.sql(f"""
        SELECT
            date_trunc('quarter', date_transfer) AS quarter,
            AVG(price) AS avg_price
        FROM clean_transactions
        WHERE district = '{district}'
        GROUP BY quarter
        ORDER BY quarter
    """).df()
    con.close()

    if len(df) < 4:
        return None, None

    df["period"] = range(len(df))
    X = df[["period"]]
    y = df["avg_price"]

    model = LinearRegression()
    model.fit(X, y)

    future_periods = np.array(range(len(df), len(df) + 4)).reshape(-1, 1)
    predictions = model.predict(future_periods)

    return df, predictions


def forecast_district_arima(district: str, db_path: str = str(DB_PATH), periods: int = 4):
    con = duckdb.connect(db_path, read_only=True)

    df = con.sql(f"""
        SELECT
            date_trunc('quarter', date_transfer) AS quarter,
            AVG(price) AS avg_price
        FROM clean_transactions
        WHERE district = '{district}'
        GROUP BY quarter
        ORDER BY quarter
    """).df()
    con.close()

    if len(df) < 8:
        return None, None

    series = df.set_index("quarter")["avg_price"]
    series.index = pd.DatetimeIndex(series.index).to_period("Q")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ARIMA(series, order=(1, 1, 1))
        fitted = model.fit()

    forecast_result = fitted.forecast(steps=periods)

    return df, forecast_result.values


if __name__ == "__main__":
    print("--- Linear regression baseline ---")
    history, predictions = forecast_district("EALING")
    print(predictions)

    print("\n--- ARIMA ---")
    history_arima, predictions_arima = forecast_district_arima("EALING")
    print(predictions_arima)
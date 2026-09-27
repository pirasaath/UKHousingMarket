import duckdb
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA
import warnings


def forecast_district(district: str, db_path: str = "data/london_housing.duckdb"):
    con = duckdb.connect(db_path)

    # Get average price per quarter for this district
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

    # Turn quarters into a simple number (0, 1, 2, ...) so we can run linear regression
    df["period"] = range(len(df))
    X = df[["period"]]
    y = df["avg_price"]

    model = LinearRegression()
    model.fit(X, y)

    # Predict the next 4 quarters
    future_periods = np.array(range(len(df), len(df) + 4)).reshape(-1, 1)
    predictions = model.predict(future_periods)

    return df, predictions


def forecast_district_arima(district: str, db_path: str = "data/london_housing.duckdb", periods: int = 4):
    con = duckdb.connect(db_path)

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
        return None, None  # ARIMA needs a reasonable amount of history to fit properly

    series = df.set_index("quarter")["avg_price"]
    series.index = pd.DatetimeIndex(series.index).to_period("Q")

    # order=(p, d, q):
    # p = how many past values to look back on (autoregressive part)
    # d = how many times to difference the series to remove trend (1 = use quarter-over-quarter change)
    # q = how many past forecast errors to correct for (moving average part)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # statsmodels is chatty about convergence details, safe to ignore here
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
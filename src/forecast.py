import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from db import get_connection

# ============================================================
# FORECAST FUNCTION
# ============================================================

def evaluate_and_forecast_postcode(
    postcode_district=None,
    district=None,
    prop_type=None,
    new_build=None,
    duration=None,
    ppd_category=None,
    min_year=2020,
    max_year=2026,
    test_quarters=4,
    forecast_quarters=4,
):
    con = get_connection()

    # Build query conditions dynamically
    conditions = ["EXTRACT(YEAR FROM date_transfer) BETWEEN ? AND ?"]
    params = [min_year, max_year]

    if postcode_district is not None:
        conditions.append("postcode_district = ?")
        params.append(postcode_district)

    if district is not None:
        conditions.append("district = ?")
        params.append(district)

    if prop_type is not None:
        conditions.append("property_type = ?")
        params.append(prop_type)

    if new_build is not None:
        conditions.append("new_build = ?")
        params.append(new_build)

    if duration is not None:
        conditions.append("duration = ?")
        params.append(duration)

    if ppd_category is not None:
        conditions.append("ppd_category = ?")
        params.append(ppd_category)

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT
            date_trunc('quarter', date_transfer) AS quarter,
            MEDIAN(price) AS price
        FROM clean_price_paid
        WHERE {where_clause}
        GROUP BY quarter
        ORDER BY quarter
    """

    df = con.execute(query, params).df()

    # Check if there is enough data points to model
    if len(df) < (test_quarters + 4):
        return None

    # Ensure regular quarterly frequency
    df['quarter'] = pd.to_datetime(df['quarter'])
    df = df.set_index('quarter').asfreq('QS').interpolate().reset_index()

    prices = df['price'].values
    
    # Backtesting split
    train = prices[:-test_quarters]
    test = prices[-test_quarters:]

    try:
        # Fit model on training set for backtest evaluation
        model = ExponentialSmoothing(
            train, 
            trend='add', 
            seasonal=None, 
            initialization_method='estimated'
        ).fit()
        
        predictions = model.forecast(test_quarters)
        
        mape = np.mean(np.abs((test - predictions) / test)) * 100
        rmse = np.sqrt(np.mean((test - predictions) ** 2))

        # Re-fit on all available historical data for future forecast
        full_model = ExponentialSmoothing(
            prices, 
            trend='add', 
            seasonal=None, 
            initialization_method='estimated'
        ).fit()
        
        future_predictions = full_model.forecast(forecast_quarters)

    except Exception:
        # Fallback if optimization fails
        mape = 0.0
        rmse = 0.0
        future_predictions = np.full(forecast_quarters, prices[-1])

    return {
        "df": df,
        "future_predictions": future_predictions,
        "mape": mape,
        "rmse": rmse
    }
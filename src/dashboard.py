

import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
from agent import ask_agent
from forecast import forecast_district, forecast_district_arima

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "london_housing.duckdb"

st.set_page_config(page_title="London Housing Intelligence", layout="wide")
st.title("🏠 London Housing Market Intelligence")

con = duckdb.connect(str(DB_PATH), read_only=True)

districts = con.sql(
    "SELECT DISTINCT district FROM clean_transactions ORDER BY district"
).df()["district"].tolist()
selected_district = st.sidebar.selectbox("Choose a district", districts)
forecast_method = st.sidebar.radio("Forecast method", ["Linear Regression", "ARIMA"])

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Price trend — {selected_district}")
    trend = con.sql(f"""
        SELECT date_trunc('quarter', date_transfer) AS quarter, AVG(price) AS avg_price
        FROM clean_transactions
        WHERE district = '{selected_district}'
        GROUP BY quarter ORDER BY quarter
    """).df()
    st.line_chart(trend.set_index("quarter"))

with col2:
    st.subheader(f"Forecast — next 4 quarters ({forecast_method})")
    if forecast_method == "Linear Regression":
        history, predictions = forecast_district(selected_district)
    else:
        history, predictions = forecast_district_arima(selected_district)

    if predictions is not None:
        st.write(pd.DataFrame({"Predicted avg price": predictions}))
    else:
        st.write("Not enough data for this district.")

st.divider()

st.subheader("💬 Ask a question about the data")
question = st.text_input("e.g. 'What is the most expensive postcode in Croydon?'")
if question:
    with st.spinner("Analyzing..."):
        answer = ask_agent(question)
    st.write(answer)

con.close()
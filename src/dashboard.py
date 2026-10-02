import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
from agent import ask_agent
from forecast import forecast_district, forecast_district_arima

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "london_housing.duckdb"

NAVY, BLUE = "#0B1B33", "#1D4ED8"

st.set_page_config(page_title="London Housing Intelligence | PERRA", page_icon="📊", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap');
.stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, [data-testid="stMetric"] * {
    font-family: 'Instrument Sans', sans-serif;
}
.block-container { padding-top: 2rem; max-width: 1200px; }
.perra-header { display: flex; align-items: center; gap: .7rem; padding-bottom: 1rem;
    border-bottom: 1px solid rgba(11,27,51,.15); margin-bottom: 1.5rem; }
.perra-word { font-family: 'Instrument Sans', sans-serif; font-weight: 700; font-size: 1.5rem;
    letter-spacing: .04em; color: #0B1B33; }
.perra-sub { margin-left: auto; color: #64748B; font-family: 'Instrument Sans', sans-serif; font-size: .95rem; }
[data-testid="stMetric"] { background: #F1F5FB; border: 1px solid rgba(11,27,51,.10);
    border-radius: 10px; padding: 1rem 1.2rem; }
[data-testid="stMetricValue"] { color: #0B1B33; font-weight: 650; }
h2, h3 { color: #0B1B33; font-weight: 650; }
</style>
""",
    unsafe_allow_html=True,
)

LOGO = (
    '<svg width="34" height="34" viewBox="0 0 24 24" aria-hidden="true">'
    '<rect x="3" y="13" width="4" height="8" rx="1" fill="#1D4ED8" fill-opacity=".55"/>'
    '<rect x="10" y="8" width="4" height="13" rx="1" fill="#1D4ED8" fill-opacity=".8"/>'
    '<rect x="17" y="3" width="4" height="18" rx="1" fill="#1D4ED8"/></svg>'
)
st.markdown(
    f'<div class="perra-header">{LOGO}<span class="perra-word">PERRA</span>'
    '<span class="perra-sub">London Housing Market Intelligence</span></div>',
    unsafe_allow_html=True,
)

con = duckdb.connect(str(DB_PATH), read_only=True)

districts = con.sql(
    "SELECT DISTINCT district FROM clean_transactions ORDER BY district"
).df()["district"].tolist()
selected_district = st.sidebar.selectbox("Choose a district", districts)
forecast_method = st.sidebar.radio("Forecast method", ["Linear Regression", "ARIMA"])

stats = con.sql(f"""
    SELECT COUNT(*) AS n, AVG(price) AS avg_p, MEDIAN(price) AS med_p
    FROM clean_transactions
    WHERE district = '{selected_district}'
""").df().iloc[0]

trend = con.sql(f"""
    SELECT date_trunc('quarter', date_transfer) AS quarter, AVG(price) AS avg_price
    FROM clean_transactions
    WHERE district = '{selected_district}'
    GROUP BY quarter ORDER BY quarter
""").df()

change = None
if len(trend) >= 8:
    change = (trend["avg_price"].iloc[-4:].mean() / trend["avg_price"].iloc[-8:-4].mean() - 1) * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric("Transactions", f"{int(stats['n']):,}")
k2.metric("Average price", f"£{stats['avg_p']:,.0f}")
k3.metric("Median price", f"£{stats['med_p']:,.0f}")
k4.metric("Last 4 quarters vs previous 4", f"{change:+.1f}%" if change is not None else "n/a")

if forecast_method == "Linear Regression":
    history, predictions = forecast_district(selected_district)
else:
    history, predictions = forecast_district_arima(selected_district)

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"{selected_district.title()}: price trend and forecast")
    hist_s = trend.set_index("quarter")["avg_price"].rename("Historical")
    if predictions is not None:
        future_q = pd.date_range(hist_s.index[-1] + pd.DateOffset(months=3), periods=4, freq="QS")
        fc_s = pd.concat([hist_s.tail(1), pd.Series(predictions, index=future_q)]).rename("Forecast")
        chart_df = pd.concat([hist_s, fc_s], axis=1)
    else:
        chart_df = hist_s.to_frame()
    st.line_chart(chart_df, color=[NAVY, BLUE][: chart_df.shape[1]])

with col2:
    st.subheader(f"Next 4 quarters")
    st.caption(forecast_method)
    if predictions is not None:
        st.write(
            pd.DataFrame(
                {
                    "Quarter": [f"Q{d.quarter} {d.year}" for d in future_q],
                    "Avg price": [f"£{p:,.0f}" for p in predictions],
                }
            ).set_index("Quarter")
        )
    else:
        st.write("Not enough data for this district.")

st.caption(
    "Quarterly averages of genuine market sales (transfers under £10,000 excluded). "
    "The latest quarter may be incomplete. Forecasts are illustrative baselines, not financial advice."
)

st.divider()

st.subheader("💬 Ask a question about the data")
question = st.text_input("e.g. 'What is the most expensive postcode in Croydon?'")
if question:
    with st.spinner("Analyzing..."):
        answer = ask_agent(question)
    st.info(answer)

con.close()
import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path

from agent import ask_agent
from forecast import evaluate_and_forecast_postcode


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "uk_housing.duckdb"

NAVY = "#0B1B33"
BLUE = "#1D4ED8"


st.set_page_config(
    page_title="London Housing Intelligence | PERRA",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700'
        '&display=swap'
    );

    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp p,
    .stApp label,
    [data-testid="stMetric"] * {
        font-family: 'Instrument Sans', sans-serif;
    }

    .block-container {
        padding-top: 2rem;
        max-width: 1250px;
    }

    .perra-header {
        display: flex;
        align-items: center;
        gap: .7rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(11,27,51,.15);
        margin-bottom: 1.5rem;
    }

    .perra-word {
        font-family: 'Instrument Sans', sans-serif;
        font-weight: 700;
        font-size: 1.5rem;
        letter-spacing: .04em;
        color: #0B1B33;
    }

    .perra-sub {
        margin-left: auto;
        color: #64748B;
        font-family: 'Instrument Sans', sans-serif;
        font-size: .95rem;
    }

    [data-testid="stMetric"] {
        background: #F1F5FB;
        border: 1px solid rgba(11,27,51,.10);
        border-radius: 10px;
        padding: 1rem 1.2rem;
    }

    [data-testid="stMetricValue"] {
        color: #0B1B33;
        font-weight: 650;
    }

    h1, h2, h3 {
        color: #0B1B33;
        font-weight: 650;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

LOGO = (
    '<svg width="34" height="34" viewBox="0 0 24 24" aria-hidden="true">'
    '<rect x="3" y="13" width="4" height="8" rx="1" fill="#1D4ED8" fill-opacity=".55"/>'
    '<rect x="10" y="8" width="4" height="13" rx="1" fill="#1D4ED8" fill-opacity=".8"/>'
    '<rect x="17" y="3" width="4" height="18" rx="1" fill="#1D4ED8"/>'
    '</svg>'
)

st.markdown(
    f"""
    <div class="perra-header">
        {LOGO}
        <span class="perra-word">PERRA</span>
        <span class="perra-sub">
            London Housing Market Intelligence
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

@st.cache_resource
def get_connection():
    return duckdb.connect(
        str(DB_PATH),
        read_only=True
    )


con = get_connection()


# ============================================================
# LOAD FILTER OPTIONS
# ============================================================

@st.cache_data
def get_filter_options():

    districts = con.sql(
        """
        SELECT DISTINCT district
        FROM clean_price_paid
        WHERE district IS NOT NULL
        ORDER BY district
        """
    ).df()["district"].tolist()

    postcode_districts = con.sql(
        """
        SELECT DISTINCT postcode_district
        FROM clean_price_paid
        WHERE postcode_district IS NOT NULL
        ORDER BY postcode_district
        """
    ).df()["postcode_district"].tolist()

    property_types = con.sql(
        """
        SELECT DISTINCT property_type
        FROM clean_price_paid
        WHERE property_type IS NOT NULL
        ORDER BY property_type
        """
    ).df()["property_type"].tolist()

    new_build_values = con.sql(
        """
        SELECT DISTINCT new_build
        FROM clean_price_paid
        WHERE new_build IS NOT NULL
        ORDER BY new_build
        """
    ).df()["new_build"].tolist()

    duration_values = con.sql(
        """
        SELECT DISTINCT duration
        FROM clean_price_paid
        WHERE duration IS NOT NULL
        ORDER BY duration
        """
    ).df()["duration"].tolist()

    return (
        districts,
        postcode_districts,
        property_types,
        new_build_values,
        duration_values,
    )


@st.cache_data
def get_district_postcodes():
    return con.sql(
        """
        SELECT DISTINCT district, postcode_district
        FROM clean_price_paid
        WHERE district IS NOT NULL
          AND postcode_district IS NOT NULL
        ORDER BY district, postcode_district
        """
    ).df()


(
    districts,
    postcode_districts,
    property_types,
    new_build_values,
    duration_values,
) = get_filter_options()

district_postcodes = get_district_postcodes()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Market filters")


selected_district = st.sidebar.selectbox(
    "District",
    ["All districts"] + districts,
)


if selected_district == "All districts":
    available_postcodes = postcode_districts
else:
    available_postcodes = district_postcodes.loc[
        district_postcodes["district"] == selected_district,
        "postcode_district",
    ].tolist()


selected_postcode = st.sidebar.selectbox(
    "Postcode district",
    ["All"] + available_postcodes,
)


selected_property = st.sidebar.selectbox(
    "Property type",
    ["All"] + property_types,
)


selected_new_build = st.sidebar.selectbox(
    "New build",
    ["All"] + new_build_values,
)


selected_duration = st.sidebar.selectbox(
    "Tenure",
    ["All"] + duration_values,
)


selected_ppd = st.sidebar.selectbox(
    "PPD category",
    ["A", "B", "All"],
    index=0,
)


year_range = st.sidebar.slider(
    "Analysis period",
    min_value=2020,
    max_value=2026,
    value=(2020, 2026),
)


st.sidebar.divider()

st.sidebar.header("Forecast")


forecast_horizon = st.sidebar.slider(
    "Forecast horizon",
    min_value=1,
    max_value=8,
    value=4,
)


st.sidebar.caption(
    "Forecast model: Exponential Smoothing"
)


# ============================================================
# PREPARE FORECAST FILTERS
# ============================================================

forecast_postcode = (
    None
    if selected_postcode == "All"
    else selected_postcode
)

forecast_district = (
    None
    if selected_district == "All districts"
    else selected_district
)

forecast_property = (
    None
    if selected_property == "All"
    else selected_property
)

forecast_new_build = (
    None
    if selected_new_build == "All"
    else selected_new_build
)

forecast_duration = (
    None
    if selected_duration == "All"
    else selected_duration
)

forecast_category = (
    None
    if selected_ppd == "All"
    else selected_ppd
)


if selected_postcode != "All":
    location_label = selected_postcode
elif selected_district != "All districts":
    location_label = selected_district.title()
else:
    location_label = "England & Wales"


# ============================================================
# LOAD MARKET DATA
# ============================================================

@st.cache_data
def load_market_data(
    postcode_district,
    district,
    property_type,
    new_build,
    duration,
    ppd_category,
    min_year,
    max_year,
):

    conditions = [
        "EXTRACT(YEAR FROM date_transfer) BETWEEN ? AND ?"
    ]

    params = [
        min_year,
        max_year,
    ]

    if postcode_district is not None:
        conditions.insert(
            0,
            "postcode_district = ?"
        )
        params.insert(0, postcode_district)

    if district is not None:
        conditions.insert(
            0,
            "district = ?"
        )
        params.insert(0, district)

    if property_type is not None:
        conditions.append(
            "property_type = ?"
        )
        params.append(property_type)

    if new_build is not None:
        conditions.append(
            "new_build = ?"
        )
        params.append(new_build)

    if duration is not None:
        conditions.append(
            "duration = ?"
        )
        params.append(duration)

    if ppd_category is not None:
        conditions.append(
            "ppd_category = ?"
        )
        params.append(ppd_category)

    where_clause = " AND ".join(
        conditions
    )

    query = f"""
        SELECT
            date_trunc(
                'quarter',
                date_transfer
            ) AS quarter,

            MEDIAN(price) AS median_price,

            AVG(price) AS average_price,

            COUNT(*) AS transactions

        FROM clean_price_paid

        WHERE {where_clause}

        GROUP BY quarter

        ORDER BY quarter
    """

    return con.execute(
        query,
        params
    ).df()


market = load_market_data(
    forecast_postcode,
    forecast_district,
    forecast_property,
    forecast_new_build,
    forecast_duration,
    forecast_category,
    year_range[0],
    year_range[1],
)


# ============================================================
# EMPTY DATA CHECK
# ============================================================

if market.empty:

    st.warning(
        "No transactions were found for the selected filters."
    )

    st.stop()


# ============================================================
# MARKET KPIs
# ============================================================

total_transactions = market[
    "transactions"
].sum()

latest_median = market[
    "median_price"
].iloc[-1]

latest_average = market[
    "average_price"
].iloc[-1]


# Year-on-year growth (matched on the exact quarter one year
# earlier, so empty quarters cannot shift the comparison)

latest_quarter = market[
    "quarter"
].iloc[-1]

year_ago_quarter = (
    latest_quarter
    - pd.DateOffset(years=1)
)

year_ago_median = market.loc[
    market["quarter"] == year_ago_quarter,
    "median_price",
]

if not year_ago_median.empty:

    yoy_growth = (
        latest_median /
        year_ago_median.iloc[0]
        - 1
    ) * 100

else:

    yoy_growth = None


# ============================================================
# MARKET HEADER
# ============================================================

st.subheader(
    f"{location_label} — Housing Market"
)


# ============================================================
# KPI CARDS
# ============================================================

k1, k2, k3, k4 = st.columns(4)


k1.metric(
    "Transactions",
    f"{int(total_transactions):,}"
)


k2.metric(
    "Latest median price",
    f"£{latest_median:,.0f}"
)


k3.metric(
    "Latest average price",
    f"£{latest_average:,.0f}"
)


k4.metric(
    "YoY price growth",
    (
        f"{yoy_growth:+.1f}%"
        if yoy_growth is not None
        else "n/a"
    )
)


# ============================================================
# PRICE TREND
# ============================================================

st.divider()

st.subheader(
    "Quarterly price trend"
)


price_chart = (
    market
    .set_index("quarter")[
        [
            "median_price",
            "average_price",
        ]
    ]
    .rename(
        columns={
            "median_price": "Median price",
            "average_price": "Average price",
        }
    )
)


st.line_chart(
    price_chart,
    color=[
        NAVY,
        BLUE,
    ],
)


# ============================================================
# TRANSACTION VOLUME
# ============================================================

st.subheader(
    "Transaction volume"
)


volume_chart = (
    market
    .set_index("quarter")[
        ["transactions"]
    ]
    .rename(
        columns={
            "transactions":
            "Transactions"
        }
    )
)


st.bar_chart(
    volume_chart
)


# ============================================================
# PROPERTY TYPE BREAKDOWN
# ============================================================

st.divider()

st.subheader(
    "Property type breakdown"
)


segment_conditions = [
    "EXTRACT(YEAR FROM date_transfer) BETWEEN ? AND ?"
]

segment_params = [
    year_range[0],
    year_range[1],
]


if forecast_postcode is not None:

    segment_conditions.insert(
        0,
        "postcode_district = ?"
    )

    segment_params.insert(
        0,
        forecast_postcode
    )


if forecast_district is not None:

    segment_conditions.insert(
        0,
        "district = ?"
    )

    segment_params.insert(
        0,
        forecast_district
    )


if forecast_new_build is not None:

    segment_conditions.append(
        "new_build = ?"
    )

    segment_params.append(
        forecast_new_build
    )


if forecast_duration is not None:

    segment_conditions.append(
        "duration = ?"
    )

    segment_params.append(
        forecast_duration
    )


if forecast_category is not None:

    segment_conditions.append(
        "ppd_category = ?"
    )

    segment_params.append(
        forecast_category
    )


segment_where = " AND ".join(
    segment_conditions
)


segment_query = f"""
    SELECT
        property_type,
        COUNT(*) AS transactions,
        MEDIAN(price) AS median_price

    FROM clean_price_paid

    WHERE {segment_where}

    GROUP BY property_type

    ORDER BY median_price DESC
"""


segment = con.execute(
    segment_query,
    segment_params
).df()


if not segment.empty:

    c1, c2 = st.columns(2)

    with c1:

        st.caption(
            "Median price by property type"
        )

        st.bar_chart(
            segment.set_index(
                "property_type"
            )["median_price"]
        )

    with c2:

        st.caption(
            "Transactions by property type"
        )

        st.bar_chart(
            segment.set_index(
                "property_type"
            )["transactions"]
        )


# ============================================================
# FORECAST
# ============================================================

st.divider()

st.subheader(
    "Price forecast"
)

st.caption(
    "Exponential Smoothing forecast based on the selected "
    "district, postcode and market filters."
)


forecast_result = (
    evaluate_and_forecast_postcode(
        postcode_district=forecast_postcode,
        district=forecast_district,
        prop_type=forecast_property,
        new_build=forecast_new_build,
        duration=forecast_duration,
        ppd_category=forecast_category,
        min_year=year_range[0],
        max_year=year_range[1],
        test_quarters=4,
        forecast_quarters=forecast_horizon,
    )
)


# ============================================================
# FORECAST RESULT
# ============================================================

if forecast_result is None:

    st.warning(
        "There is not enough data to generate a forecast "
        "for this selection."
    )

else:


    forecast_data = forecast_result["df"]

    future_predictions = (
        forecast_result[
            "future_predictions"
        ]
    )

    mape = forecast_result["mape"]

    rmse = forecast_result["rmse"]


    # ----------------------------------------
    # Historical series
    # ----------------------------------------

    historical = (
        forecast_data
        .set_index("quarter")["price"]
        .rename("Historical")
    )


    # ----------------------------------------
    # Future dates
    # ----------------------------------------

    future_dates = pd.date_range(
        start=historical.index[-1]
        + pd.DateOffset(months=3),

        periods=len(
            future_predictions
        ),

        freq="QS",
    )


    # ----------------------------------------
    # Forecast series
    # ----------------------------------------

    forecast_series = pd.Series(
        future_predictions,
        index=future_dates,
        name="Forecast",
    )


    # ----------------------------------------
    # Combined chart
    # ----------------------------------------

    chart_df = pd.concat(
        [
            historical,
            forecast_series,
        ],
        axis=1,
    )


    st.line_chart(
        chart_df,
        color=[
            NAVY,
            BLUE,
        ],
    )


    # ========================================================
    # MODEL PERFORMANCE
    # ========================================================

    st.subheader(
        "Forecast model performance"
    )


    m1, m2 = st.columns(2)


    with m1:

        st.metric(
            "Backtest MAPE",
            f"{mape:.1f}%"
        )


    with m2:

        st.metric(
            "Backtest RMSE",
            f"£{rmse:,.0f}"
        )


    st.caption(
        "Performance is calculated using a historical "
        "backtesting window of four quarters."
    )


    # ========================================================
    # FORECAST TABLE
    # ========================================================

    st.subheader(
        "Next quarters"
    )


    forecast_table = pd.DataFrame(
        {
            "Quarter": future_dates,
            "Forecast price":
                future_predictions,
        }
    )


    forecast_table[
        "Quarter"
    ] = (
        forecast_table[
            "Quarter"
        ]
        .dt.to_period("Q")
        .astype(str)
    )


    forecast_table[
        "Forecast price"
    ] = (
        forecast_table[
            "Forecast price"
        ]
        .map(
            lambda x:
            f"£{x:,.0f}"
        )
    )


    st.dataframe(
        forecast_table,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# AI ANALYST
# ============================================================

st.divider()

st.subheader(
    "💬 Ask the PERRA Housing Analyst"
)


question = st.text_input(
    "Ask a question about the data",
    placeholder=(
        "What is the most expensive postcode in Croydon?"
    ),
)


if question:

    with st.spinner(
        "Analyzing housing data..."
    ):

        try:

            answer = ask_agent(
                question
            )

            st.info(answer)

        except Exception as e:

            st.error(
                f"The AI analyst could not answer "
                f"the question: {e}"
            )

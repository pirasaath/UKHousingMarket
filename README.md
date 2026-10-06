**UK Housing Market Intelligence**

An end-to-end data & AI project by PERRA: an interactive dashboard on UK house prices with quarterly price forecasts and a NL AI that answers questions by generating and running SQL on the data.

Live demo: https://ukhousingmarket-perra.streamlit.app/.
Also see our website: https://perra.io 

We are specialised in DATA & AI Consultancy.

**Features**
Market dashboard — filter by district, postcode district, property type, new build, tenure, PPD category and period. KPIs for transactions, latest median/average price and year-on-year growth.
Trends and breakdowns — quarterly median/average price, transaction volume and a property type breakdown.
Price forecast — Exponential Smoothing (additive trend) forecast of the median price, with a 4-quarter backtest reporting MAPE and RMSE.
AI CHATBOT — ask a question in plain English; a Gemini model translates it to DuckDB SQL, the query runs against the data, and the result is summarised in plain language.

**Data**
HM Land Registry Price Paid Data — residential property sales in England & Wales. Prices are filtered to £10k–£10M.
ONS Postcode Directory (ONSPD) — maps postcodes to local authorities.

The processed database is hosted in MotherDuck as uk_housing and is not stored in this repository because of its size.

**Stack**
- DuckDB — data storage & querying
- Google Gemini API — natural language agent
- scikit-learn / statsmodels — forecasting
- Motherduck
- Python
- Streamlit — dashboard

**About**

Built by PERRA — DATA & AI CONSULTANCY - BY PERA RAJAHKUMAR.

**Data source**
Contains HM Land Registry data © Crown copyright and database right 2026. 
Licensed under the Open Government Licence v3.0.

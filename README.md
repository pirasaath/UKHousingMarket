# UK Housing Market Intelligence

Analysis of HM Land Registry Price Paid Data (Greater London, last 5 years) 
with a DuckDB processing layer, an AI agent that answers natural-language 
questions, two forecasting models (Linear Regression & ARIMA), and an 
interactive Streamlit dashboard.

**Note this is only random 100000 observations. Not complete 5 years. **

## Setup
1. `pip install -r requirements.txt`
2. Place your data file in `data/` (HM Land Registry Price Paid Data, London filter)
3. Add a `.env` file with `GOOGLE_API_KEY=your-key-here`
4. Run `notebooks/01_explore.ipynb` to build the database
5. `cd src && streamlit run dashboard.py`

## Stack
- DuckDB — data storage & querying
- Google Gemini API — natural language agent
- scikit-learn / statsmodels — forecasting (Linear Regression, ARIMA)
- Streamlit — dashboard

## Data source
Contains HM Land Registry data © Crown copyright and database right 2026. 
Licensed under the Open Government Licence v3.0.

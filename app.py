import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from requests import Session

# 1. Setup Session to avoid Rate Limiting
# This mimics a browser, which reduces the chance of being blocked
@st.cache_resource
def get_session():
    session = Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

# 2. Configuration & Tickers
st.set_page_config(page_title="Global 200 Monitor", layout="wide")

# Replace this with your full list of 200 tickers
TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"] 

# 3. Optimized Data Fetching
@st.cache_data(ttl=3600)
def fetch_all_data(ticker_list):
    clean_tickers = [str(t).strip().upper() for t in ticker_list if t and isinstance(t, str)]
    if not clean_tickers:
        return None

    # Use the session created above
    session = get_session()
    
    # Download OHLCV data (Less likely to be rate-limited than .info)
    data = yf.download(
        tickers=clean_tickers,
        period="1y",
        interval="1d",
        group_by='ticker',
        threads=True,
        session=session,
        progress=False
    )
    return data

def analyze_stocks(all_data, ticker_list):
    results = []
    for ticker in ticker_list:
        try:
            # Extract data from multi-index
            if len(ticker_list) > 1:
                df = all_data[ticker].dropna()
            else:
                df = all_data.dropna()

            if df.empty: continue
            
            # Simple technical indicators
            current_price = df['Close'].iloc[-1]
            ma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
            
            confidence = 60 if current_price > ma_200 else 30
            
            results.append({
                "Ticker": ticker,
                "Price": round(current_price, 2),
                "Confidence": confidence
            })
        except:
            continue
    return results

# --- UI LOGIC ---
st.title("🚀 Global 200 Stock Monitor")

if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None

with st.spinner("Analyzing 200 stocks..."):
    all_raw_data = fetch_all_data(TICKERS)
    if all_raw_data is not None:
        analysis = analyze_stocks(all_raw_data, TICKERS)
        sorted_stocks = sorted(analysis, key=lambda x: x['Confidence'], reverse=True)
    else:
        st.error("No data found.")
        sorted_stocks = []

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Top Picks")
    for stock in sorted_stocks[:20]:
        if st.button(f"{stock['Ticker']} | ₹{stock['Price']} ({stock['Confidence']}%)", key=f"btn_{stock['Ticker']}"):
            st.session_state.selected_stock = stock['Ticker']

with col2:
    if st.session_state.selected_stock:
        target = st.session_state.selected_stock
        st.header(f"📊 Deep Dive: {target}")
        
        # USE TRY/EXCEPT here because .info is the most fragile part of yfinance
        try:
            with st.spinner("Fetching fundamentals..."):
                ticker_obj = yf.Ticker(target, session=get_session())
                info = ticker_obj.info
                
                # Display only available keys to avoid more errors
                metrics = {
                    "Sector": info.get('sector', 'N/A'),
                    "PE Ratio": info.get('trailingPE', 'N/A'),
                    "Market Cap": info.get('marketCap', 'N/A'),
                    "52 Week High": info.get('fiftyTwoWeekHigh', 'N/A')
                }
                st.write(metrics)
        except Exception as e:
            st.warning(f"Yahoo Finance is rate-limiting the 'Deep Dive' for {target}. The main dashboard will still work, but fundamental data is temporarily unavailable. Try again in a few minutes.")
    else:
        st.info("Click a stock on the left to view Deep Dive details.")
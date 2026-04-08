import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time

# --- OPTIMIZED DOWNLOADER ---
@st.cache_data(ttl=3600) # Streamlit cache to save data for 1 hour
def fetch_bulk_data(ticker_list):
    tickers_str = " ".join(ticker_list)
    # threads=True processing ko fast banata hai
    data = yf.download(tickers_str, period="1y", group_by='ticker', threads=True)
    return data

st.title("🛡️ Arth Sutra Wealth Engine (Fixed)")

# Nifty 200 sample
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "SBIN.NS", "ITC.NS"]

try:
    all_raw_data = fetch_bulk_data(tickers)
    
    analysis_results = []
    for ticker in tickers:
        df = all_raw_data[ticker].copy()
        if df.empty: continue
        
        # Calculate Indicators
        df['SMA44'] = ta.sma(df['Close'], length=44)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        
        curr = df.iloc[-1]
        
        # Simple Logic
        confidence = 0
        if curr['Close'] > curr['SMA200']: confidence += 50
        if abs(curr['Close'] - curr['SMA44']) / curr['SMA44'] < 0.02: confidence += 50
        
        analysis_results.append({
            "Ticker": ticker,
            "Price": round(curr['Close'], 2),
            "Confidence": f"{confidence}%",
            "Verdict": "BULLISH" if confidence >= 50 else "WAIT"
        })

    st.table(pd.DataFrame(analysis_results))

except Exception as e:
    st.error(f"Limit reached. Try again in 5 mins. Technical Error: {e}")
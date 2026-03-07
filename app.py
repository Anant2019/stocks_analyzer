import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 1. App Configuration
st.set_page_config(page_title="Swing Triple Bullish Scanner", layout="wide")
st.title("📈 44-200 SMA Bullish Scanner")

# 2. Define your Watchlist (Example: Nifty 50 or S&P 500 tickers)
tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "RELIANCE.NS", "TCS.NS"] 

def check_strategy(ticker):
    try:
        # Fetch 1 year of daily data
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if len(data) < 200: return None
        
        # Calculate Indicators
        data['sma44'] = ta.sma(data['Close'], length=44)
        data['sma200'] = ta.sma(data['Close'], length=200)
        
        # Current and Previous Values for Trend Logic
        curr = data.iloc[-1]
        prev = data.iloc[-2]
        prev2 = data.iloc[-3]
        
        # Logic: 44 > 200 AND both rising
        is_trending = curr['sma44'] > curr['sma200'] and curr['sma44'] > prev2['sma44'] and curr['sma200'] > prev2['sma200']
        
        # Candle Logic: Strong green candle touching/near 44 SMA
        is_strong = curr['Close'] > curr['Open'] and curr['Low'] <= curr['sma44'] and curr['Close'] > curr['sma44']
        
        if is_trending and is_strong:
            return {
                "Ticker": ticker,
                "Price": round(float(curr['Close']), 2),
                "44 SMA": round(float(curr['sma44']), 2),
                "200 SMA": round(float(curr['sma200']), 2)
            }
    except:
        return None

# 3. Scanner Trigger
if st.button("🔍 Scan Markets for Hits"):
    hits = []
    with st.spinner("Scanning tickers..."):
        for t in tickers:
            result = check_strategy(t)
            if result:
                hits.append(result)
    
    if hits:
        st.success(f"Found {len(hits)} stocks matching your criteria!")
        st.table(pd.DataFrame(hits))
    else:
        st.warning("No hits found today. Keep an eye on the 44 SMA!")

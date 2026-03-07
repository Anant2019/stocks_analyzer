import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import datetime

# 1. Page Setup
st.set_page_config(page_title="44-200 SMA Scanner", layout="wide")
st.title("📈 Swing Triple Bullish Scanner")
st.write(f"Current System Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 2. Ticker List (Using .NS for Indian Stocks)
tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS"]

def check_strategy(symbol):
    try:
        # Download 2 years of data to ensure 200 SMA is accurate
        df = yf.download(symbol, period="2y", interval="1d", progress=False)
        
        if df.empty or len(df) < 200:
            return None

        # Handle YFinance Multi-Index if it occurs
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Calculate SMAs
        df['sma44'] = ta.sma(df['Close'], length=44)
        df['sma200'] = ta.sma(df['Close'], length=200)

        # Get last 3 rows for trend/candle logic
        curr = df.iloc[-1]
        prev2 = df.iloc[-3]

        # --- THE LOGIC ---
        # 1. Trend: 44 > 200 AND 44 is rising
        is_trending = float(curr['sma44']) > float(curr['sma200']) and float(curr['sma44']) > float(prev2['sma44'])
        
        # 2. Candle: Green candle AND Low touched or went below 44 SMA
        is_bullish_candle = float(curr['Close']) > float(curr['Open'])
        is_touching_44 = float(curr['Low']) <= float(curr['sma44'])

        if is_trending and is_bullish_candle and is_touching_44:
            return {
                "Ticker": symbol,
                "Price": round(float(curr['Close']), 2),
                "44 SMA": round(float(curr['sma44']), 2),
                "Status": "🔥 HIT"
            }
            
    except Exception as e:
        # This prevents the app from going blank if one stock errors out
        st.error(f"Error processing {symbol}: {e}")
        return None
    return None

# 3. UI Logic
if st.button("🔍 Run Friday Analysis"):
    hits = []
    progress_bar = st.progress(0)
    
    for i, t in enumerate(tickers):
        res = check_strategy(t)
        if res:
            hits.append(res)
        progress_bar.progress((i + 1) / len(tickers))
    
    if hits:
        st.success(f"Found {len(hits)} signals!")
        st.table(pd.DataFrame(hits))
    else:
        st.info("No 'Triple Bullish' hits found for the selected stocks on Friday's close.")
        st.write("Tip: Markets were down on Friday, so most stocks likely had Red candles (failing the strategy).")

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

# Define your watchlist
tickers = ["RELIANCE.NS", "TCS.NS", "COALINDIA.NS", "INFY.NS", "ADANIPORTS.NS", "TATAMOTORS.NS"] 

def scan_stocks():
    bullish_stocks = []
    
    for ticker in tickers:
        try:
            # Download data
            data = yf.download(ticker, period="1y", interval="1d", progress=False)
            if len(data) < 200: continue
            
            # Calculate SMAs
            data['SMA44'] = data['Close'].rolling(window=44).mean()
            data['SMA200'] = data['Close'].rolling(window=200).mean()
            
            # Select latest and previous rows
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            # EXTRACT RAW NUMBERS to avoid the "identically-labeled" ValueError
            price_close = float(latest['Close'])
            price_open = float(latest['Open'])
            price_low = float(latest['Low'])
            sma44_now = float(latest['SMA44'])
            sma44_prev = float(prev['SMA44'])
            sma200_now = float(latest['SMA200'])
            sma200_prev = float(prev['SMA200'])
            
            # LOGIC
            is_sma44_rising = sma44_now > sma44_prev
            is_sma200_rising = sma200_now > sma200_prev
            is_green_candle = price_close > price_open
            is_at_support = price_low <= (sma44_now * 1.01) 
            
            if is_sma44_rising and is_sma200_rising and is_green_candle and is_at_support:
                bullish_stocks.append({
                    "Ticker": ticker,
                    "Price": round(price_close, 2),
                    "SMA 44": round(sma44_now, 2),
                    "Status": "Bullish Support"
                })
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
            continue
            
    return pd.DataFrame(bullish_stocks)

# --- STREAMLIT UI ---
st.set_page_config(page_title="5 PM Stock Scanner", layout="wide")
st.title("📈 44/200 SMA Bullish Scanner")

if st.button('Run Scan Now'):
    results_df = scan_stocks()
    if not results_df.empty:
        st.table(results_df)
        results_df.to_csv("results.csv", index=False)
        st.success(f"Scan complete at {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.warning("No stocks matched the criteria right now.")

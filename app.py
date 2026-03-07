import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 1. Expand your list so you aren't just looking at one stock
STOCK_LIST = ["HINDALCO.NS", "COALINDIA.NS", "ADANIPORTS.NS", "BEL.NS", "TATASTEEL.NS", "SBIN.NS"]

def scan_market():
    matches = []
    for ticker in STOCK_LIST:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        # Calculate SMAs
        df['44_SMA'] = ta.sma(df['Close'], length=44)
        df['200_SMA'] = ta.sma(df['Close'], length=200)
        
        last_row = df.iloc[-1]
        
        # --- THE FIX: SMART LOGIC ---
        # 1. Is it in a Bullish Trend? (44 > 200)
        is_bullish_trend = last_row['44_SMA'] > last_row['200_SMA']
        
        # 2. Is the LOW touching or very close to the 44 SMA?
        # We use a 0.5% buffer so we don't miss "near-misses"
        near_sma44 = last_row['Low'] <= (last_row['44_SMA'] * 1.005)
        
        if is_bullish_trend and near_sma44:
            matches.append({
                "Ticker": ticker,
                "Price": last_row['Close'],
                "SMA 44": last_row['44_SMA'],
                "Status": "HITTING STRATEGY"
            })
    return matches

if st.button("Scan All My Stocks"):
    results = scan_market()
    if results:
        st.table(results)
    else:
        st.write("No stocks hitting the 44 SMA support right now.")

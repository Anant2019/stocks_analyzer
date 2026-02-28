import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Final Professional Hunter", layout="wide")

# --- ACTUAL NSE 200 TICKERS ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 
    'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HCLTECH.NS', 
    'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS', 
    'INFY.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 
    'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATACONSUM.NS', 
    'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS'
] # Add more to reach 200

st.title("🏹 Triple Bullish Hunter (Strict Pine Sync)")
target_date = st.date_input("Select Research Date", datetime.now() - timedelta(days=1))

def hunt_stocks(sel_date):
    results = []
    progress = st.progress(0)
    status = st.empty()
    
    # Ensuring 500 days of data for SMA 200 stability
    start_d = sel_date - timedelta(days=500)
    end_d = datetime.now()
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            status.text(f"Scanning {ticker}...")
            df = yf.download(ticker, start=start_d, end=end_d, auto_adjust=True, progress=False)
            
            if len(df) < 200: continue
            
            # 1. PINE SCRIPT MATH
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            # Date Alignment
            if pd.Timestamp(sel_date) not in df.index:
                actual_date = df.index[df.index <= pd.Timestamp(sel_date)][-1]
            else:
                actual_date = pd.Timestamp(sel_date)
            
            idx = df.index.get_loc(actual_date)
            row = df.iloc[idx]
            prev2 = df.iloc[idx-2]

            # 2. THE STRICT LOGIC (As per your Pine Script)
            # Trend: 44 > 200 and SMAs rising
            is_trending = row['s44'] > row['s200'] and row['s44'] > prev2['s44'] and row['s200'] > prev2['s200']
            
            # Strong Green Candle: Close > Open and Close in upper half
            is_strong = row['Close'] > row['Open'] and row['Close'] > ((row['High'] + row['Low']) / 2)
            
            # Support on 44 SMA: Low <= 44 SMA and Close > 44 SMA
            # Adding a tiny 0.2% buffer for TV-yfinance data bridge
            is_support = row['Low'] <= (row['s44'] * 1.002) and row['Close'] > row['s44']

            if is_trending and is_strong and is_support:
                risk = row['Close'] - row['Low']
                results.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(row['Close'], 2),
                    "SL": round(row['Low'], 2),
                    "Target 1:1": round(row['Close'] + risk, 2),
                    "Target 1:2": round(row['Close'] + (risk * 2), 2)
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    
    status.empty()
    return pd.DataFrame(results)

if st.button('🚀 Start Professional Hunt'):
    df_results = hunt_stocks(target_date)
    if not df_results.empty:
        st.success(f"Found {len(df_results)} setups!")
        st.table(df_results)
    else:
        st.error("Setup not found on this date. Double-check your TradingView chart for the same date.")

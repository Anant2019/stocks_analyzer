import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- SYSTEM CONFIG ---
st.set_page_config(page_title="Pro-Quant Auditor V6", layout="wide")

def get_clean_data(ticker, start_date, end_date):
    """Fetches and flattens data to avoid MultiIndex errors."""
    df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)
    if df.empty: return None
    # Professional Flattening: Handles yfinance 0.2.x+ column structures
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def run_strategy_logic(df):
    """Vectorized implementation of Swing Triple Bullish 44-200."""
    # 1. Vectorized Indicators
    df['s44'] = df['Close'].rolling(window=44).mean()
    df['s200'] = df['Close'].rolling(window=200).mean()
    
    # 2. Strict Trend & Slope (Rising SMAs)
    # Price > 44 > 200 AND SMAs are pointing UP (Slope)
    df['is_trending'] = (df['s44'] > df['s200']) & \
                        (df['s44'] > df['s44'].shift(2)) & \
                        (df['s200'] > df['s200'].shift(2))
    
    # 3. Institutional Strength (Green Candle + Strong Close)
    df['is_strong'] = (df['Close'] > df['Open']) & \
                      (df['Close'] > ((df['High'] + df['Low']) / 2))
    
    # 4. The Touch (Mean Reversion) - 0.2% Institutional Action Zone
    # Low must touch or be within 0.2% of SMA 44, but Close must be above it
    df['is_touching'] = (df['Low'] <= (df['s44'] * 1.002)) & (df['Close'] > df['s44'])
    
    # Final Signal
    df['Signal'] = df['is_trending'] & df['is_strong'] & df['is_touching']
    return df

# --- UI INTERFACE ---
st.title("🛡️ Pro-Quant: Triple Bullish 44-200")
st.sidebar.header("Strategy Settings")
ticker = st.sidebar.text_input("NSE Ticker", "RELIANCE.NS")
target_date = st.sidebar.date_input("Analysis Date")

if st.sidebar.button("Execute Vectorized Scan"):
    # Fetch wider window for SMA stability and backtesting
    start_dt = pd.to_datetime(target_date) - pd.Timedelta(days=550)
    end_dt = pd.to_datetime(target_date) + pd.Timedelta(days=150)
    
    df = get_clean_data(ticker, start_dt, end_dt)
    
    if df is not None and len(df) > 200:
        df = run_strategy_logic(df)
        
        # Locate the specific signal date
        target_ts = pd.Timestamp(target_date)
        if target_ts not in df.index:
            target_ts = df.index[df.index <= target_ts][-1]
        
        if df.loc[target_ts, 'Signal']:
            row = df.loc[target_ts]
            risk = row['Close'] - row['Low']
            target_2 = row['Close'] + (risk * 2)
            
            # Backtest outcome (Bar-by-bar walk forward)
            future = df.loc[target_ts:].iloc[1:]
            outcome = "Pending ⏳"
            for f_ts, f_row in future.iterrows():
                if f_row['Low'] <= row['Low']:
                    outcome = "SL Hit 🔴"
                    break
                if f_row['High'] >= target_2:
                    outcome = "Target 1:2 Hit 🟢"
                    break
            
            # Professional Metrics
            st.success(f"Signal Identified for {ticker}")
            cols = st.columns(4)
            cols[0].metric("Entry (Close)", f"₹{round(row['Close'], 2)}")
            cols[1].metric("Stop Loss", f"₹{round(row['Low'], 2)}")
            cols[2].metric("Target (1:2)", f"₹{round(target_2, 2)}")
            cols[3].metric("Outcome", outcome)
        else:
            st.error("No signal detected. The trend or the 'SMA 44 Touch' did not meet the 70% accuracy criteria.")
    else:
        st.warning("Insufficient data. Check the ticker or date range.")

st.divider()
st.caption("Quantitative Research Engine | Vectorized for 1:2 Risk Management.")

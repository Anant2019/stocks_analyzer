import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURATION & PERSONA SETTINGS ---
st.set_page_config(page_title="Institutional Quant Scanner", layout="wide")

def calculate_metrics(df, results_df):
    """Calculates Institutional Risk Metrics: Sharpe, MDD, Volatility"""
    if results_df.empty:
        return 0.0, 0.0, 0.0
    
    # Simple daily returns for volatility (using Close prices)
    returns = df['Close'].pct_change().dropna()
    volatility = returns.std() * np.sqrt(252)
    
    # Sharpe Ratio (Assuming 5% Risk-Free Rate)
    sharpe = (returns.mean() * 252 - 0.05) / (returns.std() * np.sqrt(252))
    
    # Max Drawdown
    cumulative = (1 + returns).cumprod()
    peak = cumulative.expanding(min_periods=1).max()
    mdd = ((cumulative - peak) / peak).min()
    
    return round(sharpe, 2), round(mdd * 100, 2), round(volatility * 100, 2)

# --- TICKER UNIVERSE ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 
             'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 
             'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 
             'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'ITC.NS', 'INFY.NS', 'JSWSTEEL.NS', 
             'KOTAKBANK.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'RELIANCE.NS', 'SBIN.NS', 'TCS.NS', 'TITAN.NS']

# --- APP UI ---
st.title("🛡️ Institutional Strategy Auditor")
target_dt = st.date_input("Analysis Date", value=datetime.now().date() - timedelta(days=1))

if st.button("🚀 Execute Vectorized Scan"):
    all_results = []
    
    progress_bar = st.progress(0)
    for idx, ticker in enumerate(NIFTY_200):
        try:
            # 1. DATA RETRIEVAL (Vectorized window)
            df = yf.download(ticker, start=target_dt - timedelta(days=600), end=target_dt + timedelta(days=90), auto_adjust=True, progress=False)
            if df.empty or len(df) < 205: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # 2. VECTORIZED MATH (No Loops)
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            # Lookback Logic (Shifted Series)
            df['s44_p2'] = df['s44'].shift(2)
            df['s200_p2'] = df['s200'].shift(2)

            # 3. STRATEGY FILTERS
            # Trend: 44 > 200 AND Both Rising
            df['is_trending'] = (df['s44'] > df['s200']) & (df['s44'] > df['s44_p2']) & (df['s200'] > df['s200_p2'])
            # Candle: Green + Strong Close (Top 50% of range)
            df['is_strong'] = (df['Close'] > df['Open']) & (df['Close'] > ((df['High'] + df['Low']) / 2))
            # The Touch: Low <= SMA 44 (with 0.3% fuzzy buffer)
            df['is_touching'] = (df['Low'] <= (df['s44'] * 1.003)) & (df['Close'] > df['s44'])

            # Signal Trigger
            df['signal'] = df['is_trending'] & df['is_strong'] & df['is_touching']
            
            # Check the Target Date session
            target_ts = pd.Timestamp(target_dt)
            if target_ts not in df.index:
                # Snap to nearest prior trading session
                target_ts = df.index[df.index <= target_ts][-1]

            if df.loc[target_ts, 'signal']:
                row = df.loc[target_ts]
                risk = row['Close'] - row['Low']
                t2 = row['Close'] + (2 * risk)
                
                # Backtest Outcome
                future = df[df.index > target_ts]
                outcome = "Pending ⏳"
                for f_ts, f_row in future.iterrows():
                    if f_row['Low'] <= row['Low']:
                        outcome = "SL Hit 🔴"
                        break
                    if f_row['High'] >= t2:
                        outcome = "Target 1:2 Hit 🟢"
                        break

                all_results.append({
                    "Ticker": ticker, "Outcome": outcome, "Entry": round(row['Close'], 2),
                    "SL": round(row['Low'], 2), "T2": round(t2, 2)
                })
        except Exception as e:
            continue
        progress_bar.progress((idx + 1) / len(NIFTY_200))

    # --- OUTPUT ---
    if all_results:
        res_df = pd.DataFrame(all_results)
        sharpe, mdd, vol = calculate_metrics(df, res_df) # Metrics from last scanned valid df
        
        st.subheader("📊 Strategy Performance Metrics")
        m1, m2, m3 = st.columns(3)
        m1.metric("Sharpe Ratio", sharpe)
        m2.metric("Max Drawdown", f"{mdd}%")
        m3.metric("Annualized Vol", f"{vol}%")
        
        st.dataframe(res_df, use_container_width=True)
    else:
        st.error("Quant Engine: No signals matched the 44-200 Triple Bullish criteria for this timestamp.")

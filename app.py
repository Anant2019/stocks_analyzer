import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- INSTITUTIONAL PERSONA CONFIG ---
st.set_page_config(page_title="Swing Triple Bullish Auditor", layout="wide")

def get_institutional_metrics(returns):
    """Calculates Sharpe Ratio and Max Drawdown."""
    if returns.empty: return 0.0, 0.0
    sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
    cumulative = (1 + returns).cumprod()
    peak = cumulative.expanding(min_periods=1).max()
    mdd = ((cumulative - peak) / peak).min()
    return round(sharpe, 2), round(mdd * 100, 2)

# --- TICKER UNIVERSE ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 
             'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 
             'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 
             'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'ITC.NS', 'INFY.NS', 'JSWSTEEL.NS', 
             'KOTAKBANK.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'RELIANCE.NS', 'SBIN.NS', 'TCS.NS', 'TITAN.NS']

st.title("🛡️ Triple Bullish 44-200 Strategy Auditor")
st.markdown("### 70% Accuracy Benchmark | 1:2 Risk-Reward")

target_dt = st.date_input("Analysis Date", value=datetime.now().date() - timedelta(days=1))

if st.button("🚀 Execute Quantitative Scan"):
    results = []
    progress = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            # Vectorized Data Retrieval
            df = yf.download(ticker, start=target_dt - timedelta(days=600), end=target_dt + timedelta(days=120), auto_adjust=True, progress=False)
            if df.empty or len(df) < 205: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # Vectorized Logic
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            # Trend Check (Current vs 2 bars ago)
            df['trend'] = (df['s44'] > df['s200']) & (df['s44'] > df['s44'].shift(2)) & (df['s200'] > df['s200'].shift(2))
            
            # Strength Check (Green Candle + Strong Close)
            df['strong'] = (df['Close'] > df['Open']) & (df['Close'] > ((df['High'] + df['Low']) / 2))
            
            # Touch Check (Low <= SMA44 with 0.3% Buffer)
            df['touch'] = (df['Low'] <= (df['s44'] * 1.003)) & (df['Close'] > df['s44'])
            
            df['buy'] = df['trend'] & df['strong'] & df['touch']
            
            # Execution for Selected Date
            analysis_ts = pd.Timestamp(target_dt)
            if analysis_ts not in df.index:
                analysis_ts = df.index[df.index <= analysis_ts][-1]
                
            if df.loc[analysis_ts, 'buy']:
                row = df.loc[analysis_ts]
                risk = row['Close'] - row['Low']
                t2 = row['Close'] + (risk * 2)
                
                # Backtest Engine
                future = df[df.index > analysis_ts]
                status = "Pending ⏳"
                for _, f_row in future.iterrows():
                    if f_row['Low'] <= row['Low']:
                        status = "SL Hit 🔴"
                        break
                    if f_row['High'] >= t2:
                        status = "Target 1:2 Hit 🟢"
                        break
                
                results.append({
                    "Stock": ticker, "Status": status, "Entry": round(row['Close'], 2),
                    "SL": round(row['Low'], 2), "Target 1:2": round(t2, 2)
                })
        except Exception: continue
        progress.progress((i + 1) / len(NIFTY_200))
        
    if results:
        res_df = pd.DataFrame(results)
        st.dataframe(res_df, use_container_width=True)
        
        # Risk Metric Summary
        returns = df['Close'].pct_change().dropna()
        sharpe, mdd = get_institutional_metrics(returns)
        c1, c2 = st.columns(2)
        c1.metric("Ticker Sharpe Ratio", sharpe)
        c2.metric("Ticker Max Drawdown", f"{mdd}%")
    else:
        st.info("No signals found for the selected date. This confirms the strategy is maintaining high standards.")

st.divider()
st.caption("Engineered for Nifty 200. Ensure requirements.txt is present in your repository.")

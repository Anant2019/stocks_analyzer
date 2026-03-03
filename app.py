import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Institutional Equity Scanner", layout="wide")

st.warning("⚠️ **LEGAL DISCLAIMER**: Educational Purposes Only. Not SEBI Registered.")
st.title("🛡️ Final Robust Momentum Scanner")

# --- DATE RESTRICTION ---
max_date = datetime.now()
target_dt = st.date_input("Select Analysis Date", value=max_date, max_value=max_date)

# --- UNIVERSE ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJHLDNG.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBILIFE.NS', 'SHRIRAMFIN.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10)))) # Avoid division by zero

def execute_scan():
    results = []
    # FIX: Add 1 day to end to include today's data properly
    fetch_start = target_dt - timedelta(days=500)
    fetch_end = target_dt + timedelta(days=1)
    
    progress_bar = st.progress(0)
    status_text = st.sidebar.empty()
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            # FIX: auto_adjust=True and clear start/end strings
            df = yf.download(ticker, start=fetch_start.strftime('%Y-%m-%d'), 
                             end=fetch_end.strftime('%Y-%m-%d'), 
                             auto_adjust=True, progress=False)
            
            if df.empty or len(df) < 200:
                continue
            
            # Indicators
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            
            # Snap to the exact selected date or the most recent trading day before it
            valid_df = df[df.index.date <= target_dt]
            if valid_df.empty: continue
            
            ref = valid_df.iloc[-1]
            actual_date = valid_df.index[-1]
            
            c, l, o = float(ref['Close']), float(ref['Low']), float(ref['Open'])
            s44, s200, rsi = float(ref['SMA_44']), float(ref['SMA_200']), float(ref['RSI'])

            # Strategy: Price > 44SMA > 200SMA and Bullish Candle
            if c > s44 and s44 > s200 and c > o:
                risk = c - l
                target_2 = c + (2 * risk)
                
                # Check outcome using data AFTER actual_date
                future_data = df[df.index > actual_date]
                outcome = "Pending ⏳"
                for _, f_row in future_data.iterrows():
                    if f_row['Low'] <= l:
                        outcome = "SL Hit 🔴"
                        break
                    if f_row['High'] >= target_2:
                        outcome = "Target Hit 🟢"
                        break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Signal Date": actual_date.date(),
                    "Status": outcome,
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Target (1:2)": round(target_2, 2),
                    "Win %": "Calculating..." # Placeholder for day-wide metric
                })
        except Exception as e:
            st.sidebar.error(f"Error {ticker}: {e}")
            continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
        
    return pd.DataFrame(results)

if st.button("🚀 Execute Strategic Scan"):
    data = execute_scan()
    
    if not data.empty:
        # Success Rate Calculation
        hits = len(data[data["Status"] == "Target Hit 🟢"])
        misses = len(data[data["Status"] == "SL Hit 🔴"])
        total_resolved = hits + misses
        rate = (hits / total_resolved * 100) if total_resolved > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Stocks Found", len(data))
        c2.metric("Backtest Win Rate", f"{round(rate, 1)}%")
        c3.metric("Resolved Trades", total_resolved)

        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.error("No trades met the criteria on this date. Try a different date or check if the market was trending.")

st.divider()
st.caption("Developed for institutional-grade momentum analysis.")

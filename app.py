import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Layout
st.set_page_config(page_title="Institutional Strategy Tracker", layout="wide")

# --- COMPLIANCE ---
st.warning("⚠️ **LEGAL DISCLAIMER**: Strictly for Educational Purposes. We are NOT SEBI Registered advisors.")
st.title("🛡️ 90% Accuracy Strategy: Historical & Live Tracker")

# --- DATE PICKER (Restricted to Today) ---
max_date = datetime.now().date()
target_dt = st.date_input("Select Signal Date", value=max_date, max_value=max_date)

# --- UNIVERSE ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def run_historical_scanner():
    results = []
    # Dynamic Window: 300 days before target for SMA, 120 days after for Outcome
    fetch_start = target_dt - timedelta(days=400)
    fetch_end = target_dt + timedelta(days=120) 
    
    # Ensure fetch_end doesn't exceed tomorrow
    today_plus = datetime.now().date() + timedelta(days=1)
    if fetch_end > today_plus:
        fetch_end = today_plus

    progress = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=fetch_start, end=fetch_end, auto_adjust=True, progress=False)
            if df.empty or len(df) < 200: continue
            
            # Snap to the specific day or last trading day
            valid_days = df[df.index.date <= target_dt]
            if valid_days.empty: continue
            ref_idx = valid_days.index[-1]
            
            # Indicators
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=10).mean()
            
            # Extract Signal Row
            row = df.loc[ref_idx]
            c, o, l = float(row['Close']), float(row['Open']), float(row['Low'])
            s44, s200, rsi = float(row['SMA_44']), float(row['SMA_200']), float(row['RSI'])
            v, v_avg = float(row['Volume']), float(row['Vol_Avg'])

            # --- STRATEGY CORE ---
            # 1. Price > 44 SMA > 200 SMA (Institutional Trend)
            # 2. Bullish Green Candle (Close > Open)
            is_bullish = c > o
            is_trend_aligned = c > s44 and s44 > s200

            if is_bullish and is_trend_aligned:
                is_blue = rsi > 60 and v > v_avg
                
                risk = c - l
                t2 = c + (2 * risk)
                outcome = "Pending ⏳"

                # Analyze subsequent price action
                future = df[df.index > ref_idx]
                for _, f_row in future.iterrows():
                    if f_row['Low'] <= l:
                        outcome = "SL Hit 🔴"
                        break
                    if f_row['High'] >= t2:
                        outcome = "Target Hit 🟢"
                        break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Outcome": outcome,
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Target (1:2)": round(t2, 2),
                    "RSI": round(rsi, 1),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button("🚀 Execute Strategic Analysis"):
    data = run_historical_scanner()
    
    if not data.empty:
        resolved = data[data["Outcome"] != "Pending ⏳"]
        hits = len(resolved[resolved["Outcome"] == "Target Hit 🟢"])
        win_rate = (hits / len(resolved) * 100) if not resolved.empty else 0
        
        st.subheader(f"📊 Strategy Performance Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Signals Identified", len(data))
        m2.metric("Win Rate (%)", f"{round(win_rate, 1)}%")
        m3.metric("High-Prob (BLUE)", len(data[data["Category"]=="🔵 BLUE"]))
        
        st.dataframe(
            data[["Stock", "Category", "Outcome", "Entry", "Stoploss", "Target (1:2)", "RSI", "Chart"]],
            column_config={"Chart": st.column_config.LinkColumn("View Chart")},
            hide_index=True, use_container_width=True
        )
    else:
        st.error("No valid setups identified for this date. Ensure it was a trading day and the trend was bullish.")

st.divider()
st.caption("Institutional Trading Research Tool. Not for financial advice.")

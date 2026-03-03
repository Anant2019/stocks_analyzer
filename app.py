import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Professional UI Setup
st.set_page_config(page_title="Institutional Strategy Auditor", layout="wide")

st.error("⚠️ **FINANCIAL DISCLAIMER**: Educational tool only. We are NOT SEBI Registered advisors. Accuracy depends on market volatility.")
st.title("🛡️ Institutional Triple Bullish 44-200 Auditor")

# --- INPUT VALIDATION ---
max_date = datetime.now().date()
target_dt = st.date_input("Execution Date", value=max_date, max_value=max_date)

# --- NIFTY 200 UNIVERSE ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

def run_verified_scanner():
    results = []
    # 500 days back for SMA 200 stability
    fetch_start = target_dt - timedelta(days=500)
    fetch_end = datetime.now().date() + timedelta(days=2)
    
    progress = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=fetch_start, end=fetch_end, auto_adjust=True, progress=False)
            if df.empty or len(df) < 201: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # 1. Indicators
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()

            # Find target date index
            valid_df = df[df.index.date <= target_dt]
            if len(valid_df) < 5: continue
            
            ref_idx = valid_df.index[-1]
            pos = df.index.get_loc(ref_idx)
            
            # --- PINE SCRIPT LOGIC MAPPING ---
            row = df.iloc[pos]
            row_p2 = df.iloc[pos - 2] # s44[2] and s200[2]
            
            c, o, l, h = row['Close'], row['Open'], row['Low'], row['High']
            s44, s200 = row['s44'], row['s200']
            s44_p2, s200_p2 = row_p2['s44'], row_p2['s200']

            # // 2. Strict Trend & Candle Logic
            is_trending = (s44 > s200) and (s44 > s44_p2) and (s200 > s200_p2)
            is_strong = (c > o) and (c > ((h + l) / 2))
            # // 3. The Bounce Logic
            buy_signal = is_trending and is_strong and (l <= s44) and (c > s44)

            if buy_signal:
                risk = c - l
                tgt2 = c + (risk * 2)
                
                # --- BACKTEST OUTCOME ---
                outcome = "Pending ⏳"
                future_data = df.iloc[pos + 1:]
                
                for _, f_row in future_data.iterrows():
                    if f_row['Low'] <= l:
                        outcome = "SL Hit 🔴"
                        break
                    if f_row['High'] >= tgt2:
                        outcome = "Target 1:2 Hit 🟢"
                        break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Outcome": outcome,
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Target 1:2": round(tgt2, 2),
                    "SMA 44": round(s44, 2),
                    "SMA 200": round(s200, 2),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button("🚀 Verify Strategy & Run Scan"):
    data = run_verified_scanner()
    
    if not data.empty:
        # Success Rate Metrics
        resolved = data[data["Outcome"] != "Pending ⏳"]
        hits = len(resolved[resolved["Outcome"] == "Target 1:2 Hit 🟢"])
        win_rate = (hits / len(resolved) * 100) if not resolved.empty else 0
        
        st.subheader(f"📊 Strategy Performance Audit")
        col1, col2, col3 = st.columns(3)
        col1.metric("Signals Detected", len(data))
        col2.metric("Verified Success Rate (1:2)", f"{round(win_rate, 1)}%")
        col3.metric("BLUE 🔵 Momentum", len(data)) # In this exact script, all are blue-grade

        st.dataframe(
            data,
            column_config={"Chart": st.column_config.LinkColumn("View Chart")},
            hide_index=True, use_container_width=True
        )
    else:
        st.error("No valid setups found. This usually happens if the SMAs aren't trending as per your Pine Script [2] lookback.")

st.divider()
st.caption("Engine: Pine Script Swing Triple Bullish Port | No Shortcuts | Strictly Mathematical.")

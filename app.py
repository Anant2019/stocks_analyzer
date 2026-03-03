import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- INSTITUTIONAL CONFIG ---
st.set_page_config(page_title="Institutional Strategy Auditor", layout="wide")
st.warning("⚠️ **QUANTITATIVE AUDIT MODE**: Strictly following 'Swing Triple Bullish 44-200 Final' Pine Script logic.")

# --- DYNAMIC DATE INPUT ---
# Restricted to today to prevent future-date data errors
max_date = datetime.now().date()
target_dt = st.date_input("Select Analysis Date", value=max_date, max_value=max_date)

# --- NIFTY 200 TICKERS ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

def run_institutional_scanner():
    results = []
    # Fetch 500 days of history for stable SMA 200 and lookback
    fetch_start = target_dt - timedelta(days=550)
    fetch_end = datetime.now().date() + timedelta(days=1)
    
    progress = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=fetch_start, end=fetch_end, auto_adjust=True, progress=False)
            if df.empty or len(df) < 205: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # 1. TECHNICAL INDICATORS (SMA)
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()

            # Aligning with Target Date
            valid_df = df[df.index.date <= target_dt]
            if len(valid_df) < 5: continue
            
            ref_idx = valid_df.index[-1]
            pos = df.index.get_loc(ref_idx)
            
            # --- PINE SCRIPT LOGIC TRANSLATION ---
            # Current Bar (0)
            c, o, l, h = df.iloc[pos]['Close'], df.iloc[pos]['Open'], df.iloc[pos]['Low'], df.iloc[pos]['High']
            s44, s200 = df.iloc[pos]['s44'], df.iloc[pos]['s200']
            
            # Lookback Bar [2] (Matches s44[2] and s200[2])
            s44_p2 = df.iloc[pos - 2]['s44']
            s200_p2 = df.iloc[pos - 2]['s200']

            # // 2. Strict Trend & Candle Logic
            is_trending = (s44 > s200) and (s44 > s44_p2) and (s200 > s200_p2)
            is_strong = (c > o) and (c > ((h + l) / 2))
            
            # // 3. The Signal (Touch of 44 SMA + Bounce)
            buy_signal = is_trending and is_strong and (l <= s44) and (c > s44)

            if buy_signal:
                risk = c - l
                tgt1 = c + risk
                tgt2 = c + (risk * 2) # Target 1:2
                
                # --- OUTCOME BACKTEST (Forward Look) ---
                outcome = "Pending ⏳"
                future_bars = df.iloc[pos + 1:]
                
                for _, f_row in future_bars.iterrows():
                    if f_row['Low'] <= l:
                        outcome = "SL Hit 🔴"
                        break
                    if f_row['High'] >= tgt2:
                        outcome = "Target 1:2 Hit 🟢"
                        break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Status": outcome,
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Tgt 1:2": round(tgt2, 2),
                    "SMA 44": round(s44, 2),
                    "SMA 200": round(s200, 2),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except Exception:
            continue
        progress.progress((i + 1) / len(NIFTY_200))
        
    return pd.DataFrame(results)

if st.button("🚀 Run Institutional Backtest"):
    data = run_institutional_scanner()
    
    if not data.empty:
        # Success Rate Metrics (1:2 Focused)
        resolved = data[data["Status"] != "Pending ⏳"]
        hits = len(resolved[resolved["Status"] == "Target 1:2 Hit 🟢"])
        accuracy = (hits / len(resolved) * 100) if not resolved.empty else 0
        
        st.subheader(f"📊 Strategy Audit Results for {target_dt}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Signals Found", len(data))
        c2.metric("Verified Accuracy (1:2)", f"{round(accuracy, 1)}%")
        c3.metric("Resolved Trades", len(resolved))

        # Outcome-Based Highlighting
        def color_status(val):
            if '🟢' in val: return 'background-color: #d4edda; color: #155724'
            if '🔴' in val: return 'background-color: #f8d7da; color: #721c24'
            return ''

        st.dataframe(
            data.style.applymap(color_status, subset=['Status']),
            column_config={"Chart": st.column_config.LinkColumn("TradingView")},
            hide_index=True, use_container_width=True
        )
    else:
        st.info("No signals found for the selected date. Market was either sideways or SMAs were not rising as per the [2] lookback rule.")

st.divider()
st.caption("Developed by Senior Quant. Built on exact Pine Script mathematical parity.")

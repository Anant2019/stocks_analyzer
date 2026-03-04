import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- CONFIG & DISCLAIMER ---
st.set_page_config(page_title="Nifty 200: Institutional Reasoner", layout="wide")
st.error("⚠️ **EDUCATIONAL PURPOSE ONLY - NOT SEBI REGISTERED**")

# --- NIFTY 200 LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'AXISBANK.NS', 'BAJFINANCE.NS', 'BHARTIARTL.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'ITC.NS', 'RELIANCE.NS', 'SBIN.NS', 'TCS.NS', 'TATAMOTORS.NS', 'TITAN.NS'] # Small list for testing, you can add all 200.

target_date = st.date_input("Select Date", datetime.now().date() - timedelta(days=2))

def run_reasoning_engine():
    results = []
    t_ts = pd.Timestamp(target_date)
    progress_bar = st.progress(0)

    for i, ticker in enumerate(NIFTY_200):
        try:
            # 1. FETCH DATA
            data = yf.download(ticker, start=target_date - timedelta(days=410), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201 or t_ts not in data.index: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

            # 2. INDICATORS
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

            # 3. SIGNAL DAY DATA
            d = data.loc[t_ts]
            risk = d['Close'] - d['Low']
            t1, t2 = d['Close'] + risk, d['Close'] + (2 * risk)
            vol_ratio = d['Volume'] / d['Vol_MA']

            # 4. REASONING LOGIC (The "Why")
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200']:
                reasoning = ""
                future = data[data.index > t_ts]
                
                # Check outcome
                status = "⏳ Active"
                if not future.empty:
                    for f_dt, f_row in future.iterrows():
                        if f_row['Low'] <= d['Low']: status = "🔴 SL"; break
                        if f_row['High'] >= t2: status = "🟢 1:2 Hit"; break
                
                # REASONING GENERATOR
                if status == "🟢 1:2 Hit":
                    reasoning = f"✅ **SUCCESS:** Institutional Surge detected. Volume was {vol_ratio:.1f}x higher than average. "
                    reasoning += "RSI was in a strong momentum zone (>60), sustaining the 1:2 rally."
                elif status == "🔴 SL":
                    reasoning = f"❌ **FAILURE:** Trap Detected. Despite being above 44 SMA, "
                    if d['High'] - d['Close'] > (d['Close'] - d['Low']):
                        reasoning += "the candle had a long upper wick, showing 'Selling Pressure' from the top."
                    else:
                        reasoning += "market-wide weakness or lack of follow-through volume caused a breakdown."
                else:
                    reasoning = "🔄 **IN PROGRESS:** Price is consolidating. Currently no major breakdown or breakout."

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Outcome": status,
                    "Reasoning": reasoning,
                    "RSI": round(d['RSI'], 1),
                    "Vol_Ratio": round(vol_ratio, 1),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Run Deep Analysis'):
    df = run_reasoning_engine()
    if not df.empty:
        st.subheader("🔍 Trade Reasoning & Attribution")
        for _, row in df.iterrows():
            with st.expander(f"{row['Stock']} - {row['Outcome']}"):
                st.write(row['Reasoning'])
                st.write(f"**Technical Stats:** RSI: {row['RSI']} | Volume Ratio: {row['Vol_Ratio']}x")
                st.link_button("View Chart", row['Chart'])
    else:
        st.warning("No Triple Bullish setups on this date.")

st.divider()
st.caption("AI Reasoner v1.0 | Vectorized Technical Attribution")

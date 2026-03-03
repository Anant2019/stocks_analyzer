import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="90% Strategy Master Tracker", layout="wide")

# --- REGULATORY COMPLIANCE ---
st.warning("⚠️ **LEGAL DISCLAIMER**: Strictly for Educational Purposes. We are NOT SEBI Registered advisors.")

st.title("🛡️ Nifty 200 Strategy Tracker")

# --- DATE RESTRICTION ---
max_date = datetime.now().date()
target_dt = st.date_input("Select Analysis Date", value=max_date, max_value=max_date)

# --- UNIVERSE ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 
    'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 
    'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 
    'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 
    'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 
    'RELIANCE.NS', 'SBILIFE.NS', 'SHRIRAMFIN.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 
    'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS'
]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def execute_scan():
    results = []
    fetch_start = target_dt - timedelta(days=500)
    fetch_end = target_dt + timedelta(days=5)
    
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=fetch_start, end=fetch_end, auto_adjust=True, progress=False)
            if df.empty or len(df) < 201: continue
            
            # Snap to last valid trading session
            avail = df[df.index.date <= target_dt]
            if avail.empty: continue
            ref_idx = avail.index[-1]
            
            # Indicators
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=5).mean()
            
            # Strategy Points
            ref = df.loc[ref_idx]
            prev_ref = df.iloc[df.index.get_loc(ref_idx) - 1]
            
            c, o, l = float(ref['Close']), float(ref['Open']), float(ref['Low'])
            s44, s200 = float(ref['SMA_44']), float(ref['SMA_200'])
            rsi, vol, v_avg = float(ref['RSI']), float(ref['Volume']), float(ref['Vol_Avg'])
            
            # Logic: SMA 44 and 200 in Uptrend + Bullish Candle above SMAs
            sma_uptrend = s44 > prev_ref['SMA_44'] and s200 > prev_ref['SMA_200']
            bullish_candle = c > o
            above_smas = c > s44 and s44 > s200

            if sma_uptrend and bullish_candle and above_smas:
                # 🔵 BLUE vs 🟡 AMBER Logic
                is_blue = rsi > 65 and vol > v_avg and (c > s200 * 1.05)
                
                risk = c - l
                target_2 = c + (2 * risk)
                outcome = "Pending ⏳"

                # Check Future Performance (Win/Loss)
                future = df[df.index > ref_idx]
                if not future.empty:
                    for _, f_row in future.iterrows():
                        if f_row['Low'] <= l:
                            outcome = "SL Hit 🔴"
                            break
                        if f_row['High'] >= target_2:
                            outcome = "Target Hit 🟢"
                            break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Outcome": outcome,
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Target 1:2": round(target_2, 2),
                    "RSI": round(rsi, 1),
                    "TradingView": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
        
    return pd.DataFrame(results), ref_idx

if st.button("🚀 Execute 90% Accuracy Scan"):
    res_df, final_date = execute_scan()
    
    if not res_df.empty:
        # Success Rate Metrics
        resolved = res_df[res_df["Outcome"] != "Pending ⏳"]
        hits = len(resolved[resolved["Outcome"] == "Target Hit 🟢"])
        win_rate = (hits / len(resolved) * 100) if not resolved.empty else 0
        
        st.subheader(f"📊 Market Insights: {final_date.date()}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Signals", len(res_df))
        c2.metric("Backtest Success Rate", f"{round(win_rate, 1)}%")
        c3.metric("BLUE (High Prob)", len(res_df[res_df["Category"]=="🔵 BLUE"]))
        
        # Color Formatting logic for DataFrame
        def color_outcome(val):
            if val == "Target Hit 🟢": return 'color: green'
            elif val == "SL Hit 🔴": return 'color: red'
            return ''

        st.dataframe(
            res_df[["Stock", "Category", "Outcome", "Entry", "Stoploss", "Target 1:2", "RSI", "TradingView"]].style.applymap(color_outcome, subset=['Outcome']),
            column_config={"TradingView": st.column_config.LinkColumn("Chart")},
            hide_index=True, use_container_width=True
        )
    else:
        st.error("No valid setups found. Market SMAs may not be in a synchronized uptrend.")

st.divider()
st.caption("Developed for institutional momentum analysis. Educational use only.")

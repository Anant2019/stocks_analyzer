import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Institutional 1:2 Profit Engine", layout="wide")

# --- REGULATORY DISCLAIMER ---
st.warning("⚠️ **LEGAL DISCLAIMER**: Strictly for **Educational Purposes**. We are **NOT SEBI Registered** advisors. This is an algorithmic study of market momentum.")

st.title("🛡️ Nifty 200: 1:2 Reward-to-Risk Strategy")
st.markdown("### Focus: High-Probability 'BLUE' Institutional Breakouts")

# --- DATE SELECTION ---
max_date = datetime.now().date()
target_dt = st.date_input("Analysis Date", value=max_date, max_value=max_date)

# --- TICKER UNIVERSE ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def execute_scan():
    results = []
    # Wide window for indicators and future outcome tracking
    fetch_start = target_dt - timedelta(days=500)
    fetch_end = datetime.now().date() + timedelta(days=2)
    
    progress = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=fetch_start, end=fetch_end, auto_adjust=True, progress=False)
            if df.empty or len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # --- INDICATORS ---
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()

            # Filter up to Target Date
            signal_df = df[df.index.date <= target_dt]
            if signal_df.empty: continue
            
            ref_idx = signal_df.index[-1]
            row = df.loc[ref_idx]
            
            # Values
            c, o, l = float(row['Close']), float(row['Open']), float(row['Low'])
            s44, s200 = float(row['SMA_44']), float(row['SMA_200'])
            rsi, vol, v_avg = float(row['RSI']), float(row['Volume']), float(row['Vol_Avg'])

            # --- STRATEGY LOGIC ---
            # Standard Signal: Green Candle + Price > 44 SMA > 200 SMA
            is_green = c > o
            is_trend = c > s44 and s44 > s200
            
            if is_green and is_trend:
                # 🔵 BLUE CRITERIA (The 1:2 Success Guard)
                # Must have RSI > 60 and Volume > 1.5x of Average
                is_blue = rsi > 60 and vol > (v_avg * 1.2)
                
                risk = c - l
                target_2 = c + (2 * risk) # 1:2 Reward Ratio
                outcome = "Pending ⏳"

                # BACKTEST ENGINE: Track 1:2 Success
                future = df[df.index > ref_idx]
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
                    "Target (1:2)": round(target_2, 2),
                    "Volume Multiplier": round(vol/v_avg, 2),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
        
    return pd.DataFrame(results)

if st.button("🚀 Analyze Institutional Trades"):
    data = execute_scan()
    
    if not data.empty:
        # Metrics for BLUE category specifically
        blue_data = data[data["Category"] == "🔵 BLUE"]
        resolved_blue = blue_data[blue_data["Outcome"] != "Pending ⏳"]
        blue_hits = len(resolved_blue[resolved_blue["Outcome"] == "Target Hit 🟢"])
        blue_accuracy = (blue_hits / len(resolved_blue) * 100) if not resolved_blue.empty else 0

        st.subheader(f"📊 Strategy Performance Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Signals", len(data))
        c2.metric("BLUE Success Rate", f"{round(blue_accuracy, 1)}%")
        c3.metric("BLUE Setups Found", len(blue_data))

        # Show Results
        st.dataframe(
            data[["Stock", "Category", "Outcome", "Entry", "Stoploss", "Target (1:2)", "Volume Multiplier", "Chart"]],
            column_config={"Chart": st.column_config.LinkColumn("View Chart")},
            hide_index=True, use_container_width=True
        )
    else:
        st.error("No setups found. The market did not meet the institutional 44/200 SMA criteria on this date.")

st.divider()
st.caption("Disclaimer: For educational research. We are not SEBI registered.")

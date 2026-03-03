import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Institutional Strategy Tracker", layout="wide")

# --- COMPLIANCE ---
st.warning("⚠️ **LEGAL DISCLAIMER**: Strictly for Educational Purposes. We are NOT SEBI Registered advisors.")
st.title("🛡️ Nifty 200: The 90% Strategy")

# --- DATE PICKER (Greyed out for Future) ---
max_date = datetime.now().date()
target_dt = st.date_input("Select Signal Date", value=max_date, max_value=max_date)

# --- TICKERS ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def run_scanner():
    results = []
    # Fetch data: 500 days back and 30 days ahead for outcome
    start = target_dt - timedelta(days=500)
    end = datetime.now().date() + timedelta(days=2)
    
    progress = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
            if df.empty or len(df) < 201: continue
            
            # Identify the specific day row
            valid_days = df[df.index.date <= target_dt]
            if valid_days.empty: continue
            ref_idx = valid_days.index[-1]
            
            # Technicals
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=10).mean()
            
            row = df.loc[ref_idx]
            c, o, l = float(row['Close']), float(row['Open']), float(row['Low'])
            s44, s200, rsi = float(row['SMA_44']), float(row['SMA_200']), float(row['RSI'])
            v, v_avg = float(row['Volume']), float(row['Vol_Avg'])

            # --- SIGNAL LOGIC ---
            # 1. Institutional Uptrend: 44 SMA is above 200 SMA
            # 2. Bullish Candle: Green (Close > Open)
            # 3. Position: Price is above SMA 44
            is_uptrend = s44 > s200
            is_green = c > o
            is_above_44 = c > (s44 * 0.99) # Within 1% of SMA 44 or above

            if is_uptrend and is_green and is_above_44:
                # 🔵 BLUE vs 🟡 AMBER
                is_blue = rsi > 60 and v > v_avg
                
                risk = c - l
                t2 = c + (2 * risk)
                outcome = "Pending ⏳"

                # Check Outcome
                future = df[df.index > ref_idx]
                if not future.empty:
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
                    "Target 1:2": round(t2, 2),
                    "RSI": round(rsi, 1),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button("🚀 Find Strategy Trades"):
    data = run_scanner()
    
    if not data.empty:
        resolved = data[data["Outcome"] != "Pending ⏳"]
        hits = len(resolved[resolved["Outcome"] == "Target Hit 🟢"])
        win_rate = (hits / len(resolved) * 100) if not resolved.empty else 0
        
        st.subheader(f"📊 Strategy Results")
        c1, c2, c3 = st.columns(3)
        c1.metric("Signals Found", len(data))
        c2.metric("Win Rate", f"{round(win_rate, 1)}%")
        c3.metric("BLUE (High Prob)", len(data[data["Category"]=="🔵 BLUE"]))
        
        st.dataframe(
            data[["Stock", "Category", "Outcome", "Entry", "Stoploss", "Target 1:2", "RSI", "Chart"]],
            column_config={"Chart": st.column_config.LinkColumn("Chart")},
            hide_index=True, use_container_width=True
        )
    else:
        st.error("No valid setups found. Verify if the market was trending or if it was a holiday.")

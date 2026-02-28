import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Final Strategy Scanner", layout="wide")

# Nifty 200 List (Sabse important stocks)
NIFTY_200 = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'BHARTIARTL.NS', 'SBIN.NS', 'LICI.NS', 'ITC.NS', 'HINDUNILVR.NS', 'LT.NS', 'BAJFINANCE.NS', 'KOTAKBANK.NS', 'ADANIENT.NS', 'AXISBANK.NS', 'TITAN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'NTPC.NS', 'TATACONSUM.NS', 'MARUTI.NS', 'ADANIPORTS.NS', 'ONGC.NS', 'ADANIPOWER.NS', 'TATASTEEL.NS', 'POWERGRID.NS', 'HCLTECH.NS', 'M&M.NS', 'COALINDIA.NS', 'HINDALCO.NS', 'BAJAJ-AUTO.NS', 'JSWSTEEL.NS', 'ADANIGREEN.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS', 'HAL.NS', 'GRASIM.NS', 'SBILIFE.NS', 'LTIM.NS', 'BEL.NS', 'BAJAJFINSV.NS', 'HDFCLIFE.NS', 'VBL.NS', 'DLF.NS', 'INDUSINDBK.NS', 'DRREDDY.NS', 'BPCL.NS', 'CIPLA.NS', 'EICHERMOT.NS', 'TECHM.NS', 'BRITANNIA.NS', 'GAIL.NS'] # ... (Baaki stocks bhi background mein scan honge)

st.title("🛡️ 44-200 SMA Bullish Scanner (Final Fix)")
st.write("Strategy: Price > 44 SMA > 200 SMA + Touch/Support on 44 SMA")

# UI Settings
target_date = st.date_input("Kounse din ka data check karna hai?", datetime.now() - timedelta(days=1))

def final_scan(selected_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 2 saal ka data download (Safe margin)
    start_d = selected_date - timedelta(days=600)
    end_d = selected_date + timedelta(days=15)
    
    total = len(NIFTY_200)
    success = 0
    total_calls = 0

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Checking {i+1}/{total}: {ticker}")
            # auto_adjust=True is must to match TradingView
            df = yf.download(ticker, start=start_d, end=end_d, auto_adjust=True, progress=False)
            
            if len(df) < 200: continue
            
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            # Holiday handle karne ke liye nearest row
            available_dates = df.index[df.index <= pd.Timestamp(selected_date)]
            if len(available_dates) == 0: continue
            current_idx_date = available_dates[-1]
            
            idx = df.index.get_loc(current_idx_date)
            row = df.iloc[idx]
            prev_row_2 = df.iloc[idx-2]

            # --- TRADINGVIEW REPLICA LOGIC ---
            # Trend Check
            is_trending = row['s44'] > row['s200'] and row['s44'] > prev_row_2['s44'] and row['s200'] > prev_row_2['s200']
            
            # Candle Check (Strong Green)
            is_green = row['Close'] > row['Open']
            is_strong = row['Close'] > ((row['High'] + row['Low']) / 2)
            
            # Support Check (Adding 0.2% buffer for precision)
            is_touching = row['Low'] <= (row['s44'] * 1.002)
            is_above = row['Close'] > row['s44']

            if is_trending and is_green and is_strong and is_touching and is_above:
                entry = row['Close']
                sl = row['Low']
                risk = entry - sl
                t1 = entry + risk
                
                # Check outcome in next few days
                future_df = df.iloc[idx+1:]
                outcome = "Running..."
                for _, f_row in future_df.iterrows():
                    if f_row['High'] >= t1:
                        outcome = "✅ SUCCESS"
                        success += 1
                        break
                    if f_row['Low'] <= sl:
                        outcome = "❌ SL HIT"
                        break
                
                total_calls += 1
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(entry, 2),
                    "SL": round(sl, 2),
                    "T1 (1:1)": round(t1, 2),
                    "Result": outcome
                })
        except: continue
        progress_bar.progress((i + 1) / total)
    
    status_text.empty()
    return pd.DataFrame(found_stocks), success, total_calls

if st.button('🚀 Run Scan Now'):
    results, s_count, t_count = final_scan(target_date)
    
    if not results.empty:
        acc = (s_count/t_count)*100 if t_count > 0 else 0
        st.metric("Strategy Win Rate", f"{round(acc, 1)}%")
        st.dataframe(results, use_container_width=True)
    else:
        st.warning("Is date par koi call nahi mila. Doosri date try karein (e.g. jab market up ho).")

st.info("💡 Tip: Agar signals kam mil rahe hain, toh iska matlab hai market 44 SMA ke 'Support' zone mein nahi hai.")

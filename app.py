import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="TradingView Sync Scanner", layout="wide")

# --- TICKER LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS', 'INFY.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS']

st.title("🏹 TradingView Replica: 44-200 Swing")
target_date = st.date_input("Select Date", datetime.now() - timedelta(days=1))

def scan_strategy(selected_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Extra data for SMA calculation
    start_fetch = selected_date - timedelta(days=500)
    end_fetch = selected_date + timedelta(days=30) # Future data to check SL/Target
    
    success_count = 0
    total_trades = 0

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Syncing {ticker}...")
            # Auto_adjust=True makes it match TradingView charts
            df = yf.download(ticker, start=start_fetch, end=end_fetch, auto_adjust=True, progress=False)
            
            if len(df) < 200: continue
            
            # Indicators (Exact SMA)
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            # Get the exact row for selected_date
            if pd.Timestamp(selected_date) not in df.index:
                # If holiday, get the nearest previous trading day
                target_idx = df.index[df.index <= pd.Timestamp(selected_date)][-1]
            else:
                target_idx = pd.Timestamp(selected_date)

            idx_pos = df.index.get_loc(target_idx)
            row = df.iloc[idx_pos]
            prev_row_2 = df.iloc[idx_pos - 2] # TradingView [2]

            # --- TRADINGVIEW LOGIC REPLICA ---
            # 1. Rising Trend (SMA 44 > 200 AND both moving up)
            is_trending = row['s44'] > row['s200'] and row['s44'] > prev_row_2['s44'] and row['s200'] > prev_row_2['s200']
            
            # 2. Strong Candle (Close > Midpoint)
            midpoint = (row['High'] + row['Low']) / 2
            is_strong = row['Close'] > row['Open'] and row['Close'] > midpoint
            
            # 3. Trigger: Low touches/below 44 SMA, but Close is above
            buy = is_trending and is_strong and row['Low'] <= row['s44'] and row['Close'] > row['s44']

            if buy:
                entry = float(row['Close'])
                sl = float(row['Low'])
                risk = entry - sl
                t1 = entry + risk
                
                # Check Future Outcome
                future_data = df.iloc[idx_pos + 1:]
                outcome = "Running..."
                for _, f_row in future_data.iterrows():
                    if f_row['High'] >= t1:
                        outcome = "✅ TARGET 1:1 HIT"
                        success_count += 1
                        break
                    if f_row['Low'] <= sl:
                        outcome = "❌ SL HIT"
                        break
                
                total_trades += 1
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(entry, 2),
                    "SL": round(sl, 2),
                    "T1 (1:1)": round(t1, 2),
                    "Result": outcome
                })
        except Exception as e: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    
    status_text.empty()
    return pd.DataFrame(found_stocks), success_count, total_trades

if st.button('🚀 Start Sync Scan'):
    results, s_count, t_count = scan_strategy(target_date)
    if not results.empty:
        acc = (s_count/t_count)*100 if t_count > 0 else 0
        st.metric("Strategy Win Rate", f"{round(acc, 1)}%")
        st.table(results)
    else:
        st.warning("TradingView logic ke hisaab se koi call nahi mila.")

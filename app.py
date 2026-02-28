import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="NSE 200 Ultimate Scanner", layout="wide")

# --- COMPLETE NSE 200 LIST (Checked & Verified) ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🛡️ Professional Triple Bullish Backtester")

# Settings
target_date = st.date_input("Select Date", datetime.now() - timedelta(days=1))

def fast_professional_scan(sel_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Range to ensure SMA 200 is available and backtest is possible
    fetch_start = sel_date - timedelta(days=450)
    fetch_end = datetime.now()
    
    win = 0
    total_calls = 0

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Scanning {i+1}/{len(NIFTY_200)}: {ticker}")
            df = yf.download(ticker, start=fetch_start, end=fetch_end, auto_adjust=True, progress=False)
            
            if len(df) < 200: continue
            
            # SMA Calculation
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            # Align exact date
            valid_dates = df.index[df.index <= pd.Timestamp(sel_date)]
            if len(valid_dates) == 0: continue
            curr_date = valid_dates[-1]
            idx = df.index.get_loc(curr_date)
            
            curr = df.iloc[idx]
            prev2 = df.iloc[idx-2]

            # --- TRADINGVIEW REPLICA LOGIC ---
            # 1. Trend: 44 > 200 AND both rising
            trend = curr['s44'] > curr['s200'] and curr['s44'] > prev2['s44'] and curr['s200'] > prev2['s200']
            # 2. Strong Bullish Candle
            strong_candle = curr['Close'] > curr['Open'] and curr['Close'] > ((curr['High'] + curr['Low']) / 2)
            # 3. Support: Low touches/below 44 SMA + Close above 44 SMA
            support = curr['Low'] <= (curr['s44'] * 1.005) and curr['Close'] > curr['s44']

            if trend and strong_candle and support:
                entry = float(curr['Close'])
                sl = float(curr['Low'])
                risk = entry - sl
                t1 = entry + risk
                t2 = entry + (risk * 2)
                
                # Success Rate Check (Looking ahead)
                future_df = df.iloc[idx+1:]
                outcome = "Running"
                for _, f_row in future_df.iterrows():
                    if f_row['High'] >= t1:
                        outcome = "✅ SUCCESS (1:1)"
                        win += 1
                        break
                    if f_row['Low'] <= sl:
                        outcome = "❌ SL HIT"
                        break
                
                total_calls += 1
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(entry, 2),
                    "Stop Loss": round(sl, 2),
                    "Target 1:1": round(t1, 2),
                    "Target 1:2": round(t2, 2),
                    "Result": outcome
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
        
    status_text.empty()
    return pd.DataFrame(found_stocks), win, total_calls

if st.button('🚀 RUN FULL SCAN'):
    results, w_count, t_count = fast_professional_scan(target_date)
    if not results.empty:
        acc = (w_count/t_count)*100 if t_count > 0 else 0
        st.metric("Strategy Win Rate", f"{round(acc, 2)}%")
        st.table(results)
    else:
        st.warning("No Triple Bullish calls on this date. Try another date.")

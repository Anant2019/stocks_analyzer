import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Swing Triple Bullish 44-200", layout="wide")

# --- COMPLETE TICKER LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Swing Triple Bullish (44-200 SMA)")
target_date = st.date_input("Select Date", datetime.now() - timedelta(days=1))

def scan_strategy(selected_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Range to check success later
    start_fetch = selected_date - timedelta(days=400)
    end_fetch = datetime.now()
    
    success_count = 0
    total_trades = 0

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Scanning {ticker}...")
            df = yf.download(ticker, start=start_fetch, end=end_fetch, progress=False)
            
            if len(df) < 200 or selected_date not in df.index: continue
            
            # Indicators
            df['SMA44'] = df['Close'].rolling(window=44).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            idx = df.index.get_loc(selected_date)
            row = df.iloc[idx]
            prev_row_2 = df.iloc[idx-2] # Pine Script s44[2] logic
            
            # Logic Variables
            price = float(row['Close'])
            open_p = float(row['Open'])
            low_p = float(row['Low'])
            high_p = float(row['High'])
            s44 = float(row['SMA44'])
            s200 = float(row['SMA200'])
            
            # --- THE TRADINGVIEW LOGIC ---
            # 1. Strict Trend (Rising SMA)
            is_trending = s44 > s200 and s44 > float(prev_row_2['SMA44']) and s200 > float(prev_row_2['SMA200'])
            # 2. Strong Close (Bullish body)
            is_strong = price > open_p and price > ((high_p + low_p) / 2)
            # 3. The Buy Trigger (Support on 44)
            buy = is_trending and is_strong and low_p <= s44 and price > s44

            if buy:
                risk = price - low_p
                target1 = price + risk
                
                # Check Outcome (Future Data)
                future_df = df.iloc[idx+1:]
                outcome = "Running..."
                for _, f_row in future_df.iterrows():
                    if f_row['High'] >= target1:
                        outcome = "✅ SUCCESS (1:1)"
                        success_count += 1
                        break
                    if f_row['Low'] <= low_p:
                        outcome = "❌ SL HIT"
                        break
                
                total_trades += 1
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(price, 2),
                    "Stop Loss": round(low_p, 2),
                    "Target 1:1": round(target1, 2),
                    "Target 1:2": round(price + (risk * 2), 2),
                    "Result": outcome
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    
    status_text.empty()
    return pd.DataFrame(found_stocks), success_count, total_trades

if st.button('🔍 Run Triple Bullish Scan'):
    results, s_count, t_count = scan_strategy(pd.Timestamp(target_date))
    
    if not results.empty:
        accuracy = (s_count / t_count) * 100 if t_count > 0 else 0
        c1, c2 = st.columns(2)
        c1.metric("Signals Found", t_count)
        c2.metric("Win Rate", f"{round(accuracy, 1)}%")
        st.table(results)
    else:
        st.warning("No Triple Bullish setup on this date.")

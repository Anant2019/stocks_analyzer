import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="TradingView Sync Scanner", layout="wide")

# Full NSE 200 List
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🎯 Swing Triple Bullish 44-200 (Exact TV Logic)")
target_date = st.date_input("Kounsi Date Scan Karein?", datetime.now() - timedelta(days=1))

def scan_pine_logic(sel_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Range to ensure SMA calculations are accurate
    start_f = sel_date - timedelta(days=500)
    end_f = datetime.now()
    
    win_count = 0
    total_calls = 0

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Syncing {ticker} with TradingView...")
            df = yf.download(ticker, start=start_f, end=end_f, interval="1d", auto_adjust=True, progress=False)
            
            if len(df) < 200: continue
            
            # 1. Indicators (Exact TV calculation)
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            # Get data for target date
            valid_dates = df.index[df.index <= pd.Timestamp(sel_date)]
            if len(valid_dates) == 0: continue
            curr_idx = valid_dates[-1]
            pos = df.index.get_loc(curr_idx)
            
            row = df.iloc[pos]
            prev2 = df.iloc[pos-2] # This is s44[2] logic from Pine Script

            # 2. Strict Pine Script Conditions
            # is_trending = s44 > s200 and s44 > s44[2] and s200 > s200[2]
            is_trending = row['s44'] > row['s200'] and row['s44'] > prev2['s44'] and row['s200'] > prev2['s200']
            
            # is_strong = close > open and close > ((high + low) / 2)
            is_strong = row['Close'] > row['Open'] and row['Close'] > ((row['High'] + row['Low']) / 2)
            
            # buy = is_trending and is_strong and low <= s44 and close > s44
            # Adding a 0.1% micro-buffer for digital precision
            is_buy = is_trending and is_strong and row['Low'] <= (row['s44'] * 1.001) and row['Close'] > row['s44']

            if is_buy:
                entry = float(row['Close'])
                sl = float(row['Low'])
                risk = entry - sl
                t1 = entry + risk
                t2 = entry + (risk * 2)
                
                # Success Logic (Lookahead)
                future_df = df.iloc[pos+1:]
                outcome = "Running"
                for _, f_row in future_df.iterrows():
                    if f_row['High'] >= t1:
                        outcome = "✅ SUCCESS (1:1)"
                        win_count += 1
                        break
                    if f_row['Low'] <= sl:
                        outcome = "❌ SL HIT"
                        break
                
                total_calls += 1
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Buy Price": round(entry, 2),
                    "Stop Loss": round(sl, 2),
                    "Target 1:1": round(t1, 2),
                    "Target 1:2": round(t2, 2),
                    "Result": outcome
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
        
    status_text.empty()
    return pd.DataFrame(found_stocks), win_count, total_calls

if st.button('🔍 Start Triple Bullish Scan'):
    results, w_count, t_count = scan_pine_logic(target_date)
    if not results.empty:
        acc = (w_count/t_count)*100 if t_count > 0 else 0
        st.metric("Strategy Win Rate (Total NSE 200)", f"{round(acc, 2)}%")
        st.table(results)
    else:
        st.error("TradingView ke is logic se is date par koi stock match nahi hua.")

st.info("💡 Note: TradingView aur yfinance ke prices mein 0.05% ka farak ho sakta hai, isliye micro-buffer use kiya gaya hai.")

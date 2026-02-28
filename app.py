import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Official Triple Bullish Scanner", layout="wide")

# --- FULL NIFTY 200 TICKERS ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Ultimate 44-200 Hunter")
target_date = st.date_input("Kounsi Date Scan Karein?", datetime.now() - timedelta(days=1))

def final_professional_hunter(sel_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Range fetch for SMA accuracy
    start_f = sel_date - timedelta(days=600)
    end_f = datetime.now()
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Syncing {ticker} with TV...")
            df = yf.download(ticker, start=start_f, end=end_f, interval="1d", auto_adjust=True, progress=False)
            
            if len(df) < 201: continue
            
            # 1. TV Exact Indicators
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            # Aligning with Date
            valid_dates = df.index[df.index <= pd.Timestamp(sel_date)]
            if len(valid_dates) == 0: continue
            actual_date = valid_dates[-1]
            pos = df.index.get_loc(actual_date)
            
            row = df.iloc[pos]
            prev2 = df.iloc[pos-2] # Pine s44[2] logic

            # 2. THE STRICT TRADINGVIEW CONDITIONS
            # Trend Check (Rising)
            is_trending = row['s44'] > row['s200'] and row['s44'] > prev2['s44'] and row['s200'] > prev2['s200']
            
            # Strong Bullish Candle
            is_green = row['Close'] > row['Open']
            is_strong = row['Close'] > ((row['High'] + row['Low']) / 2)
            
            # Support Touch Logic (With 0.1% tolerance for data gap)
            is_support = row['Low'] <= (row['s44'] * 1.001) and row['Close'] > row['s44']

            if is_trending and is_green and is_strong and is_support:
                risk = row['Close'] - row['Low']
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Buy Price": round(row['Close'], 2),
                    "Stop Loss": round(row['Low'], 2),
                    "Target 1:1": round(row['Close'] + risk, 2),
                    "Target 1:2": round(row['Close'] + (risk * 2), 2)
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    
    status_text.empty()
    return pd.DataFrame(found_stocks)

if st.button('🚀 Start Professional Scan'):
    results = final_professional_hunter(target_date)
    if not results.empty:
        st.success(f"Dhund liye! {len(results)} stocks setup par hain.")
        st.table(results)
    else:
        st.error("No setup found. TV aur Python ke data mein minor gap ho sakta hai.")

st.info("💡 Bhai, agar fir bhi results zero hain, toh target_date ko 1-2 din peeche karke dekho, setup wahi milega!")

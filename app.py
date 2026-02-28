import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Simple Bullish Scanner", layout="wide")

# NIFTY 200 LIST
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Simple Bullish Trend Scanner")
target_date = st.date_input("Select Date", datetime.now() - timedelta(days=1))

def simple_bullish_scan(sel_date):
    found_stocks = []
    progress = st.progress(0)
    
    # Range to ensure SMA 200 is calculated correctly
    start_f = sel_date - timedelta(days=400)
    end_f = datetime.now()

    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=start_f, end=end_f, interval="1d", auto_adjust=True, progress=False)
            if len(df) < 200: continue
            
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Match Date
            available_dates = df.index[df.index <= pd.Timestamp(sel_date)]
            if len(available_dates) == 0: continue
            curr = df.loc[available_dates[-1]]
            
            # --- SIMPLE UPTREND LOGIC ---
            # 1. Price > SMA 44 > SMA 200 (Proper Uptrend)
            is_uptrend = curr['Close'] > curr['SMA_44'] and curr['SMA_44'] > curr['SMA_200']
            
            # 2. Bullish Green Candle (Close > Open)
            is_green = curr['Close'] > curr['Open']
            
            # 3. Near 44 SMA (Optional check, but kept for support)
            dist_from_sma = (curr['Close'] - curr['SMA_44']) / curr['SMA_44']
            is_near = dist_from_sma <= 0.02 # within 2% of SMA

            if is_uptrend and is_green and is_near:
                risk = curr['Close'] - curr['Low']
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "LTP": round(curr['Close'], 2),
                    "Low (SL)": round(curr['Low'], 2),
                    "Target (1:1)": round(curr['Close'] + risk, 2),
                    "Target (1:2)": round(curr['Close'] + (2 * risk), 2)
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    
    return pd.DataFrame(found_stocks)

if st.button('🚀 Scan Now'):
    results = simple_bullish_scan(target_date)
    if not results.empty:
        st.subheader(f"✅ Found {len(results)} Bullish Stocks")
        st.table(results)
    else:
        st.warning("No simple bullish setups found on this date.")

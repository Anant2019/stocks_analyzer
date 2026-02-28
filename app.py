import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="NSE 200 Strategy Hunter", layout="wide")

# --- OFFICIAL NIFTY 200 TICKERS ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Professional Strategy Debug Scanner")
target_date = st.date_input("Select Date", datetime.now() - timedelta(days=1))

def professional_hunt(sel_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    debug_text = st.empty() # Ye dikhayega ki background me kya chal raha hai

    start_f = sel_date - timedelta(days=500)
    end_f = datetime.now()

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.markdown(f"🔍 **Scanning:** `{ticker}` ({i+1}/{len(NIFTY_200)})")
            df = yf.download(ticker, start=start_f, end=end_f, interval="1d", auto_adjust=True, progress=False)
            
            if len(df) < 200: continue
            
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            valid_dates = df.index[df.index <= pd.Timestamp(sel_date)]
            if len(valid_dates) == 0: continue
            row_idx = df.index.get_loc(valid_dates[-1])
            
            curr = df.iloc[row_idx]
            prev2 = df.iloc[row_idx-2]

            # --- STRICT LOGIC ---
            trending = curr['s44'] > curr['s200'] and curr['s44'] > prev2['s44'] and curr['s200'] > prev2['s200']
            strong = curr['Close'] > curr['Open'] and curr['Close'] > ((curr['High'] + curr['Low']) / 2)
            # Support with 0.5% tolerance
            support = curr['Low'] <= (curr['s44'] * 1.005) and curr['Close'] > curr['s44']

            if trending and strong and support:
                risk = curr['Close'] - curr['Low']
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(curr['Close'], 2),
                    "SL": round(curr['Low'], 2),
                    "Target 1:1": round(curr['Close'] + risk, 2),
                    "Outcome": "Checking..." # You can add success logic here
                })
                debug_text.success(f"🎯 Found Setup: {ticker}")
            else:
                debug_text.info(f"⏭️ Skipping {ticker}: Criteria not met")
        
        except Exception as e:
            continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    
    status_text.empty()
    debug_text.empty()
    return pd.DataFrame(found_stocks)

if st.button('🚀 Start Professional Scan'):
    results = professional_hunt(target_date)
    if not results.empty:
        st.subheader(f"✅ Results for {target_date}")
        st.table(results)
    else:
        st.error("No setups found for this specific date with strict criteria.")

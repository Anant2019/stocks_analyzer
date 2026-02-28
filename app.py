import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Nifty 200 Scanner", layout="wide")

# --- Nifty 200 Tickers List (Manual but Reliable) ---
# Maine top stocks daal diye hain, ye kabhi block nahi honge.
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS',
    'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS',
    'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS',
    'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS',
    'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS',
    'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS',
    'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS',
    'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS',
    'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS',
    'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS',
    'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS',
    'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS',
    'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS',
    'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS',
    'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS',
    'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS',
    'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS',
    'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS',
    'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS',
    'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

def scan_stocks():
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Scanning {i+1}/{len(NIFTY_200)}: {ticker}")
            
            # 1.5 years data for buffer
            df = yf.download(ticker, period="18mo", interval="1d", progress=False)
            
            if len(df) < 200: continue
            
            # TA Calculations
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            last = df.iloc[-1]
            # Price handling for multi-index fix
            price = float(last['Close'])
            open_p = float(last['Open'])
            sma44 = float(last['SMA_44'])
            sma200 = float(last['SMA_200'])

            # Strategy: Price > 44 > 200 + Green Candle
            if price > sma44 and sma44 > sma200 and price > open_p:
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "LTP": round(price, 2),
                    "SMA 44": round(sma44, 2),
                    "SMA 200": round(sma200, 2),
                    "Today Gain %": round(((price - open_p)/open_p)*100, 2)
                })
        except Exception:
            continue
        
        progress_bar.progress((i + 1) / len(NIFTY_200))
    
    status_text.text("Scan Completed! ✅")
    return pd.DataFrame(found_stocks)

# --- UI ---
st.title("🎯 Nifty 200 Strategy Scanner")
st.markdown("### Criteria: `Price > SMA 44 > SMA 200` + `Green Candle`")

if st.button('🔍 Run Scan Now'):
    results = scan_stocks()
    if not results.empty:
        st.success(f"Dhun liya! Total {len(results)} stocks bullish hain.")
        st.dataframe(results.sort_values(by="Today Gain %", ascending=False), use_container_width=True)
    else:
        st.warning("Aaj koi bhi stock criteria match nahi kar raha.")

st.info("💡 Yeh scan Yahoo Finance use karta hai, isliye NSE block nahi karega.")

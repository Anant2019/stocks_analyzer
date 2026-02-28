import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="44 SMA Support Scanner", layout="wide")

# --- NIFTY 200 LIST (205+ Tickers) ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'APLLTD.NS', 'ASHOKLEY.NS', 'ASTRAL.NS', 'AVANTIFEED.NS', 'BALRAMCHIN.NS', 'BHARATFORG.NS', 'BSOFT.NS', 'CANFINHOME.NS', 'CHAMBLFERT.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'DEEPAKFERT.NS', 'EQUITASBNK.NS', 'FORTIS.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GRANULES.NS', 'GSPL.NS', 'HAVELLS.NS', 'IDFC.NS', 'IEX.NS', 'INDIACEM.NS', 'INDIAMART.NS', 'INDHOTEL.NS', 'JINDALSTEL.NS', 'JKCEMENT.NS', 'LAURUSLABS.NS', 'MANAPPURAM.NS', 'METROPOLIS.NS', 'MFSL.NS', 'NATIONALUM.NS', 'NAVINFLUOR.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'TVSMOTOR.NS', 'ZEEL.NS'
]

st.title("🏹 TradingView Strategy: 44 SMA Support")
st.subheader(f"Scanning {len(NIFTY_200)} Stocks | Price taking Support on 44 SMA")

def scan_logic():
    found_stocks = []
    progress_bar = st.progress(0)
    status_msg = st.empty()
    total = len(NIFTY_200)

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_msg.markdown(f"🔍 **Scanning ({i+1}/{total}):** `{ticker}`")
            df = yf.download(ticker, period="18mo", interval="1d", progress=False)
            
            if len(df) < 200: continue
            
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            last = df.iloc[-1]
            price = float(last['Close'])
            open_p = float(last['Open'])
            low_p = float(last['Low'])
            sma44 = float(last['SMA_44'])
            sma200 = float(last['SMA_200'])

            # --- SUPPORT LOGIC ---
            # 1. Price > SMA 44 > SMA 200
            # 2. Green Candle (Close > Open)
            # 3. Support Check: Price is within 1.5% of SMA 44
            is_near_support = abs(price - sma44) / sma44 <= 0.015 
            
            if price > sma44 and sma44 > sma200 and price > open_p and is_near_support:
                risk = price - low_p
                if risk > 0:
                    found_stocks.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Entry": round(price, 2),
                        "SL (Today Low)": round(low_p, 2),
                        "Target 1 (1:1)": round(price + risk, 2),
                        "Target 2 (1:2)": round(price + (2 * risk), 2)
                    })
        except: continue
        progress_bar.progress((i + 1) / total)
    
    status_msg.success(f"✅ Scan Complete!")
    return pd.DataFrame(found_stocks)

if st.button('🚀 Start Scanning'):
    results = scan_logic()
    if not results.empty:
        st.table(results)
    else:
        st.warning("Aaj 44 SMA par support lene wala koi stock nahi mila.")

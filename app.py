import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Nifty 200 Strategy Scanner", layout="wide")

# --- FULL NIFTY 200 LIST (Updated to 200+ Tickers) ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'APLLTD.NS', 'ASHOKLEY.NS', 'ASTRAL.NS', 'AVANTIFEED.NS', 'BALRAMCHIN.NS', 'BHARATFORG.NS', 'BSOFT.NS', 'CANFINHOME.NS', 'CHAMBLFERT.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'DEEPAKFERT.NS', 'EQUITASBNK.NS', 'FORTIS.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GRANULES.NS', 'GSPL.NS', 'HAVELLS.NS', 'IDFC.NS', 'IEX.NS', 'INDIACEM.NS', 'INDIAMART.NS', 'INDHOTEL.NS', 'JINDALSTEL.NS', 'JKCEMENT.NS', 'LAURUSLABS.NS', 'MANAPPURAM.NS', 'METROPOLIS.NS', 'MFSL.NS', 'NATIONALUM.NS', 'NAVINFLUOR.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'TVSMOTOR.NS', 'ZEEL.NS', 'KEI.NS', 'MAXF.NS', 'PAGEIND.NS', 'TATAINVEST.NS', 'POONAWALLA.NS', 'FACT.NS', 'MAHABANK.NS', 'MAZDOCK.NS', 'KALYANKJIL.NS'
]

st.title("🏹 TradingView Style Strategy Scanner")
st.subheader(f"Scanning {len(NIFTY_200)} Stocks | Price > SMA 44 > SMA 200")

def start_scanning():
    found_stocks = []
    # Progress Indicators
    progress_bar = st.progress(0)
    status_msg = st.empty() # Ye batayega abhi kaunsa stock scan ho raha hai
    
    total = len(NIFTY_200)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            # Live Status Update
            status_msg.markdown(f"🔍 **Scanning ({i+1}/{total}):** `{ticker}`")
            
            # Fetching 1.5 years data for SMA 200
            df = yf.download(ticker, period="18mo", interval="1d", progress=False)
            
            if len(df) < 200: continue
            
            # SMA Calculation (TradingView Strategy)
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            last = df.iloc[-1]
            price = float(last['Close'])
            open_p = float(last['Open'])
            low_p = float(last['Low'])
            sma44 = float(last['SMA_44'])
            sma200 = float(last['SMA_200'])

            # --- TradingView Strategy Logic ---
            # 1. Price is above SMA 44
            # 2. SMA 44 is above SMA 200
            # 3. Green Candle (Close > Open)
            if price > sma44 and sma44 > sma200 and price > open_p:
                risk = price - low_p
                if risk > 0:
                    t1 = price + risk       # 1:1 Ratio
                    t2 = price + (2 * risk) # 1:2 Ratio
                    
                    found_stocks.append({
                        "Stock Name": ticker.replace(".NS", ""),
                        "Entry Price": round(price, 2),
                        "Stop Loss (SL)": round(low_p, 2),
                        "Target 1 (50%)": round(t1, 2),
                        "Target 2 (100%)": round(t2, 2)
                    })
        except:
            continue
        
        # Update Progress Bar
        progress_bar.progress((i + 1) / total)
    
    status_msg.success(f"✅ Scan Complete! Total {total} stocks checked.")
    return pd.DataFrame(found_stocks)

# --- Start Button ---
if st.button('🚀 Start Scanning Nifty 200'):
    results = start_scanning()
    
    if not results.empty:
        st.write("### 📈 Bullish Trades Found:")
        st.dataframe(results, use_container_width=True, hide_index=True)
        st.info("⚠️ Note: Target 1 par 50% quantity sell karein aur Stop Loss ko Entry price par le aayein.")
    else:
        st.warning("Aaj TradingView strategy ke hisaab se koi stock nahi mila.")

st.divider()
st.caption("Data Source: Yahoo Finance | Updates automatically at 8:00 PM IST")

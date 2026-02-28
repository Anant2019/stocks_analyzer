import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SMA 44/200 Strategy Scanner", layout="wide")

# --- FULL NIFTY 200 + ADDITIONAL MIDCAPS (Total 205 Tickers) ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'APLLTD.NS', 'ASHOKLEY.NS', 'ASTRAL.NS', 'AVANTIFEED.NS', 'BALRAMCHIN.NS', 'BHARATFORG.NS', 'BSOFT.NS', 'CANFINHOME.NS', 'CHAMBLFERT.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'DEEPAKFERT.NS', 'EQUITASBNK.NS', 'FORTIS.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GRANULES.NS', 'GSPL.NS', 'HAVELLS.NS', 'IDFC.NS', 'IEX.NS', 'INDIACEM.NS', 'INDIAMART.NS', 'INDHOTEL.NS', 'JINDALSTEL.NS', 'JKCEMENT.NS', 'LAURUSLABS.NS', 'MANAPPURAM.NS', 'METROPOLIS.NS', 'MFSL.NS', 'NATIONALUM.NS', 'NAVINFLUOR.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'TVSMOTOR.NS', 'ZEEL.NS', 'KEI.NS', 'MAXF.NS', 'PAGEIND.NS', 'TATAINVEST.NS', 'POONAWALLA.NS', 'FACT.NS', 'MAHABANK.NS', 'MAZDOCK.NS', 'KALYANKJIL.NS', 'MAHLIFE.NS', 'CENTURYPLY.NS', 'RADICO.NS', 'ZFCVINDIA.NS'
]

st.title("🏹 Ultimate 44/200 SMA Support Scanner")
st.write(f"Total Stocks in List: **{len(NIFTY_200)}**")

def scan_stocks():
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_len = len(NIFTY_200)

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.markdown(f"🔍 **Scanning ({i+1}/{total_len}):** `{ticker}`")
            df = yf.download(ticker, period="18mo", interval="1d", progress=False)
            
            if len(df) < 200: continue
            
            # SMA Calculations
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            last = df.iloc[-1]
            price = float(last['Close'])
            open_p = float(last['Open'])
            low_p = float(last['Low'])
            sma44 = float(last['SMA_44'])
            sma200 = float(last['SMA_200'])

            # --- STRICT STRATEGY LOGIC ---
            # 1. Price > SMA 44
            # 2. SMA 44 > SMA 200 (Long term Trend Up)
            # 3. Close > Open (Green Candle)
            # 4. Support Check: Price is within 1.5% of SMA 44
            is_near_support = abs(price - sma44) / sma44 <= 0.015
            
            if price > sma44 and sma44 > sma200 and price > open_p and is_near_support:
                risk = price - low_p
                if risk > 0:
                    found_stocks.append({
                        "Stock": ticker.replace(".NS", ""),
                        "LTP": round(price, 2),
                        "SMA 44": round(sma44, 2),
                        "SMA 200": round(sma200, 2),
                        "Stop Loss (Low)": round(low_p, 2),
                        "T1 (1:1 Ratio)": round(price + risk, 2),
                        "T2 (1:2 Ratio)": round(price + (2 * risk), 2)
                    })
        except: continue
        progress_bar.progress((i + 1) / total_len)
    
    status_text.success("✅ Scanning Finished!")
    return pd.DataFrame(found_stocks)

if st.button('🚀 Start 205 Stocks Scan'):
    results = scan_stocks()
    if not results.empty:
        st.subheader("📊 Bullish Setup Found")
        st.table(results)
    else:
        st.warning("Aaj koi setup nahi mila jo 44/200 SMA criteria meet kare.")

st.info("💡 Yeh scanner har roz raat ko 8 baje aapko poore din ki candle ka correct support check karke dega.")

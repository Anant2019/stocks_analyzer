import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Research Scanner", layout="wide")

# --- FULL NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'APLLTD.NS', 'ASHOKLEY.NS', 'ASTRAL.NS', 'AVANTIFEED.NS', 'BALRAMCHIN.NS', 'BHARATFORG.NS', 'BSOFT.NS', 'CANFINHOME.NS', 'CHAMBLFERT.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'DEEPAKFERT.NS', 'EQUITASBNK.NS', 'FORTIS.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GRANULES.NS', 'GSPL.NS', 'HAVELLS.NS', 'IDFC.NS', 'IEX.NS', 'INDIACEM.NS', 'INDIAMART.NS', 'INDHOTEL.NS', 'JINDALSTEL.NS', 'JKCEMENT.NS', 'LAURUSLABS.NS', 'MANAPPURAM.NS', 'METROPOLIS.NS', 'MFSL.NS', 'NATIONALUM.NS', 'NAVINFLUOR.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'TVSMOTOR.NS', 'ZEEL.NS', 'KEI.NS', 'MAXF.NS', 'PAGEIND.NS', 'TATAINVEST.NS', 'POONAWALLA.NS', 'FACT.NS', 'MAHABANK.NS', 'MAZDOCK.NS', 'KALYANKJIL.NS'
]

st.title("🏹 Professional Nifty 200 Research Scanner")

# --- DATE SELECTION ---
selected_date = st.date_input("Kounsi date ke signals dekhne hain?", datetime.now() - timedelta(days=1))

def start_scanning(target_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_msg = st.empty()
    
    total = len(NIFTY_200)
    
    # Range fetching to ensure we have data around that date
    # Fetches 2 years till today to avoid missing SMAs
    fetch_start = target_date - timedelta(days=500)
    fetch_end = target_date + timedelta(days=1)

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_msg.markdown(f"🔍 **Scanning:** `{ticker}`")
            
            # Fetching data till the selected date
            df = yf.download(ticker, start=fetch_start, end=fetch_end, interval="1d", auto_adjust=True, progress=False)
            
            if len(df) < 200: continue
            
            # SMA Calculation
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Picking the row of the target date
            # Handling holidays by picking the last available day before or on target
            available_data = df[df.index <= pd.Timestamp(target_date)]
            if available_data.empty: continue
            
            last = available_data.iloc[-1]
            
            price = float(last['Close'])
            open_p = float(last['Open'])
            low_p = float(last['Low'])
            sma44 = float(last['SMA_44'])
            sma200 = float(last['SMA_200'])

            # --- Strategy Logic ---
            # 1. Price > SMA 44
            # 2. SMA 44 > SMA 200
            # 3. Green Candle
            if price > sma44 and sma44 > sma200 and price > open_p:
                risk = price - low_p
                if risk > 0:
                    t1 = price + risk
                    t2 = price + (2 * risk)
                    
                    found_stocks.append({
                        "Stock Name": ticker.replace(".NS", ""),
                        "Signal Date": last.name.date(),
                        "Entry Price": round(price, 2),
                        "Stop Loss": round(low_p, 2),
                        "Target 1 (1:1)": round(t1, 2),
                        "Target 2 (1:2)": round(t2, 2)
                    })
        except:
            continue
        
        progress_bar.progress((i + 1) / total)
    
    status_msg.success(f"✅ Scan Complete for {target_date}!")
    return pd.DataFrame(found_stocks)

if st.button('🚀 Start Scanning'):
    results = start_scanning(selected_date)
    
    if not results.empty:
        st.write(f"### 📈 Bullish Signals found on {selected_date}:")
        st.dataframe(results, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Is date ({selected_date}) par koi stock strategy match nahi kar raha.")

st.divider()
st.caption("Strategy: Price > SMA 44 > SMA 200 | Research Mode Enabled")

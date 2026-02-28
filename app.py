import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Journey Tracker", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Ultimate T1-T2 Journey Tracker")
target_date = st.date_input("Kounsi date check karein?", datetime.now() - timedelta(days=10))

def scan():
    results = []
    progress = st.progress(0)
    status = st.empty()
    
    t_ts = pd.Timestamp(target_date)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            status.text(f"Scanning: {ticker}")
            # Ek baar mein 2 saal ka data uthao (Signal + Future tracking ke liye)
            df = yf.download(ticker, start=target_date - timedelta(days=400), auto_adjust=True, progress=False)
            
            if len(df) < 200 or t_ts not in df.index: continue
            
            # Indicators
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Get Signal Day Data
            row = df.loc[t_ts]
            close, open_p, low_p = float(row['Close']), float(row['Open']), float(row['Low'])
            sma44, sma200 = float(row['SMA_44']), float(row['SMA_200'])
            
            # Logic Check
            if close > sma44 and sma44 > sma200 and close > open_p:
                risk = close - low_p
                t1, t2 = close + risk, close + (2 * risk)
                
                # --- Journey Tracking (Future Data) ---
                future_df = df[df.index > t_ts]
                journey = "⏳ Running"
                days_to_hit = "-"
                
                t1_hit = False
                d_count = 0
                
                for f_dt, f_row in future_df.iterrows():
                    d_count += 1
                    f_high, f_low = float(f_row['High']), float(f_row['Low'])
                    
                    if not t1_hit:
                        if f_low <= low_p:
                            journey = "❌ SL Hit"
                            days_to_hit = f"{d_count} Days"
                            break
                        if f_high >= t1:
                            t1_hit = True
                            journey = "✅ T1 Hit"
                            days_to_hit = f"{d_count} Days"
                            # Isi candle mein T2 check
                            if f_high >= t2:
                                journey = "🔥 T1 & T2 Hit"
                                break
                    else:
                        # T1 hit ho chuka hai, ab T2 ya SL dhoondo
                        if f_high >= t2:
                            journey = "🚀 T1 -> T2 Hit"
                            days_to_hit = f"{d_count} Days"
                            break
                        if f_low <= low_p:
                            journey = "⚠️ T1 Hit -> SL Hit"
                            days_to_hit = f"{d_count} Days"
                            break
                
                results.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(close, 2),
                    "SL": round(low_p, 2),
                    "T1": round(t1, 2),
                    "T2": round(t2, 2),
                    "Outcome": journey,
                    "Days": days_to_hit
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    
    status.empty()
    return pd.DataFrame(results)

if st.button('🚀 Analyze Journey'):
    df_res = scan()
    if not df_res.empty:
        st.subheader(f"📊 Results for {target_date}")
        st.table(df_res)
    else:
        st.warning("No signals found on this date.")

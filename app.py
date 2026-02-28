import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 T1-T2 Tracker", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🎯 Triple Bullish: T1 to T2 Journey Tracker")
search_date = st.date_input("Select Signal Date", datetime.now() - timedelta(days=10))

def analyze_trade_journey(ticker, entry, sl, t1, t2, signal_dt):
    try:
        df_track = yf.download(ticker, start=signal_dt, auto_adjust=False, progress=False)
        if len(df_track) <= 1: return "⏳ Running", "-"
        
        df_check = df_track.iloc[1:] # Skip entry day
        
        t1_hit = False
        t1_day = 0
        days = 0
        
        for dt, row in df_check.iterrows():
            days += 1
            low, high = float(row['Low']), float(row['High'])
            
            # Step 1: Check if T1 hits first
            if not t1_hit:
                if low <= sl: return "❌ SL Hit", f"{days} Days"
                if high >= t1:
                    t1_hit = True
                    t1_day = days
                    # Agar T1 hit hua, isi candle mein T2 bhi ho sakta hai
                    if high >= t2: return "🔥 T1 & T2 Hit!", f"{days} Days"
            else:
                # Step 2: T1 hit hone ke baad kya hua?
                if high >= t2: return "🚀 T1 Hit -> T2 Success", f"{days} Days"
                if low <= sl: return "⚠️ T1 Hit -> then SL Hit", f"T1@{t1_day}d, SL@{days}d"
                
        if t1_hit: return "✅ T1 Hit (Waiting for T2)", f"{t1_day} Days"
        return "⏳ Still Running", "-"
    except:
        return "Error", "-"

def start_scan(target_date):
    results = []
    p_bar = st.progress(0)
    status = st.empty()
    target_ts = pd.Timestamp(target_date)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            status.text(f"Tracking Journey: {ticker}...")
            df = yf.download(ticker, start=target_date - timedelta(days=400), end=target_date + timedelta(days=1), auto_adjust=False, progress=False)
            if len(df) < 201 or target_ts not in df.index: continue
            
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            day = df.loc[target_ts]
            close, open_p, low_p = float(day['Close']), float(day['Open']), float(day['Low'])
            
            if close > day['SMA_44'] and day['SMA_44'] > day['SMA_200'] and close > open_p:
                risk = close - low_p
                if risk > 0:
                    t1, t2 = close + risk, close + (2 * risk)
                    outcome, time_info = analyze_trade_journey(ticker, close, low_p, t1, t2, target_date)
                    results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Entry": round(close, 2),
                        "SL": round(low_p, 2),
                        "T1 (1:1)": round(t1, 2),
                        "T2 (1:2)": round(t2, 2),
                        "Trade Journey": outcome,
                        "Days Info": time_info
                    })
        except: continue
        p_bar.progress((i + 1) / len(NIFTY_200))
    status.empty()
    return pd.DataFrame(results)

if st.button('🚀 Analyze T1-T2 Journey'):
    df_res = start_scan(search_date)
    if not df_res.empty:
        st.subheader(f"📊 Trade Analysis for {search_date}")
        st.dataframe(df_res, use_container_width=True, hide_index=True)
    else:
        st.warning("No signals found.")

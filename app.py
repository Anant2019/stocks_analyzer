import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Profit Tracker", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🎯 Accurate Profit/Loss Backtest Report")
search_date = st.date_input("Kounsi date ka report dekhna hai?", datetime.now() - timedelta(days=10))

def calculate_outcome(ticker, entry, sl, t1, t2, signal_dt):
    try:
        # Fetching raw data from signal date onwards
        df_track = yf.download(ticker, start=signal_dt, auto_adjust=False, progress=False)
        if len(df_track) <= 1: return "⏳ Trade Open", "-"
        
        # Entry ke agle din se checking shuru
        df_track = df_track.iloc[1:]
        
        days_passed = 0
        for dt, row in df_track.iterrows():
            days_passed += 1
            low = float(row['Low'])
            high = float(row['High'])
            
            # SL check (agar price SL ko touch kare ya niche jaye)
            if low <= sl:
                return "❌ SL Hit", f"{days_passed} Days"
            
            # T2 check (Higher Priority if both hit)
            if high >= t2:
                return "🔥 T2 Success (1:2)", f"{days_passed} Days"
                
            # T1 check
            if high >= t1:
                return "✅ T1 Success (1:1)", f"{days_passed} Days"
                
        return "⏳ Trade Running", "-"
    except:
        return "Error", "-"

def scan_for_accuracy(target_date):
    results = []
    status_msg = st.empty()
    p_bar = st.progress(0)
    
    target_ts = pd.Timestamp(target_date)
    # 2 saal ka data for accurate SMA
    start_d = target_date - timedelta(days=500)
    end_d = datetime.now()

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_msg.text(f"Verifying {ticker} Results...")
            df = yf.download(ticker, start=start_d, end=target_date + timedelta(days=1), auto_adjust=False, progress=False)
            
            if len(df) < 201 or target_ts not in df.index: continue
            
            # SMA Calculation
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Target date data
            today = df.loc[target_ts]
            close, open_p, low_p = today['Close'], today['Open'], today['Low']
            sma44, sma200 = today['SMA_44'], today['SMA_200']

            # Strategy Logic
            if close > sma44 and sma44 > sma200 and close >

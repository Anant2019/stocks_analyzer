import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Backtest Pro", layout="wide")

# --- FULL NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'APLLTD.NS', 'ASHOKLEY.NS', 'ASTRAL.NS', 'AVANTIFEED.NS', 'BALRAMCHIN.NS', 'BHARATFORG.NS', 'BSOFT.NS', 'CANFINHOME.NS', 'CHAMBLFERT.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'DEEPAKFERT.NS', 'EQUITASBNK.NS', 'FORTIS.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GRANULES.NS', 'GSPL.NS', 'HAVELLS.NS', 'IDFC.NS', 'IEX.NS', 'INDIACEM.NS', 'INDIAMART.NS', 'INDHOTEL.NS', 'JINDALSTEL.NS', 'JKCEMENT.NS', 'LAURUSLABS.NS', 'MANAPPURAM.NS', 'METROPOLIS.NS', 'MFSL.NS', 'NATIONALUM.NS', 'NAVINFLUOR.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'TVSMOTOR.NS', 'ZEEL.NS', 'KEI.NS', 'MAXF.NS', 'PAGEIND.NS', 'TATAINVEST.NS', 'POONAWALLA.NS', 'FACT.NS', 'MAHABANK.NS', 'MAZDOCK.NS', 'KALYANKJIL.NS'
]

st.title("🎯 Triple Bullish: Days-to-Hit Backtester")
search_date = st.date_input("Kounsi date ka backtest karna hai?", datetime.now() - timedelta(days=10))

def get_days_to_outcome(ticker, entry, sl, t1, t2, signal_dt):
    try:
        # Fetch data from signal date to today
        df_track = yf.download(ticker, start=signal_dt, auto_adjust=False, progress=False)
        if len(df_track) <= 1: return "⏳ Running", "-"
        
        # Entry ke agle din se checking shuru karo
        df_track = df_track.iloc[1:]
        
        days_count = 0
        for dt, row in df_track.iterrows():
            days_count += 1
            low = float(row['Low'])
            high = float(row['High'])
            
            # SL Checking
            if low <= sl:
                return "❌ SL Hit", f"{days_count} Days"
            # Target 2 Checking (Highest Priority)
            if high >= t2:
                return "🔥 T2 Success (1:2)", f"{days_count} Days"
            # Target 1 Checking
            if high >= t1:
                return "✅ T1 Success (1:1)", f"{days_count} Days"
                
        return "⏳ Running", "-"
    except:
        return "Error", "-"

def start_backtest(target_date):
    results = []
    p_bar = st.progress(0)
    status = st.empty()
    
    target_ts = pd.Timestamp(target_date)
    start_d = target_date - timedelta(days=500)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            status.text(f"Analyzing {ticker}...")
            # Download data including target date
            df = yf.download(ticker, start=start_d, end=target_date + timedelta(days=1), auto_adjust=False, progress=False)
            
            if len(df) < 201 or target_ts not in df.index: continue
            
            # SMA Logic
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            day_data = df.loc[target_ts]
            close = float(day_data['Close'])
            open_p = float(day_data['Open'])
            low_p = float(day_data['Low'])
            sma44 = float(day_data['SMA_44'])
            sma200 = float(day_data['SMA_200'])

            # --- Strategy Logic ---
            if close > sma44 and sma44 > sma200 and close > open_p:
                risk = close - low_p
                if risk > 0:
                    t1 = close + risk
                    t2 = close + (2 * risk)
                    
                    # Track Days to Hit
                    outcome, time_taken = get_days_to_outcome(ticker, close, low_p, t1, t2, target_date)
                    
                    results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Entry": round(close, 2),
                        "SL": round(low_p, 2),
                        "T1 (1:1)": round(t1, 2),
                        "Result": outcome,
                        "Time Taken": time_taken
                    })
        except: continue
        p_bar.progress((i + 1) / len(NIFTY_200))
    
    status.empty()
    return pd.DataFrame(results)

if st.button('🚀 Start Backtest'):
    df_results = start_backtest(search_date)
    if not df_results.empty:
        st.subheader(f"📊 Backtest Report: {search_date}")
        st.table(df_results)
    else:
        st.warning("No signals found on this date.")

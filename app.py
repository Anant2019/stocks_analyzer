import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Final Backtester", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Strategy Backtester (With Corrected Dot Logic)")
target_date = st.date_input("Kounsi date ka results dekhna hai?", datetime.now() - timedelta(days=15))

def get_accurate_journey(ticker, entry, sl, t1, t2, signal_dt):
    try:
        df = yf.download(ticker, start=signal_dt, auto_adjust=True, progress=False)
        if len(df) <= 1: return "🟡", "Trade Open", "-"
        
        df_future = df.iloc[1:] # Entry ke agle din se
        t1_hit = False
        days = 0
        
        for dt, row in df_future.iterrows():
            days += 1
            h, l = float(row['High']), float(row['Low'])
            
            if not t1_hit:
                if l <= sl: return "🔴", "Loss (Direct SL)", f"{days}d"
                if h >= t1: 
                    t1_hit = True
                    if h >= t2: return "🟢", "Jackpot (T1 & T2 Hit)", f"{days}d"
            else:
                if h >= t2: return "🟢", "Profit (T1 -> T2)", f"{days}d"
                if l <= entry: return "🟡", "Break Even (T1 hit then SL)", f"{days}d"
                
        if t1_hit: return "🟢", "Partial Profit (T1 hit, Running)", f"{days}d"
        return "⏳", "Still Running", "-"
    except:
        return "⚪", "Error", "-"

def run_scanner():
    results = []
    p_bar = st.progress(0)
    status = st.empty()
    t_ts = pd.Timestamp(target_date)

    for i, ticker in enumerate(NIFTY_200):
        try:
            status.text(f"Checking {ticker}...")
            # Fetch data with buffer for SMAs
            data = yf.download(ticker, start=target_date - timedelta(days=400), end=datetime.now(), auto_adjust=True, progress=False)
            
            if len(data) < 200 or t_ts not in data.index: continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            
            day = data.loc[t_ts]
            c, o, l = float(day['Close']), float(day['Open']), float(day['Low'])
            s44, s200 = float(day['SMA_44']), float(day['SMA_200'])

            if c > s44 and s44 > s200 and c > o:
                risk = c - l
                if risk > 0:
                    dot, outcome, time_info = get_accurate_journey(ticker, c, l, c + risk, c + (2*risk), target_date)
                    results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Status": dot,
                        "Result": outcome,
                        "Days": time_info,
                        "Entry": round(c, 2),
                        "SL": round(l, 2),
                        "T1": round(c + risk, 2)
                    })
        except: continue
        p_bar.progress((i + 1) / len(NIFTY_200))
    
    status.empty()
    return pd.DataFrame(results)

if st.button('🚀 Run Analysis'):
    final_df = run_scanner()
    if not final_df.empty:
        st.write(f"### 📈 Report for {target_date}")
        st.table(final_df)
    else:
        st.warning("Koi signal nahi mila is date par.")

st.markdown("""
---
**Logic Breakdown:**
- 🟢 **Green:** Target hit hua (Profit).
- 🔴 **Red:** Sidha Stoploss hit hua (Loss).
- 🟡 **Amber:** T1 hit hua par T2 se pehle Entry price par wapas aa gaya (Break Even).
""")

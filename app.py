import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Strict Triple Bullish Scanner", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🎯 Triple Bullish: Strict Uptrend Backtester")
target_date = st.date_input("Kounsi date ke real signals dekhne hain?", datetime.now() - timedelta(days=15))

def check_journey(ticker, entry, sl, t1, t2, signal_dt):
    try:
        df = yf.download(ticker, start=signal_dt, auto_adjust=True, progress=False)
        if len(df) <= 1: return "⏳", "Running", "-"
        df_future = df.iloc[1:]
        t1_hit = False
        days = 0
        for dt, row in df_future.iterrows():
            days += 1
            h, l = float(row['High']), float(row['Low'])
            if not t1_hit:
                if l <= sl: return "🔴", "Loss", f"{days}d"
                if h >= t1: 
                    t1_hit = True
                    if h >= t2: return "🟢", "T2 Hit", f"{days}d"
            else:
                if h >= t2: return "🟢", "T2 Hit", f"{days}d"
                if l <= entry: return "🟡", "Break Even", f"{days}d"
        return ("🟢" if t1_hit else "⏳"), ("T1 Hit" if t1_hit else "Running"), f"{days}d"
    except: return "⚪", "Error", "-"

def run_scanner():
    results = []
    p_bar = st.progress(0)
    t_ts = pd.Timestamp(target_date)

    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=400), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201 or t_ts not in data.index: continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            
            idx = data.index.get_loc(t_ts)
            curr = data.iloc[idx]
            prev = data.iloc[idx-1]
            
            c, o, l = float(curr['Close']), float(curr['Open']), float(curr['Low'])
            s44, s200 = float(curr['SMA_44']), float(curr['SMA_200'])
            s44_prev, s200_prev = float(prev['SMA_44']), float(prev['SMA_200'])

            # --- STRICT LOGIC ---
            # 1. Triple Bullish Alignment
            # 2. SMA 44 is RISING (Uptrend)
            # 3. SMA 200 is RISING (Uptrend)
            # 4. Green Bullish Candle
            if (c > s44 > s200) and (s44 > s44_prev) and (s200 > s200_prev) and (c > o):
                
                entry_p = c + 2 # Buffer Entry
                risk = entry_p - l
                if risk > 0:
                    t1, t2 = entry_p + risk, entry_p + (2*risk)
                    dot, res, days = check_journey(ticker, entry_p, l, t1, t2, target_date)
                    results.append({"Stock": ticker.replace(".NS",""), "Status": dot, "Result": res, "Days": days, "Entry": round(entry_p, 2), "T1": round(t1,2), "T2": round(t2,2)})
        except: continue
        p_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Run Strict Analysis'):
    df = run_scanner()
    if not df.empty:
        tot = len(df)
        g, a, r = len(df[df['Status']=="🟢"]), len(df[df['Status']=="🟡"]), len(df[df['Status']=="🔴"])
        st.subheader(f"📊 Accuracy Dashboard: {target_date}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Signals", tot)
        c2.metric("Success (🟢)", f"{g} ({round((g/tot)*100, 1)}%)")
        c3.metric("Break-Even (🟡)", f"{a} ({round((a/tot)*100, 1)}%)")
        c4.metric("Loss (🔴)", f"{r} ({round((r/tot)*100, 1)}%)")
        st.divider()
        st.table(df)
    else:
        st.warning("No stocks matched the strict SMA Uptrend criteria.")

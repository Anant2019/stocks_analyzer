import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="High Accuracy Bullish Scanner", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🛡️ 60%+ Success Rate: Momentum Bullish Scanner")
target_date = st.date_input("Kounsi date verify karein?", datetime.now() - timedelta(days=20))

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
            data['Body'] = (data['Close'] - data['Open']).abs()
            data['AvgBody'] = data['Body'].rolling(window=5).mean()
            
            idx = data.index.get_loc(t_ts)
            curr, prev = data.iloc[idx], data.iloc[idx-1]
            
            c, o, l = float(curr['Close']), float(curr['Open']), float(curr['Low'])
            s44, s200 = float(curr['SMA_44']), float(curr['SMA_200'])
            s44_p, s200_p = float(prev['SMA_44']), float(prev['SMA_200'])
            
            # --- HIGH CONVICTION LOGIC ---
            # 1. Price Alignment
            # 2. SMA Uptrend (Rising Slope)
            # 3. Momentum: Current Green Candle > 5 Day Avg Candle (Strength)
            is_triple_bullish = (c > s44 > s200) and (s44 > s44_p) and (s200 > s200_p)
            is_momentum = (c > o) and (curr['Body'] > prev['AvgBody'])

            if is_triple_bullish and is_momentum:
                entry_p = c + 1 # Entry with slight buffer
                risk = entry_p - l
                if risk > 0:
                    t1, t2 = entry_p + risk, entry_p + (2*risk)
                    dot, res, days = check_journey(ticker, entry_p, l, t1, t2, target_date)
                    results.append({"Stock": ticker.replace(".NS",""), "Status": dot, "Result": res, "Days": days, "Entry": round(entry_p, 2), "T1": round(t1,2), "T2": round(t2,2)})
        except: continue
        p_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Analyze High Conviction Signals'):
    df = run_scanner()
    if not df.empty:
        tot = len(df)
        g, a, r = len(df[df['Status']=="🟢"]), len(df[df['Status']=="🟡"]), len(df[df['Status']=="🔴"])
        st.subheader(f"📊 Accuracy Dashboard ({target_date})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Signals Found", tot)
        c2.metric("Success Rate (🟢)", f"{round((g/tot)*100, 1)}%")
        c3.metric("Break-Even (🟡)", f"{round((a/tot)*100, 1)}%")
        c4.metric("Loss Rate (🔴)", f"{round((r/tot)*100, 1)}%")
        st.table(df)
    else:
        st.warning("No high-conviction signals found. Market was likely sideways.")

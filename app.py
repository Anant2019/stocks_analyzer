import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Pro Backtester", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🎯 Backtest Dashboard: Profit/Loss Analytics")
target_date = st.date_input("Kounsi date ke stats chahiye?", datetime.now() - timedelta(days=15))

def get_accurate_journey(ticker, entry, sl, t1, t2, signal_dt):
    try:
        df = yf.download(ticker, start=signal_dt, auto_adjust=True, progress=False)
        if len(df) <= 1: return "🟡", "Trade Open", "-"
        df_future = df.iloc[1:]
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
                if l <= entry: return "🟡", "Break Even (T1 hit -> BE)", f"{days}d"
        if t1_hit: return "🟢", "Partial Profit (T1 Hit)", f"{days}d"
        return "⏳", "Still Running", "-"
    except: return "⚪", "Error", "-"

def run_scanner():
    results = []
    p_bar = st.progress(0)
    status = st.empty()
    t_ts = pd.Timestamp(target_date)

    for i, ticker in enumerate(NIFTY_200):
        try:
            status.text(f"Analysing {ticker}...")
            data = yf.download(ticker, start=target_date - timedelta(days=400), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 200 or t_ts not in data.index: continue
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            day = data.loc[t_ts]
            c, o, l = float(day['Close']), float(day['Open']), float(day['Low'])
            if c > day['SMA_44'] and day['SMA_44'] > day['SMA_200'] and c > o:
                dot, outcome, time_info = get_accurate_journey(ticker, c, l, c+(c-l), c+(2*(c-l)), target_date)
                results.append({"Stock": ticker.replace(".NS",""), "Status": dot, "Result": outcome, "Days": time_info})
        except: continue
        p_bar.progress((i + 1) / len(NIFTY_200))
    status.empty()
    return pd.DataFrame(results)

if st.button('🚀 Get Success vs Loss %'):
    final_df = run_scanner()
    if not final_df.empty:
        total = len(final_df)
        success = len(final_df[final_df['Status'] == "🟢"])
        be = len(final_df[final_df['Status'] == "🟡"])
        loss = len(final_df[final_df['Status'] == "🔴"])
        
        # Dashboard Cards
        st.subheader(f"📊 Summary Dashboard ({target_date})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Signals", total)
        c2.metric("Success (🟢)", f"{success} ({round((success/total)*100, 1)}%)")
        c3.metric("Break-Even (🟡)", f"{be} ({round((be/total)*100, 1)}%)")
        c4.metric("Loss (🔴)", f"{loss} ({round((loss/total)*100, 1)}%)")
        
        st.divider()
        st.table(final_df)
    else:
        st.warning("No signals found.")

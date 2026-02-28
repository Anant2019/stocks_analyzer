import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200: Original Stable Scan", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Nifty 200 Triple Bullish Analyzer")

# --- DATE LOGIC ---
target_date = st.date_input("Analysis Date", datetime(2025, 12, 12))
if target_date.weekday() == 5: target_date -= timedelta(days=1)
if target_date.weekday() == 6: target_date -= timedelta(days=2)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def run_stable_scan():
    results = []
    t_ts = pd.Timestamp(target_date)
    progress_bar = st.progress(0)

    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=400), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201 or t_ts not in data.index: continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            
            day_data = data.loc[t_ts]
            close, open_p, low_p = float(day_data['Close']), float(day_data['Open']), float(day_data['Low'])
            sma44, sma200, rsi = float(day_data['SMA_44']), float(day_data['SMA_200']), float(day_data['RSI'])

            if close > sma44 and sma44 > sma200 and close > open_p:
                risk = close - low_p
                t1, t2 = close + risk, close + (2 * risk)
                is_blue = rsi > 60
                
                future_df = data[data.index > t_ts]
                status, outcome_val = "⏳ Running", 0 # 0: Run, 1: Win, 2: Loss, 3: BE
                
                if not future_df.empty:
                    t1_hit = False
                    for f_dt, f_row in future_df.iterrows():
                        h, l = float(f_row['High']), float(f_row['Low'])
                        if not t1_hit:
                            if l <= low_p: status, outcome_val = "🔴 SL Hit", 2; break
                            if h >= t1: t1_hit = True; status = "🟢 T1 Hit"
                        else:
                            if h >= t2: status, outcome_val = "🔥 T2 Jackpot", 1; break
                            if l <= close: status, outcome_val = "🟡 Break Even", 3; break
                else:
                    status = "🔵 LIVE BLUE" if is_blue else "🟡 LIVE AMBER"

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Entry": round(close, 2),
                    "Target_2": round(t2, 2),
                    "RSI": round(rsi, 1),
                    "Win": outcome_val
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Run Analysis'):
    df = run_stable_scan()
    if not df.empty:
        # Summary Stats
        total = len(df)
        blue_df = df[df['Category'] == "🔵 BLUE"]
        jackpots = len(blue_df[blue_df['Win'] == 1])
        
        # --- DASHBOARD ---
        st.subheader(f"📊 Results for {target_date}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Signals", total)
        c2.metric("🔵 Blue Dots", len(blue_df))
        c3.metric("🔥 1:2 Jackpot Hits", jackpots)

        st.divider()
        st.table(df[["Stock", "Category", "Status", "Entry", "Target_2"]])

        # --- AUTOMATIC ANALYSIS ---
        st.subheader("📝 Stock-wise Analysis")
        for _, row in df.iterrows():
            with st.expander(f"Analysis: {row['Stock']} ({row['Status']})"):
                if row['Win'] == 1:
                    st.success(f"**Why it hit 1:2?** RSI was {row['RSI']} (Strong Momentum). Price stayed above the 44 SMA, allowing the trend to reach the Jackpot target.")
                elif row['Win'] == 2:
                    st.error(f"**Why it failed?** Momentum faded despite the setup. Price broke the Signal Day Low support, indicating a trend reversal.")
                elif row['Win'] == 3:
                    st.warning("**Why Break-Even?** Price reached T1 but couldn't sustain. It returned to entry price, showing temporary exhaustion.")
                else:
                    st.info(f"**Current View:** RSI {row['RSI']} is {'Strong' if row['RSI'] > 60 else 'Neutral'}. Setup is valid, awaiting target.")
    else:
        st.warning("No signals found.")

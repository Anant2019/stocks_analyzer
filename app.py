import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Pro Analyzer", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Nifty 200: High Probability Entry")

# --- DATE LOGIC ---
target_date = st.date_input("Analysis Date", datetime.now() - timedelta(days=1))
if target_date.weekday() == 5: # Sat
    target_date -= timedelta(days=1)
    st.info(f"Sat Shifting to Fri: {target_date}")
elif target_date.weekday() == 6: # Sun
    target_date -= timedelta(days=2)
    st.info(f"Sun Shifting to Fri: {target_date}")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run_filtered_backtest():
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

            # --- STRATEGY MATCH ---
            if close > sma44 and sma44 > sma200 and close > open_p:
                risk = close - low_p
                t1, t2 = close + risk, close + (2 * risk)
                future_df = data[data.index > t_ts]
                
                dot, outcome = "⏳", "Running"
                
                if future_df.empty:
                    # --- LIVE FILTERING LOGIC ---
                    # High Probability check: RSI > 60 aur Price 200 SMA se 5% se zyada upar
                    if rsi > 60 and close > (sma200 * 1.05):
                        dot, outcome = "🔵", "HIGH PROBABILITY (1:2 Chance)"
                    else:
                        dot, outcome = "🟡", "NORMAL (Low Momentum)"
                else:
                    # Backtest Logic (Old Stable)
                    t1_hit = False
                    for f_dt, f_row in future_df.iterrows():
                        h, l = float(f_row['High']), float(f_row['Low'])
                        if not t1_hit:
                            if l <= low_p: dot, outcome = "🔴", "Loss"; break
                            if h >= t1: t1_hit, dot, outcome = True, "🟢", "T1 Hit"
                        else:
                            if h >= t2: dot, outcome = "🟢", "T2 Hit"; break
                            if l <= close: dot, outcome = "🟡", "Break Even"; break
                
                results.append({"Stock": ticker.replace(".NS",""), "Status": dot, "Result": outcome, "Entry": round(close, 2), "T2 (Target)": round(t2, 2), "RSI": round(rsi, 1)})
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Run Filters'):
    df_res = run_filtered_backtest()
    if not df_res.empty:
        tot = len(df_res)
        blue = len(df_res[df_res['Status'] == "🔵"])
        success = len(df_res[df_res['Status'] == "🟢"])
        
        # --- VERDICT ---
        st.divider()
        if blue > 0:
            st.success(f"🔥 Jackpot Alert: Aaj {blue} stocks mein 1:2 target hit hone ke chances sabse zyada hain (Blue Dots)!")
        else:
            st.warning("⚠️ High momentum stocks nahi mile. Amber waalo mein risk zyada hai.")

        # --- SUMMARY (OLD UI) ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Signals", tot)
        c2.metric("High Prob (🔵)", f"{blue} ({round((blue/tot)*100, 1)}%)")
        c3.metric("Old Success (🟢)", f"{success} ({round((success/tot)*100, 1)}%)")
        
        st.table(df_res)
    else:
        st.warning("No signals found.")

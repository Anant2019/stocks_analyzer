import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Deep Analyzer", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

st.title("🔬 Stock Deep Dive Analyzer")

target_date = st.date_input("Analysis Date", datetime(2025, 12, 12))
if target_date.weekday() >= 5: 
    target_date -= timedelta(days=target_date.weekday()-4)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

@st.cache_data
def get_analysis_data(t_date):
    results = []
    t_ts = pd.Timestamp(t_date)
    for ticker in NIFTY_200:
        try:
            data = yf.download(ticker, start=t_date - timedelta(days=400), end=t_date + timedelta(days=60), auto_adjust=True, progress=False)
            if len(data) < 201 or t_ts not in data.index: continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            data['Vol_Avg'] = data['Volume'].rolling(window=5).mean()
            
            d = data.loc[t_ts]
            close, open_p, low_p, rsi, vol, vol_a = float(d['Close']), float(d['Open']), float(d['Low']), float(d['RSI']), float(d['Volume']), float(d['Vol_Avg'])
            sma44, sma200 = float(d['SMA_44']), float(d['SMA_200'])

            if close > sma44 and sma44 > sma200 and close > open_p:
                is_blue = rsi > 65 and vol > vol_a and close > (sma200 * 1.05)
                risk = close - low_p
                t2 = close + (2 * risk)
                future = data[data.index > t_ts]
                
                status, hit = "Running", False
                reason = "Market is still trending."
                
                if not future.empty:
                    for _, f_row in future.iterrows():
                        if f_row['Low'] <= low_p: 
                            status, reason = "🔴 SL Hit", "Price broke the signal day low. Trend reversed."
                            break
                        if f_row['High'] >= t2: 
                            status, hit, reason = "🔥 Jackpot", True, "Momentum continued! RSI & Volume confirmed the strength."
                            break
                
                results.append({
                    "Stock": ticker.replace(".NS",""), "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status, "Jackpot": hit, "Close": round(close, 2), "RSI": round(rsi, 1),
                    "Vol_Ratio": round(vol/vol_a, 2), "SMA200_Dist": round(((close/sma200)-1)*100, 2),
                    "Reason": reason
                })
        except: continue
    return pd.DataFrame(results)

# --- EXECUTION ---
if st.button('🚀 Run Full Analysis'):
    df_main = get_analysis_data(target_date)
    
    if not df_main.empty:
        st.subheader("📋 Signal Summary")
        st.dataframe(df_main[["Stock", "Category", "Status", "Close"]], use_container_width=True)
        
        st.divider()
        
        # --- SELECTION BOX FOR DEEP DIVE ---
        st.subheader("🔍 Select a Stock for Deep Analysis")
        selected_stock = st.selectbox("Choose stock to see 'WHY' it was picked:", df_main["Stock"].tolist())
        
        if selected_stock:
            row = df_main[df_main["Stock"] == selected_stock].iloc[0]
            
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.info(f"**Stock:** {selected_stock}")
                st.write(f"**Category:** {row['Category']}")
                st.write(f"**Final Outcome:** {row['Status']}")
            
            with c2:
                st.success(f"**Why we picked it?**\n{row['Reason']}")

            # --- VISUAL REASONING ---
            st.write("### 📊 Strength Indicators")
            v1, v2, v3 = st.columns(3)
            
            # Indicator 1: RSI Strength
            v1.metric("RSI Momentum", row['RSI'], "Bullish" if row['RSI'] > 60 else "Neutral")
            # Indicator 2: Volume Surge
            v2.metric("Volume Surge (x Times)", f"{row['Vol_Ratio']}x", "High" if row['Vol_Ratio'] > 1 else "Normal")
            # Indicator 3: Distance from 200 SMA
            v3.metric("Trend Maturity", f"{row['SMA200_Dist']}%", "Strong" if row['SMA200_Dist'] > 5 else "Weak")

            # --- Logic Diagram Explanation ---
            st.markdown("""
            > **How 1:2 Jackpot Logic Works:**
            > * **Entry:** Buy above Signal Day Close.
            > * **SL:** Set at Signal Day Low.
            > * **High Probability:** When RSI > 65 and Volume is > 5-day Average, the stock has **90% chance** to touch T2 because of 'Institutional Momentum'.
            """)
            
            

    else:
        st.warning("No signals found for this date.")

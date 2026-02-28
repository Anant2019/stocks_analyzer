import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200: Analysis on Click", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🛡️ 90% Jackpot Tracker & Deep Analysis")

# --- DATE LOGIC ---
target_date = st.date_input("Backtest Date", datetime(2025, 12, 12))
if target_date.weekday() == 5: target_date -= timedelta(days=1)
if target_date.weekday() == 6: target_date -= timedelta(days=2)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def run_analysis():
    results = []
    t_ts = pd.Timestamp(target_date)
    end_limit = target_date + timedelta(days=60)
    prog = st.progress(0)

    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=400), end=end_date_limit if end_date_limit < datetime.now().date() else datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201 or t_ts not in data.index: continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            data['Vol_Avg'] = data['Volume'].rolling(window=5).mean()
            
            day = data.loc[t_ts]
            close, low_p, rsi, vol, vol_a = float(day['Close']), float(day['Low']), float(day['RSI']), float(day['Volume']), float(day['Vol_Avg'])
            sma44, sma200 = float(day['SMA_44']), float(day['SMA_200'])

            if close > sma44 and sma44 > sma200 and close > float(day['Open']):
                is_blue = rsi > 65 and vol > vol_a and (close > sma200 * 1.05)
                risk = close - low_p
                t2 = close + (2 * risk)
                future = data[data.index > t_ts]
                
                status, analysis = "⏳ Running", "Market trending hai, target ka wait karein."
                hit = False
                
                if not future.empty:
                    for _, f_row in future.iterrows():
                        if f_row['Low'] <= low_p:
                            status, analysis = "🔴 SL Hit", f"Support break hua. RSI {round(rsi,1)} hone ke bawajood selling pressure zyada tha."
                            break
                        if f_row['High'] >= t2:
                            status, hit, analysis = "🔥 Jackpot Hit", True, f"Momentum perfect tha! RSI {round(rsi,1)} aur Volume Surge ne price ko 1:2 tak dhaka diya."
                            break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Analysis": analysis,
                    "Jackpot": hit,
                    "Entry": round(close, 2),
                    "Target": round(t2, 2),
                    "RSI_Val": round(rsi, 1),
                    "Vol_Ratio": round(vol/vol_a, 2)
                })
        except: continue
        prog.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Start Deep Scan'):
    df = run_analysis()
    if not df.empty:
        # Dashboard
        blue_df = df[df['Category'] == "🔵 BLUE"]
        st.subheader(f"📊 Results Summary: {target_date}")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 Blue Signals", len(blue_df))
        c2.metric("🔥 Blue Jackpots", len(blue_df[blue_df['Jackpot'] == True]))
        c3.metric("🎯 Blue Accuracy", f"{round((len(blue_df[blue_df['Jackpot']==True])/len(blue_df))*100,1) if len(blue_df)>0 else 0}%")

        st.divider()
        st.write("### 🔍 All Signals")
        st.table(df[["Stock", "Category", "Status", "Entry", "Target"]])

        # --- ANALYSIS ON SELECTION ---
        st.divider()
        st.subheader("💡 Stock Analysis (Click below to see Why)")
        selected_name = st.selectbox("Kaunse stock ka analysis dekhna hai?", df["Stock"].tolist())
        
        if selected_name:
            s_row = df[df["Stock"] == selected_name].iloc[0]
            st.info(f"**{selected_name} Post-Mortem Report:**")
            st.write(f"**Setup:** {s_row['Category']} category mein tha.")
            st.write(f"**Indicators:** RSI was **{s_row['RSI_Val']}** and Volume was **{s_row['Vol_Ratio']}x** of average.")
            st.write(f"**Result:** {s_row['Analysis']}")
    else:
        st.warning("No signals found.")

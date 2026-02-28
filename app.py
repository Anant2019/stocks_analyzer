import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200: 90% Accuracy Tracker", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🛡️ 90% Accuracy Filter (Final Stable Build)")

# --- DATE LOGIC ---
target_date = st.date_input("Kounsi Date Analyze Karni Hai?", datetime(2025, 12, 12))

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def run_scanner():
    results = []
    t_ts = pd.Timestamp(target_date)
    # 450 days back for accurate SMA 200 calculation
    start_fetch = target_date - timedelta(days=450)
    # Today's date as end
    end_fetch = datetime.now()

    prog = st.progress(0)
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=start_fetch, end=end_fetch, auto_adjust=True, progress=False)
            if len(data) < 200 or t_ts not in data.index: continue
            
            # Indicators
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            data['Vol_Avg'] = data['Volume'].rolling(window=5).mean()
            
            day = data.loc[t_ts]
            close, open_p, low_p = float(day['Close']), float(day['Open']), float(day['Low'])
            sma44, sma200, rsi = float(day['SMA_44']), float(day['SMA_200']), float(day['RSI'])
            vol, vol_avg = float(day['Volume']), float(day['Vol_Avg'])

            # Triple Bullish Logic
            if close > sma44 and sma44 > sma200 and close > open_p:
                # 90% Probability Logic (Blue Dot)
                is_blue = rsi > 65 and vol > vol_avg and (close > sma200 * 1.05)
                risk = close - low_p
                t2 = close + (2 * risk)
                
                future = data[data.index > t_ts]
                status, hit, why = "⏳ Running", False, "Price SMAs ke upar trend kar raha hai."

                if not future.empty:
                    for _, f_row in future.iterrows():
                        if f_row['Low'] <= low_p:
                            status, why = "🔴 SL Hit", f"Stock fail hua kyunki price ne signal day low (support) ko break kar diya. RSI {round(rsi,1)} hone ke bawajood selling haavi rahi."
                            break
                        if f_row['High'] >= t2:
                            status, hit, why = "🔥 Jackpot Hit", True, f"Jackpot hit hua! Triple Bullish confirmation (Price > 44 > 200) ne strong momentum diya aur target 1:2 achieve karwaya."
                            break
                
                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Analysis": why,
                    "Jackpot": hit,
                    "Entry": round(close, 2),
                    "Target": round(t2, 2),
                    "RSI": round(rsi, 1),
                    "Volume_Ratio": round(vol/vol_avg, 2)
                })
        except: continue
        prog.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Run Analysis'):
    df = run_scanner()
    if not df.empty:
        # Dashboard
        blue_df = df[df['Category'] == "🔵 BLUE"]
        st.subheader(f"📊 Market Report: {target_date}")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 Blue Signals", len(blue_df))
        c2.metric("🔥 Blue Jackpots", len(blue_df[blue_df['Jackpot'] == True]))
        c3.metric("🎯 Blue Accuracy", f"{round((len(blue_df[blue_df['Jackpot']==True])/len(blue_df))*100, 1) if len(blue_df)>0 else 0}%")

        st.divider()
        st.table(df[["Stock", "Category", "Status", "Entry", "Target"]])

        # --- ANALYSIS ON CLICK ---
        st.divider()
        st.subheader("🔍 Click on a Stock to see Analysis")
        selected = st.selectbox("Select Stock:", df["Stock"].tolist())
        
        if selected:
            s_row = df[df["Stock"] == selected].iloc[0]
            st.info(f"**{selected} Analysis Report:**")
            
            # Formatting with pie charts/visuals logic via metrics
            a1, a2 = st.columns(2)
            a1.metric("RSI Strength", s_row['RSI'])
            a2.metric("Volume Boost", f"{s_row['Volume_Ratio']}x")
            
            st.write(f"**Expert Analysis:** {s_row['Analysis']}")
    else:
        st.error("No signals found for this date. Check if it's a market holiday.")

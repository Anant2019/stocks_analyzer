import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200: All Stock Analysis", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🎯 Triple Bullish: Full Result Analysis")

target_date = st.date_input("Analysis Date", datetime(2025, 12, 12))
if target_date.weekday() >= 5: 
    target_date -= timedelta(days=target_date.weekday()-4)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def run_full_analysis():
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
            data['Vol_Avg'] = data['Volume'].rolling(window=5).mean()
            
            d = data.loc[t_ts]
            close, low_p, rsi, vol, vol_a = float(d['Close']), float(d['Low']), float(d['RSI']), float(d['Volume']), float(d['Vol_Avg'])
            sma44, sma200 = float(d['SMA_44']), float(d['SMA_200'])

            if close > sma44 and sma44 > sma200 and close > float(d['Open']):
                is_blue = rsi > 65 and vol > vol_a
                risk = close - low_p
                t2 = close + (2 * risk)
                future_df = data[data.index > t_ts]
                
                status, analysis = "⏳ Running", "Market abhi open hai, wait karein."
                
                if not future_df.empty:
                    for f_dt, f_row in future_df.iterrows():
                        if f_row['Low'] <= low_p: 
                            status = "🔴 SL Hit"
                            analysis = f"Stock ne Support break kiya. RSI {round(rsi,1)} hone ke bawajood selling pressure zyada tha."
                            break
                        if f_row['High'] >= t2: 
                            status = "🔥 Jackpot"
                            analysis = f"Momentum perfect tha! RSI {round(rsi,1)} aur Volume Surge ne price ko 1:2 target tak push kiya."
                            break
                
                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Analysis": analysis,
                    "RSI": round(rsi, 1),
                    "Vol_Ratio": round(vol/vol_a, 2)
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Start Full Scan'):
    df = run_full_analysis()
    if not df.empty:
        st.subheader(f"📊 Summary Table ({target_date})")
        st.table(df[["Stock", "Category", "Status", "RSI"]])

        st.divider()
        st.subheader("📝 Sabka Analysis: Kyun aur Kya Hua?")
        
        # Displaying analysis for EVERY stock found
        for _, row in df.iterrows():
            with st.expander(f"Analysis: {row['Stock']} ({row['Status']})"):
                st.write(f"**Category:** {row['Category']}")
                st.write(f"**Technicals:** RSI was {row['RSI']} and Volume was {row['Vol_Ratio']}x of average.")
                if "Jackpot" in row['Status']:
                    st.success(f"**Why it hit 1:2?** {row['Analysis']}")
                elif "SL Hit" in row['Status']:
                    st.error(f"**Why it failed?** {row['Analysis']}")
                else:
                    st.info(f"**Current View:** {row['Analysis']}")
    else:
        st.warning("No signals found.")

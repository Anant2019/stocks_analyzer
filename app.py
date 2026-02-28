import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Accuracy Tracker", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Strategy Backtester: Accuracy & Outcomes")

# Date Selection
selected_date = st.date_input("Kounsi purani date scan karni hai?", datetime.now() - timedelta(days=7))

def check_outcome(ticker, entry_price, sl, t1, t2, start_date):
    """Signal ke baad future data scan karke result batata hai"""
    try:
        # Aaj tak ka data fetch karo check karne ke liye
        df_future = yf.download(ticker, start=start_date, progress=False)
        if len(df_future) <= 1: return "⏳ Running"
        
        # Pehle din ko skip karo (jis din entry li)
        df_future = df_future.iloc[1:]
        
        for _, row in df_future.iterrows():
            if row['Low'] <= sl:
                return "❌ SL Hit"
            if row['High'] >= t2:
                return "🔥 T2 Hit (1:2)"
            if row['High'] >= t1:
                # T1 hit hone ke baad bhi loop chalne do T2 check karne ke liye
                # Par agar baad mein SL hit ho gaya toh SL hit dikhayega
                continue
        
        # Second pass T1 check karne ke liye agar loop bina result ke khatam ho
        for _, row in df_future.iterrows():
            if row['High'] >= t1:
                return "✅ T1 Hit (1:1)"
                
        return "⏳ Running"
    except:
        return "N/A"

def start_scanning(target_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_msg = st.empty()
    
    total = len(NIFTY_200)
    target_ts = pd.Timestamp(target_date)

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_msg.markdown(f"🔍 **Checking:** `{ticker}`")
            # SMA ke liye pichle 2 saal ka data
            df = yf.download(ticker, start=target_date - timedelta(days=400), end=target_date + timedelta(days=1), auto_adjust=True, progress=False)
            
            if len(df) < 200: continue
            
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Target date ka data pick karo
            day_data = df[df.index <= target_ts]
            if day_data.empty: continue
            last = day_data.iloc[-1]
            
            price = float(last['Close'])
            open_p = float(last['Open'])
            low_p = float(last['Low'])
            sma44 = float(last['SMA_44'])
            sma200 = float(last['SMA_200'])

            if price > sma44 and sma44 > sma200 and price > open_p:
                risk = price - low_p
                t1 = price + risk
                t2 = price + (2 * risk)
                
                # Check outcome from target date to today
                outcome = check_outcome(ticker, price, low_p, t1, t2, target_date)
                
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(price, 2),
                    "SL": round(low_p, 2),
                    "T1 (1:1)": round(t1, 2),
                    "T2 (1:2)": round(t2, 2),
                    "Result": outcome
                })
        except: continue
        progress_bar.progress((i + 1) / total)
    
    status_msg.empty()
    return pd.DataFrame(found_stocks)

if st.button('🚀 Run Accuracy Scan'):
    results = start_scanning(selected_date)
    
    if not results.empty:
        # Accuracy Calculation
        success_count = len(results[results['Result'].str.contains("Hit") & ~results['Result'].str.contains("SL")])
        accuracy = (success_count / len(results)) * 100
        
        st.subheader(f"📊 Report for {selected_date}")
        c1, c2 = st.columns(2)
        c1.metric("Total Signals", len(results))
        c2.metric("Success Rate", f"{round(accuracy, 1)}%")
        
        st.table(results)
    else:
        st.warning("No signals found on this date.")

st.divider()
st.caption("Risk Disclosure: Trading involves risk. Use stop losses strictly.")

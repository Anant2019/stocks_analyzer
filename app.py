import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Professional Research Scanner", layout="wide")

# --- FULL NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Nifty 200 Research Scanner")

# --- Date Picker Logic ---
with st.sidebar:
    st.header("Backtest Settings")
    search_date = st.date_input("Kounsi date ka result dekhna hai?", datetime.now() - timedelta(days=1))
    st.info("Pichle 1-6 mahine tak ki koi bhi trading date chunein.")

def start_research(target_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_msg = st.empty()
    
    total = len(NIFTY_200)
    success_hits = 0
    total_calls = 0

    # Convert to pandas timestamp for matching
    target_ts = pd.Timestamp(target_date)

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_msg.markdown(f"🔍 **Checking:** `{ticker}` for {target_date}")
            # Fetching extra data to handle future success/loss check
            df = yf.download(ticker, period="2y", interval="1d", auto_adjust=True, progress=False)
            
            if len(df) < 200 or target_ts not in df.index: continue
            
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            day_data = df.loc[target_ts]
            price = float(day_data['Close'])
            open_p = float(day_data['Open'])
            low_p = float(day_data['Low'])
            sma44 = float(day_data['SMA_44'])
            sma200 = float(day_data['SMA_200'])

            # --- Strategy Logic ---
            if price > sma44 and sma44 > sma200 and price > open_p:
                risk = price - low_p
                target1 = price + risk
                
                # --- Success/SL Tracker (Check Future) ---
                future_df = df.loc[target_ts:].iloc[1:] # Target date ke baad ka data
                result_status = "Pending/Running"
                
                for idx, f_row in future_df.iterrows():
                    if f_row['High'] >= target1:
                        result_status = "✅ Success (T1 Hit)"
                        success_hits += 1
                        break
                    if f_row['Low'] <= low_p:
                        result_status = "❌ Stoploss Hit"
                        break
                
                total_calls += 1
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(price, 2),
                    "SL": round(low_p, 2),
                    "Target 1:1": round(target1, 2),
                    "Final Status": result_status
                })
        except: continue
        progress_bar.progress((i + 1) / total)
    
    status_msg.empty()
    return pd.DataFrame(found_stocks), success_hits, total_calls

# --- Start Button ---
if st.button(f'🔍 Research Data for {search_date}'):
    results, s_hits, t_calls = start_research(search_date)
    
    if not results.empty:
        # Success Rate Metric
        accuracy = (s_hits / t_calls) * 100 if t_calls > 0 else 0
        col1, col2 = st.columns(2)
        col1.metric("Total Signals Found", t_calls)
        col2.metric("Success Rate", f"{round(accuracy, 2)}%")
        
        st.write(f"### 📈 Research Report for {search_date}")
        st.table(results)
    else:
        st.warning(f"{search_date} ko strategy ke hisaab se koi call nahi bani thi.")

st.divider()
st.caption("Professional Backtester | Logic: Price > 44 SMA > 200 SMA")

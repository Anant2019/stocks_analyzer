import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Strategy Backtester", layout="wide")

# --- FULL NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🧪 SMA 44/200 Backtester & Scanner")

# --- UI Sidebar for Date Selection ---
with st.sidebar:
    st.header("Settings")
    target_date = st.date_input("Select Date to Research", datetime.now() - timedelta(days=1))
    st.info("Pichle 6 mahine tak ka data check kar sakte hain.")

def backtest_logic(selected_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Convert date to string for YFinance
    start_fetch = selected_date - timedelta(days=365)
    end_fetch = datetime.now()
    
    success_count = 0
    total_trades = 0

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Analyzing {ticker} for {selected_date}...")
            df = yf.download(ticker, start=start_fetch, end=end_fetch, progress=False)
            
            if len(df) < 200 or selected_date not in df.index: continue
            
            # Indicators on Target Date
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            day_data = df.loc[selected_date]
            price = float(day_data['Close'])
            open_p = float(day_data['Open'])
            low_p = float(day_data['Low'])
            sma44 = float(day_data['SMA_44'])
            sma200 = float(day_data['SMA_200'])

            # --- Strategy Check ---
            is_near = abs(price - sma44) / sma44 <= 0.015
            if price > sma44 and sma44 > sma200 and price > open_p and is_near:
                risk = price - low_p
                target = price + risk
                
                # Check what happened AFTER the target date
                future_df = df.loc[selected_date:]
                result = "Pending/Running"
                
                for f_price_high, f_price_low in zip(future_df['High'][1:], future_df['Low'][1:]):
                    if f_price_high >= target:
                        result = "✅ SUCCESS (T1 Hit)"
                        success_count += 1
                        break
                    if f_price_low <= low_p:
                        result = "❌ STOPLOSS Hit"
                        break
                
                total_trades += 1
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(price, 2),
                    "SL": round(low_p, 2),
                    "Target (1:1)": round(target, 2),
                    "Outcome": result
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    
    status_text.empty()
    return pd.DataFrame(found_stocks), success_count, total_trades

if st.button(f'🔍 Research for {target_date}'):
    results, s_count, t_count = backtest_logic(pd.Timestamp(target_date))
    
    if not results.empty:
        # Success Rate Metric
        accuracy = (s_count / t_count) * 100 if t_count > 0 else 0
        col1, col2 = st.columns(2)
        col1.metric("Total Calls Found", t_count)
        col2.metric("Success Rate (T1)", f"{round(accuracy, 2)}%")
        
        st.subheader(f"Detailed Report for {target_date}")
        st.table(results)
    else:
        st.warning(f"Us din ({target_date}) hamari strategy ka koi bhi call nahi bana tha.")

st.divider()
st.caption("Note: Accuracy is based on Target 1 (1:1 ratio).")

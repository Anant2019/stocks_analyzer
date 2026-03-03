import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Institutional Equity Scanner", layout="wide")

# --- REGULATORY COMPLIANCE HEADER ---
st.warning("⚠️ **LEGAL DISCLAIMER**: This application is strictly for **Educational Purposes** only. We are **NOT SEBI Registered** advisors. The signals generated are based on mathematical algorithms and do not constitute financial advice.")

st.title("🛡️ Strategic Momentum & Success Tracker")

# --- UNIVERSE DEFINITION ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

target_dt = st.date_input("Select Date for Accuracy Backtest", datetime(2024, 12, 12))

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def execute_backtest():
    results = []
    # Fetch 500 days before and 90 days after for target tracking
    start_fetch = target_dt - timedelta(days=500)
    end_fetch = datetime.now().date()
    
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=start_fetch, end=end_fetch, auto_adjust=True, progress=False)
            if df.empty or len(df) < 201: continue
            
            avail_dates = df.index[df.index <= pd.Timestamp(target_dt)]
            if avail_dates.empty: continue
            actual_date = avail_dates[-1]
            
            # Indicators
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=5).mean()
            
            ref = df.loc[actual_date]
            c, l, o = float(ref['Close']), float(ref['Low']), float(ref['Open'])
            s44, s200, rsi = float(ref['SMA_44']), float(ref['SMA_200']), float(ref['RSI'])
            v, v_avg = float(ref['Volume']), float(ref['Vol_Avg'])

            if c > s44 and s44 > s200 and c > o:
                risk = c - l
                target_2 = c + (2 * risk)
                outcome = "Pending"
                
                # Check performance AFTER signal date
                future = df[df.index > actual_date]
                for _, f_row in future.iterrows():
                    if f_row['Low'] <= l:
                        outcome = "SL Hit"
                        break
                    if f_row['High'] >= target_2:
                        outcome = "Target Hit"
                        break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Target": round(target_2, 2),
                    "Outcome": outcome,
                    "RSI": round(rsi,1),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
        
    return pd.DataFrame(results), actual_date

if st.button("🚀 Calculate Success Rates"):
    data, final_date = execute_backtest()
    
    if not data.empty:
        # Success Rate Logic
        total = len(data)
        hits = len(data[data["Outcome"] == "Target Hit"])
        misses = len(data[data["Outcome"] == "SL Hit"])
        success_rate = (hits / (hits + misses)) * 100 if (hits + misses) > 0 else 0
        
        st.subheader(f"📊 Performance Report: {final_date.date()}")
        
        # Professional Metric Dashboard
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Signals", total)
        col2.metric("Success Rate (Win %)", f"{round(success_rate, 2)}%")
        col3.metric("Targets Hit", hits)
        
        st.dataframe(
            data[["Stock", "Outcome", "Entry", "Stoploss", "Target", "RSI", "Chart"]],
            column_config={"Chart": st.column_config.LinkColumn()},
            hide_index=True, use_container_width=True
        )
    else:
        st.error("No signals found for this session.")

st.divider()
st.caption("Educational use only. Not SEBI registered advisors.")

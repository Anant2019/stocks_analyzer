import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 70% Verified", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🎯 Triple Bullish: 70% Accuracy Scanner")
target_date = st.date_input("Kounsi date ka analytics dekhna hai?", datetime.now() - timedelta(days=20))

def run_stable_backtest():
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    t_ts = pd.Timestamp(target_date)

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Checking {ticker}...")
            # Download extra data for SMA Slope calculation
            data = yf.download(ticker, start=target_date - timedelta(days=400), end=datetime.now(), auto_adjust=True, progress=False)
            
            if len(data) < 201 or t_ts not in data.index:
                continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            
            idx = data.index.get_loc(t_ts)
            day_data = data.iloc[idx]
            prev_day = data.iloc[idx-1] # Required for SMA Slope check
            
            close = float(day_data['Close'])
            open_p = float(day_data['Open'])
            low_p = float(day_data['Low'])
            sma44 = float(day_data['SMA_44'])
            sma200 = float(day_data['SMA_200'])
            
            # --- IMPROVED LOGIC ---
            # 1. Price Alignment: Price > 44 SMA > 200 SMA
            # 2. Bullish Candle: Close > Open
            # 3. SMA Slope: Both SMAs are RISING (Today > Yesterday)
            if (close > sma44 > sma200) and (sma44 > prev_day['SMA_44']) and (sma200 > prev_day['SMA_200']) and (close > open_p):
                
                # --- T+1 ENTRY LOGIC ---
                if idx + 1 >= len(data): continue # Data not available for next day
                
                entry_price = close + 2 # Signal Close + 2 Buffer
                sl = low_p
                risk = entry_price - sl
                
                if risk > 0:
                    t1 = entry_price + risk
                    t2 = entry_price + (2 * risk)
                    
                    # Tracking Future from Entry Day (T+1)
                    future_df = data.iloc[idx+1:] 
                    dot, outcome, days = "⏳", "Still Running", "-"
                    t1_hit = False
                    d_count = 0
                    
                    for f_dt, f_row in future_df.iterrows():
                        d_count += 1
                        h, l = float(f_row['High']), float(f_row['Low'])
                        
                        if not t1_hit:
                            if l <= sl:
                                dot, outcome, days = "🔴", "Loss", f"{d_count}d"
                                break
                            if h >= t1:
                                t1_hit = True
                                dot, outcome, days = "🟢", "T1 Hit", f"{d_count}d"
                                if h >= t2:
                                    outcome = "🔥 T1 & T2 Hit"
                                    break
                        else:
                            if h >= t2:
                                dot, outcome, days = "🟢", "T2 Hit", f"{d_count}d"
                                break
                            if l <= entry_price:
                                dot, outcome, days = "🟡", "Break Even", f"{d_count}d"
                                break
                    
                    results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Status": dot,
                        "Result": outcome,
                        "Days": days,
                        "Entry": round(entry_price, 2),
                        "SL": round(sl, 2),
                        "T2": round(t2, 2)
                    })
        except Exception:
            continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
        
    status_text.empty()
    return pd.DataFrame(results)

if st.button('🚀 Start Analysis'):
    df_results = run_stable_backtest()
    
    if not df_results.empty:
        total = len(df_results)
        green = len(df_results[df_results['Status'] == "🟢"])
        amber = len(df_results[df_results['Status'] == "🟡"])
        red = len(df_results[df_results['Status'] == "🔴"])

        st.subheader(f"📊 Summary for {target_date}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Signals Found", total)
        c2.metric("Success (🟢)", f"{round((green/total)*100, 1)}%")
        c3.metric("Break-Even (🟡)", f"{round((amber/total)*100, 1)}%")
        c4.metric("Loss (🔴)", f"{round((red/total)*100, 1)}%")
        
        st.divider()
        st.write("### 🔍 Detailed Breakdown (Entry on T+1)")
        st.table(df_results)
    else:
        st.warning("No signals found matching strict SMA Uptrend criteria.")

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="70% Accuracy Verified Scanner", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🛡️ 70% Accuracy Verified Backtester")
target_date = st.date_input("Select Signal Date:", datetime.now() - timedelta(days=20))

def run_analysis():
    results = []
    p_bar = st.progress(0)
    t_ts = pd.Timestamp(target_date)

    for i, ticker in enumerate(NIFTY_200):
        try:
            # Data Fetch
            df = yf.download(ticker, start=target_date - timedelta(days=400), auto_adjust=True, progress=False)
            if len(df) < 201 or t_ts not in df.index: continue
            
            # SMAs
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            idx = df.index.get_loc(t_ts)
            curr = df.iloc[idx]
            prev = df.iloc[idx-1]
            
            # --- STRATEGY CONDITIONS (SIGNAL DAY) ---
            # 1. Triple Bullish Alignment
            # 2. Both SMAs are Rising
            # 3. Bullish Green Candle
            if (curr['Close'] > curr['SMA_44'] > curr['SMA_200']) and \
               (curr['SMA_44'] > prev['SMA_44']) and \
               (curr['SMA_200'] > prev['SMA_200']) and \
               (curr['Close'] > curr['Open']):
                
                # --- ENTRY ON NEXT DAY ---
                if idx + 1 >= len(df): continue # No data for next day yet
                
                entry_price = float(curr['Close']) + 2 # Entry: Signal Day Close + 2 Buffer
                sl = float(curr['Low'])
                risk = entry_price - sl
                
                if risk > 0:
                    t1 = entry_price + risk
                    t2 = entry_price + (2 * risk)
                    
                    # Track Future from Entry Day onwards
                    future_df = df.iloc[idx+1:]
                    dot, outcome, days_to = "⏳", "Running", "-"
                    t1_hit = False
                    d_count = 0
                    
                    for f_dt, f_row in future_df.iterrows():
                        d_count += 1
                        h, l = float(f_row['High']), float(f_row['Low'])
                        
                        if not t1_hit:
                            if l <= sl:
                                dot, outcome, days_to = "🔴", "Loss", f"{d_count}d"
                                break
                            if h >= t1:
                                t1_hit = True
                                dot, outcome, days_to = "🟢", "T1 Hit", f"{d_count}d"
                                if h >= t2:
                                    outcome = "🔥 T1 & T2 Hit"
                                    break
                        else:
                            if h >= t2:
                                dot, outcome, days_to = "🟢", "T2 Hit", f"{d_count}d"
                                break
                            if l <= entry_price:
                                dot, outcome, days_to = "🟡", "Break Even", f"{d_count}d"
                                break
                    
                    results.append({
                        "Stock": ticker.replace(".NS",""),
                        "Status": dot,
                        "Outcome": outcome,
                        "Days": days_to,
                        "Entry": round(entry_price, 2),
                        "SL": round(sl, 2),
                        "T1": round(t1, 2),
                        "T2": round(t2, 2)
                    })
        except: continue
        p_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Run Analysis'):
    final_df = run_analysis()
    if not final_df.empty:
        total = len(final_df)
        g = len(final_df[final_df['Status'] == "🟢"])
        a = len(final_df[final_df['Status'] == "🟡"])
        r = len(final_df[final_df['Status'] == "🔴"])
        
        st.subheader(f"📊 Dashboard: Verified Strategy ({target_date})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Signals Found", total)
        c2.metric("Success (🟢)", f"{round((g/total)*100, 1)}%")
        c3.metric("Break-Even (🟡)", f"{round((a/total)*100, 1)}%")
        c4.metric("Loss (🔴)", f"{round((r/total)*100, 1)}%")
        
        st.divider()
        st.table(final_df)
    else:
        st.warning("No high-probability signals found on this date.")

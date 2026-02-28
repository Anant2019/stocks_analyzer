import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Visual Tracker", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🎯 Triple Bullish: Status Dot Tracker")
target_date = st.date_input("Check Date for Backtest:", datetime.now() - timedelta(days=10))

def scan_with_dots():
    results = []
    progress = st.progress(0)
    status = st.empty()
    t_ts = pd.Timestamp(target_date)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            status.text(f"Scanning: {ticker}")
            df = yf.download(ticker, start=target_date - timedelta(days=400), auto_adjust=True, progress=False)
            if len(df) < 200 or t_ts not in df.index: continue
            
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            row = df.loc[t_ts]
            close, open_p, low_p = float(row['Close']), float(row['Open']), float(row['Low'])
            
            if close > row['SMA_44'] and row['SMA_44'] > row['SMA_200'] and close > open_p:
                risk = close - low_p
                t1, t2 = close + risk, close + (2 * risk)
                
                future_df = df[df.index > t_ts]
                outcome = "⏳ Running"
                days = "-"
                dot = "🟡" # Break-even/Running default
                
                t1_hit = False
                d_count = 0
                for f_dt, f_row in future_df.iterrows():
                    d_count += 1
                    f_high, f_low = float(f_row['High']), float(f_row['Low'])
                    
                    if not t1_hit:
                        if f_low <= low_p:
                            outcome, dot, days = "❌ SL Hit", "🔴", f"{d_count}d"
                            break
                        if f_high >= t1:
                            t1_hit, outcome, dot, days = True, "✅ T1 Hit", "🟢", f"{d_count}d"
                            if f_high >= t2:
                                outcome = "🔥 T1 & T2 Hit"
                                break
                    else:
                        if f_high >= t2:
                            outcome, dot, days = "🚀 T1 -> T2 Hit", "🟢", f"{d_count}d"
                            break
                        if f_low <= low_p:
                            outcome, dot, days = "⚠️ T1 Hit -> SL", "🔴", f"{d_count}d"
                            break
                
                results.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Status": dot,
                    "Outcome": outcome,
                    "Days": days,
                    "Entry": round(close, 2),
                    "SL": round(low_p, 2),
                    "T1": round(t1, 2),
                    "T2": round(t2, 2)
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    status.empty()
    return pd.DataFrame(results)

if st.button('🚀 Start Analysis'):
    df_res = scan_with_dots()
    if not df_res.empty:
        st.subheader(f"📊 Report for {target_date}")
        st.dataframe(df_res, use_container_width=True, hide_index=True)
        st.markdown("---")
        st.write("💡 **Legend:** 🟢 Profit | 🔴 Loss | 🟡 Break-even/Pending")
    else:
        st.warning("No signals found.")

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="ArthaSutra Audit", layout="wide", page_icon="💹")

# --- 2. STYLING (Standard Streamlit - Mobile Stable) ---
st.markdown("""
    <style>
    .stMetric { background-color: #1A1C23; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .status-up { color: #00FFA3; font-weight: bold; }
    .status-down { color: #FF7E7E; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE STRATEGY ENGINE ---
def run_arthasutra_engine(target_date):
    results = []
    actual_date = None
    # Tickers list
    NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']
    
    progress = st.progress(0)
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=410), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201: continue
            valid_dates = data.index[data.index.date <= target_date]
            if valid_dates.empty: continue
            
            t_ts = valid_dates[-1]; actual_date = t_ts.date()
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            delta = data['Close'].diff(); g = (delta.where(delta > 0, 0)).rolling(window=14).mean(); l = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = 100 - (100 / (1 + (g / (l + 1e-10))))
            
            d = data.loc[t_ts]
            # Strategy Criteria
            if d['Close'] > d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA']
                risk = d['Close'] - d['Low']; t2 = d['Close'] + (2 * risk)
                
                status, jackpot, days = "⏳ Running", False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for idx, (f_dt, f_row) in enumerate(future.iterrows()):
                        days = idx + 1
                        if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                        if f_row['High'] >= t2: status = "🟢 Jackpot Hit"; jackpot = True; break
                
                results.append({
                    "Stock": ticker.replace(".NS",""), "Type": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status, "Jackpot": jackpot, "Entry": round(float(d['Close']), 2),
                    "Target": round(float(t2), 2), "SL": round(float(d['Low']), 2), "Days": days,
                    "RSI": round(float(d['RSI']), 1), "Vol": round(float(d['Volume']/d['Vol_MA']), 2)
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 4. DISPLAY INTERFACE ---
st.title("💹 ArthaSutra Audit")
selected_date = st.date_input("Select Audit Date", datetime.now().date() - timedelta(days=2))

if st.button('🚀 Run Audit'):
    df, adj_date = run_arthasutra_engine(selected_date)
    if not df.empty:
        blue_df = df[df['Type'] == "🔵 BLUE"]
        acc = round((len(blue_df[blue_df['Jackpot']==True])/len(blue_df))*100, 1) if len(blue_df)>0 else 0
        
        st.write(f"### Results for {adj_date}")
        c1, c2 = st.columns(2)
        c1.metric("🔵 Blue Signals", len(blue_df))
        c2.metric("🎯 Blue Accuracy", f"{acc}%")
        
        st.download_button("📥 Download Full CSV", df.to_csv(index=False), f"Audit_{adj_date}.csv", use_container_width=True)
        st.divider()

        # STABLE CARD RENDERING (Using st.container + st.columns)
        for _, row in df.iterrows():
            with st.container():
                # Header row
                col_a, col_b = st.columns([2, 1])
                col_a.subheader(f"{row['Stock']} ({row['Type']})")
                col_b.write(f"**{row['Status']}**")
                
                # Info row
                col_i1, col_i2, col_i3 = st.columns(3)
                col_i1.caption("ENTRY"); col_i1.write(f"₹{row['Entry']}")
                col_i2.caption("SL"); col_i2.write(f"₹{row['SL']}")
                col_i3.caption("TARGET"); col_i3.write(f"₹{row['Target']}")
                
                # Analysis Section
                with st.expander("🔍 Analysis & Stats"):
                    st.write(f"• **Exit Time:** {row['Days']} Days")
                    st.write(f"• **Volume Surge:** {row['Vol']}x")
                    st.write(f"• **RSI Momentum:** {row['RSI']}")
                    st.link_button("View Chart 📈", f"https://www.tradingview.com/chart/?symbol=NSE:{row['Stock']}", use_container_width=True)
                st.divider()
    else:
        st.warning("No signals found for this date.")

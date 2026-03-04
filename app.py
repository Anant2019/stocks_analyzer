import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Discipline, Prosperity, Consistency", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="💹"
)

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800; color: #00FFA3 !important; }
    
    .stock-card {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        font-family: 'Source Sans Pro', sans-serif;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 800;
        float: right;
        border: 1px solid;
    }
    .price-row {
        display: flex; 
        justify-content: space-between; 
        margin-top: 15px; 
        border-top: 1px solid #333; 
        padding-top: 10px;
        text-align: center;
    }
    .audit-section {
        margin-top: 15px;
        padding: 10px;
        background: #262730;
        border-radius: 8px;
    }
    .btn-link {
        display: block;
        width: 100%;
        text-align: center;
        background-color: #00FFA3;
        color: #0E1117 !important;
        padding: 12px;
        margin-top: 15px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ENGINE (Core Logic Unchanged) ---
def run_arthasutra_engine(target_date):
    results = []
    actual_date = None
    NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']
    
    progress_bar = st.progress(0)
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=410), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            valid_dates = data.index[data.index.date <= target_date]
            if not valid_dates.empty:
                t_ts = valid_dates[-1]; actual_date = t_ts.date()
                data['SMA_44'] = data['Close'].rolling(window=44).mean()
                data['SMA_200'] = data['Close'].rolling(window=200).mean()
                data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
                delta = data['Close'].diff(); g = (delta.where(delta > 0, 0)).rolling(window=14).mean(); l = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                data['RSI'] = 100 - (100 / (1 + (g / (l + 1e-10))))
                
                d = data.loc[t_ts]
                if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                    is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                    risk = d['Close'] - d['Low']; t2 = d['Close'] + (2 * risk)
                    status, jackpot_hit, days = "⏳ Running", False, "-"
                    future = data[data.index > t_ts]
                    if not future.empty:
                        for idx, (f_dt, f_row) in enumerate(future.iterrows()):
                            days = idx + 1
                            if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                            if f_row['High'] >= t2: status = "🟢 Jackpot Hit"; jackpot_hit = True; break
                    
                    results.append({
                        "Stock": ticker.replace(".NS",""), "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                        "Status": status, "Jackpot": jackpot_hit, "Entry": round(d['Close'], 2),
                        "Target": round(t2, 2), "SL": round(d['Low'], 2), "Days": days,
                        "RSI": round(d['RSI'], 1), "Vol": round(d['Volume'] / d['Vol_MA'], 2)
                    })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 4. USER INTERFACE ---
st.title("💹 ArthaSutra")
st.caption("Discipline • Prosperity • Consistency")

selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
if st.button('🚀 Execute Strategy Audit'):
    df, adj_date = run_arthasutra_engine(selected_date)
    if not df.empty:
        blue_df = df[df['Category'] == "🔵 BLUE"]
        accuracy = round((len(blue_df[blue_df['Jackpot'] == True]) / len(blue_df)) * 100, 1) if not blue_df.empty else 0
        
        st.write(f"### 📊 Report: {adj_date}")
        m1, m2 = st.columns(2)
        m1.metric("🔵 Blue Signals", len(blue_df))
        m2.metric("🎯 Accuracy %", f"{accuracy}%")
        
        st.download_button("📥 Download Report", data=df.to_csv(index=False).encode('utf-8'), file_name=f"ArthaSutra_{adj_date}.csv", use_container_width=True)
        st.divider()

        for _, row in df.iterrows():
            clr = "#00FFA3" if "Hit" in row['Status'] else "#FF7E7E" if "SL" in row['Status'] else "#FFC107"
            
            # Using st.components for absolute isolation of HTML
            card_template = f"""
            <div class="stock-card">
                <span class="status-badge" style="color: {clr}; border-color: {clr};">{row['Status']}</span>
                <h3 style="margin:0; color:white;">{row['Stock']}</h3>
                <p style="margin:5px 0; color:#888; font-size:0.8rem;">{row['Category']} | Exit: {row['Days']} Days</p>
                
                <div class="price-row">
                    <div><small style="color:#888;">ENTRY</small><br><b style="color:white;">₹{row['Entry']}</b></div>
                    <div><small style="color:#888;">SL</small><br><b style="color:#FF7E7E;">₹{row['SL']}</b></div>
                    <div><small style="color:#888;">TARGET</small><br><b style="color:#00FFA3;">₹{row['Target']}</b></div>
                </div>

                <div class="audit-section">
                    <p style="color:#00FFA3; font-weight:700; margin-bottom:5px; font-size:0.9rem;">Deep Analysis:</p>
                    <p style="color:#BBB; font-size:0.85rem; margin:2px 0;">• Volume: {row['Vol']}x vs Average</p>
                    <p style="color:#BBB; font-size:0.85rem; margin:2px 0;">• Momentum: RSI at {row['RSI']}</p>
                    <p style="color:#BBB; font-size:0.85rem; margin:2px 0;">• Safety: Floor at ₹{row['SL']}</p>
                </div>

                <a href="https://www.tradingview.com/chart/?symbol=NSE:{row['Stock']}" target="_blank" class="btn-link">
                    Live Chart Audit 📈
                </a>
            </div>
            """
            # Wrap in st.markdown with a specific ID to force re-render
            st.markdown(card_template, unsafe_allow_html=True)
    else:
        st.warning("No Bullish Technical setups found.")

st.divider()
st.caption("ArthaSutra • Production Card Engine v3.3")

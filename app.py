import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Precision Audit", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="💹"
)

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 800; color: #00FFA3 !important; }
    
    /* Button Styling */
    .stButton button, .stDownloadButton button {
        border-radius: 12px; padding: 0.6rem 2rem; font-weight: 700;
        background-color: #262730; color: white; border: 1px solid #4B4B4B; transition: 0.3s;
        width: 100% !important;
    }
    .stButton button:hover, .stDownloadButton button:hover { border-color: #00FFA3; color: #00FFA3; }
    
    /* Card Design */
    .trade-card {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        border-left: 5px solid #444;
    }
    .rr-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 10px;
        text-align: center;
        margin-top: 10px;
    }
    .rr-item {
        background: rgba(255, 255, 255, 0.03);
        padding: 8px;
        border-radius: 8px;
    }
    .duration-badge {
        background-color: rgba(0, 255, 163, 0.1);
        color: #00FFA3;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .tv-link {
        display: block;
        background: #262730;
        color: #00FFA3 !important;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        margin-top: 15px;
        font-weight: bold;
        text-decoration: none;
        border: 1px solid #444;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LEGAL NOTICE ---
st.error("🔒 *LEGAL DISCLOSURE: NOT SEBI REGISTERED*")

# --- 4. TICKER LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BANKBARODA.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS', 'INFY.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

# --- 5. CORE ENGINE ---
@st.cache_data(ttl=3600)
def run_arthasutra_engine(target_date):
    results = []
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            
            valid = data[data.index.date <= target_date]
            if valid.empty: continue
            t_ts = valid.index[-1]
            
            # Indicators
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            data['Vol_MA'] = data['Volume'].rolling(20).mean()
            
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            
            d = data.loc[t_ts]
            
            # Entry Logic
            if d['Close'] > d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA']
                sl = float(d['Low'])
                entry = float(d['Close'])
                risk = entry - sl
                
                if risk <= 0: continue
                
                t1 = entry + risk
                t2 = entry + (2 * risk)
                
                status, days = "⏳ Running", "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['Low'] <= sl: status = "🔴 SL Hit"; days = count; break
                        if f_row['High'] >= t2: status = "🟢 Jackpot Hit"; days = count; break
                
                results.append({
                    "Stock": ticker.replace(".NS",""), "Cat": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status, "Entry": round(entry, 2), "SL": round(sl, 2),
                    "T1": round(t1, 2), "T2": round(t2, 2), "Days": days, "RSI": round(float(d['RSI']), 1)
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    
    return pd.DataFrame(results), target_date

# --- 6. DISPLAY ---
st.title("💹 ArthaSutra")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=5))

if st.button('🚀 Execute Strategy Audit', use_container_width=True):
    df, adj_date = run_arthasutra_engine(selected_date)
    
    if not df.empty:
        st.write(f"### 📊 Audit Report: {adj_date}")
        
        # Download Button
        st.download_button("📂 Download CSV Report", df.to_csv(index=False), f"ArthaSutra_{adj_date}.csv", use_container_width=True)
        
        st.divider()

        for _, row in df.iterrows():
            status_clr = "#00FFA3" if "Jackpot" in row['Status'] else "#FF7E7E" if "SL" in row['Status'] else "#FFC107"
            
            st.markdown(f"""
            <div class="trade-card" style="border-left-color: {status_clr};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.4rem; font-weight: 800; color: white;">{row['Stock']}</span>
                    <div style="text-align: right;">
                        <span style="font-weight: bold; color: {status_clr};">{row['Status']}</span><br>
                        <span class="duration-badge">{row['Days']} Sessions</span>
                    </div>
                </div>
                
                <div class="rr-grid">
                    <div class="rr-item"><small style="color:#888;">STOP LOSS</small><br><b style="color:#FF7E7E;">₹{row['SL']}</b></div>
                    <div class="rr-item"><small style="color:#888;">ENTRY</small><br><b>₹{row['Entry']}</b></div>
                    <div class="rr-item"><small style="color:#888;">RSI</small><br><b>{row['RSI']}</b></div>
                </div>

                <div class="rr-grid" style="background: rgba(0, 255, 163, 0.04); padding: 5px; border-radius: 8px;">
                    <div class="rr-item" style="background:transparent;"><small style="color:#888;">TARGET 1:1</small><br><b>₹{row['T1']}</b></div>
                    <div class="rr-item" style="background:transparent;"><small style="color:#888;">JACKPOT 1:2</small><br><b style="color:#00FFA3;">₹{row['T2']}</b></div>
                    <div class="rr-item" style="background:transparent;"><small style="color:#888;">TYPE</small><br><b>{row['Cat']}</b></div>
                </div>
                
                <a href="https://www.tradingview.com/chart/?symbol=NSE:{row['Stock']}" target="_blank" class="tv-link">Analyze Chart 📈</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No Bullish Technical setups found.")

st.divider()
st.caption("ArthaSutra • Stable Build v4.9")

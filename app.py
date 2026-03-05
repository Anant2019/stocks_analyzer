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
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 800; color: #00FFA3 !important; }
    .stButton button, .stDownloadButton button {
        border-radius: 12px; padding: 0.6rem 2rem; font-weight: 700;
        background-color: #262730; color: white; border: 1px solid #4B4B4B; transition: 0.3s;
        width: 100% !important;
    }
    .stButton button:hover, .stDownloadButton button:hover { border-color: #00FFA3; color: #00FFA3; }
    
    .trade-card {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 5px;
        border-left: 5px solid #333;
    }
    .duration-badge {
        background-color: rgba(0, 255, 163, 0.1);
        color: #00FFA3;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .rr-label { color: #888; font-size: 0.72rem; text-transform: uppercase; font-weight: bold; }
    .rr-value { color: white; font-size: 0.95rem; font-weight: bold; }
    .profit-pct { color: #00FFA3; font-size: 0.7rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE ENGINE ---
def run_arthasutra_engine(target_date):
    results = []
    actual_date = None
    progress_bar = st.progress(0)
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=410), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            valid_dates = data.index[data.index.date <= target_date]
            if valid_dates.empty: continue
            t_ts = valid_dates[-1]; actual_date = t_ts.date()
            
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            data['Vol_MA'] = data['Volume'].rolling(20).mean()
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            
            d = data.loc[t_ts]
            if d['Close'] > d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                sl = round(d['Low'], 2)
                risk_amt = d['Close'] - sl
                if risk_amt <= 0: continue
                
                t1 = round(d['Close'] + risk_amt, 2)
                t2 = round(d['Close'] + (2 * risk_amt), 2)
                t1_pct = round(((t1/d['Close'])-1)*100, 1)
                t2_pct = round(((t2/d['Close'])-1)*100, 1)
                
                status, t1_hit, t2_hit, days = "⏳ Running", False, False, "-"
                future = data[data.index > t_ts]
                
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['High'] >= t1: t1_hit = True
                        if f_row['High'] >= t2: 
                            status = "🟢 Jackpot Hit"; t2_hit = True; days = count; break
                        if f_row['Low'] <= sl: 
                            status = "🔴 SL Hit"; days = count; break

                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "T1_Pct": t1_pct, "T2_Pct": t2_pct,
                    "T1_Hit": t1_hit, "T2_Hit": t2_hit, "Days": days, "RSI": round(d['RSI'], 1)
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 4. USER INTERFACE ---
st.title("💹 ArthaSutra")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=5))

if st.button('🚀 Execute Strategy Audit', use_container_width=True):
    df, adj_date = run_arthasutra_engine(selected_date)
    if not df.empty:
        t1_ratio = (len(df[df['T1_Hit'] == True]) / len(df)) * 100
        t2_ratio = (len(df[df['T2_Hit'] == True]) / len(df)) * 100
        
        st.write(f"### 📊 Accuracy Metrics: {adj_date}")
        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 1:1 Success Ratio", f"{round(t1_ratio, 1)}%")
        m2.metric("🔥 1:2 Jackpot Ratio", f"{round(t2_ratio, 1)}%")
        m3.metric("📈 Total Signals", len(df))
        
        st.divider()
        st.download_button("📂 Download Full CSV Report", df.to_csv(index=False), f"Audit_{adj_date}.csv", use_container_width=True)

        for _, row in df.iterrows():
            border_clr = "#00FFA3" if row['T2_Hit'] else "#FFC107" if row['T1_Hit'] else "#FF7E7E" if "SL" in row['Status'] else "#333"
            
            st.markdown(f"""
            <div class="trade-card" style="border-left-color: {border_clr};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.3rem; font-weight: bold; color: white;">{row['Stock']}</span>
                    <div style="text-align: right;">
                        <span style="font-weight: bold; color: {border_clr};">{row['Status']}</span><br>
                        <span class="duration-badge">{row['Days']} Sessions</span>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 15px; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
                    <div><div class="rr-label">Entry</div><div class="rr-value">₹{row['Entry']}</div></div>
                    <div><div class="rr-label" style="color:#FF7E7E;">SL</div><div class="rr-value">₹{row['SL']}</div></div>
                    <div>
                        <div class="rr-label" style="color:#00FFA3;">T1 (1:1)</div>
                        <div class="rr-value">₹{row['T1']}</div>
                        <div class="profit-pct">+{row['T1_Pct']}%</div>
                    </div>
                    <div>
                        <div class="rr-label" style="color:#00FFA3;">T2 (1:2)</div>
                        <div class="rr-value">₹{row['T2']}</div>
                        <div class="profit-pct">+{row['T2_Pct']}%</div>
                    </div>
                </div>
                <div style="margin-top: 10px; font-size: 0.8rem; color: #666;">
                    Technical Note: RSI {row['RSI']} | 1:1 Hit: {"✅" if row['T1_Hit'] else "❌"}
                </div>
            </div>
            """, unsafe_allow_html=True)

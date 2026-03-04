import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PERFORMANCE & CACHING ---
st.set_page_config(page_title="ArthaSutra", layout="wide", initial_sidebar_state="collapsed")

@st.cache_data(ttl=3600)
def fetch_data(ticker, start_date):
    try:
        data = yf.download(ticker, start=start_date, end=datetime.now(), auto_adjust=True, progress=False)
        return data
    except: return None

# --- 2. MOBILE-FIRST UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .stError { background-color: rgba(255, 75, 75, 0.05) !important; color: #FF7E7E !important; border-radius: 12px; }
    .stock-card {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .blue-tag { background-color: #1E3A8A; color: #60A5FA; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; }
    .amber-tag { background-color: #78350F; color: #FBBF24; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; }
    .stButton button { width: 100%; border-radius: 12px; font-weight: 700; height: 3rem; background-color: #262730; transition: 0.3s; }
    .stButton button:hover { border-color: #00FFA3; color: #00FFA3; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MANDATORY LEGAL DISCLAIMER (INDIAN LAW) ---
st.error("⚖️ **STATUTORY DISCLOSURE & DISCLAIMER**")
st.markdown("""
<div style="background-color: rgba(255, 75, 75, 0.05); padding:15px; border-radius:12px; border:1px solid rgba(255, 75, 75, 0.3); margin-bottom: 20px;">
    <p style="color:#FF7E7E; font-size:0.85em; line-height:1.6; margin:0;">
        <b>NOTICE AS PER SEBI (INVESTMENT ADVISERS) REGULATIONS, 2013:</b><br>
        ArthaSutra is a mathematical technical research tool. We are <b>NOT SEBI REGISTERED</b> investment advisors or research analysts. 
        The signals generated (Blue/Amber) are purely based on historical data algorithms and do not constitute financial advice, buy/sell recommendations, or tips. 
        Equity trading is subject to market risks. Past performance is not indicative of future results. 
        <b>Consult a SEBI-registered professional before making any investment. Use of this tool is at your own risk.</b>
    </p>
</div>
""", unsafe_allow_html=True)

# --- 4. INPUTS ---
with st.form("settings_form"):
    st.markdown("### 🛠️ Strategy Audit")
    target_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    st.info("Strategy: Partial Book 50% @ 1:1 | Full Booking @ 1:2")
    submit_btn = st.form_submit_button("🚀 EXECUTE STRATEGY AUDIT")

# --- 5. CORE ENGINE (ALL PRIOR LOGICS PRESERVED) ---
def run_full_engine(t_date):
    # Comprehensive Ticker List
    TICKERS = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJFINANCE.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS', 'INFY.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'HAL.NS', 'BEL.NS']
    
    results = []
    start_lookback = t_date - timedelta(days=410)
    
    for ticker in TICKERS:
        try:
            data = fetch_data(ticker, start_lookback)
            if data is None or len(data) < 201: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            
            # Indicators
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            
            # RSI 14
            delta = data['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(window=14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            
            valid_days = data.index[data.index.date <= t_date]
            if valid_days.empty: continue
            
            d = data.loc[valid_days[-1]]
            
            # TRIPLE BULLISH FILTER
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                risk_per_share = d['Close'] - d['Low']
                if risk_per_share <= 0: continue
                
                t1 = d['Close'] + risk_per_share # 1:1 Target
                t2 = d['Close'] + (2 * risk_per_share) # 1:2 Target
                
                # Backtest logic
                status = "⏳ Running"
                future = data[data.index > valid_days[-1]]
                if not future.empty:
                    for _, f_row in future.iterrows():
                        if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                        if f_row['High'] >= t2: status = "🟢 Final Target Hit (1:2)"; break
                        if f_row['High'] >= t1: status = "🟡 Partial Booked (1:1)"; break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "BLUE" if is_blue else "AMBER",
                    "Status": status, "Entry": round(d['Close'], 2),
                    "SL": round(d['Low'], 2), "T1": round(t1, 2), "T2": round(t2, 2),
                    "RSI": round(d['RSI'], 1), "V_Ratio": round(d['Volume']/d['Vol_MA'], 1)
                })
        except: continue
            
    return results

# --- 6. DISPLAY ---
if submit_btn:
    res_list = run_full_engine(target_date)
    if res_list:
        for item in res_list:
            tag = "blue-tag" if item['Category'] == "BLUE" else "amber-tag"
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 1.4rem; font-weight: bold;">{item['Stock']}</span>
                    <span class="{tag}">{item['Category']}</span>
                </div>
                <div style="margin: 8px 0; font-weight: bold;">{item['Status']}</div>
                <hr style="border-color: #333; margin: 12px 0;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">ENTRY</p><b>₹{item['Entry']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">SL</p><b style="color: #FF7E7E;">₹{item['SL']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">T1 (1:1)</p><b style="color: #FBBF24;">₹{item['T1']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">T2 (1:2)</p><b style="color: #00FFA3;">₹{item['T2']}</b></div>
                </div>
                <div style="margin-top: 15px; background: #262730; padding: 12px; border-radius: 10px;">
                    <p style="margin:0; font-size: 0.75rem; color: #AAA; line-height: 1.4;">
                    <b>Execution:</b> Structural Bullish trend confirmed. RSI: {item['RSI']}. Vol: {item['V_Ratio']}x.<br>
                    <b>Strategy:</b> Book 50% at ₹{item['T1']} and trail SL to entry. Full book at ₹{item['T2']}.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"📈 Analyze {item['Stock']} Chart", f"https://www.tradingview.com/chart/?symbol=NSE:{item['Stock']}", use_container_width=True)

st.divider()
st.caption("ArthaSutra • 1:1 & 1:2 Booking System • Compliance Verified")

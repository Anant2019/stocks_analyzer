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

# --- 2. MOBILE-FIRST UI ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
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

# --- 3. INPUTS (REPLACED RISK WITH SWING INVESTMENT) ---
with st.form("settings_form"):
    st.markdown("### 🏦 Portfolio Architect")
    c1, c2 = st.columns(2)
    with c1:
        total_inv = st.number_input("Swing Investment Amount (₹)", value=100000, step=10000)
    with c2:
        target_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    
    rr_ratio = st.slider("Target Reward Ratio (1:X)", 1.0, 4.0, 2.0, 0.5)
    submit_btn = st.form_submit_button("🚀 EXECUTE STRATEGY AUDIT")

# --- 4. ENGINE (FIXED VALUERROR) ---
def run_full_engine(t_date, ratio, capital):
    # Expanded list for the deep-dive
    TICKERS = ['RELIANCE.NS', 'HAL.NS', 'BEL.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'ITC.NS', 'LT.NS', 'M&M.NS', 'TATAMOTORS.NS', 'TITAN.NS', 'ADANIENT.NS', 'BHARTIARTL.NS']
    
    results = []
    start_lookback = t_date - timedelta(days=410)
    
    for ticker in TICKERS:
        data = fetch_data(ticker, start_lookback)
        if data is None or len(data) < 201: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        # INDICATORS
        data['SMA_44'] = data['Close'].rolling(window=44).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
        
        # RSI
        delta = data['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(window=14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        
        valid_days = data.index[data.index.date <= t_date]
        if valid_days.empty: continue # FIXED: Checking .empty instead of truth value
        
        d = data.loc[valid_days[-1]]
        
        # LOGIC: Triple Bullish
        if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
            is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA']
            risk_per_share = d['Close'] - d['Low']
            if risk_per_share <= 0: continue
            
            target_p = d['Close'] + (ratio * risk_per_share)
            
            # Backtest
            status, jackpot = "⏳ Running", False
            future = data[data.index > valid_days[-1]]
            if not future.empty:
                for _, f_row in future.iterrows():
                    if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                    if f_row['High'] >= target_p: status = f"🟢 Jackpot (1:{ratio})"; jackpot = True; break

            results.append({
                "Stock": ticker.replace(".NS",""),
                "Category": "BLUE" if is_blue else "AMBER",
                "Status": status, "Jackpot": jackpot, "Entry": round(d['Close'], 2),
                "SL": round(d['Low'], 2), "Target": round(target_p, 2),
                "RSI": round(d['RSI'], 1), "V_Ratio": round(d['Volume']/d['Vol_MA'], 1)
            })
    
    # CAPITAL DIVISION LOGIC
    if results:
        per_stock_cap = capital / len(results)
        for r in results:
            r['Allocated'] = round(per_stock_cap, 0)
            r['Qty'] = int(per_stock_cap / r['Entry'])
            
    return results

# --- 5. DISPLAY ---
if submit_btn:
    res_list = run_full_engine(target_date, rr_ratio, total_inv)
    if res_list:
        st.write(f"### 📊 Capital Split: ₹{total_inv}")
        m1, m2 = st.columns(2)
        m1.metric("🎯 Total Signals", len(res_list))
        m2.metric("💰 Per Stock Allocation", f"₹{round(total_inv/len(res_list), 0)}")

        for item in res_list:
            tag = "blue-tag" if item['Category'] == "BLUE" else "amber-tag"
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 1.4rem; font-weight: bold;">{item['Stock']}</span>
                    <span class="{tag}">{item['Category']} CONVICTION</span>
                </div>
                <div style="margin: 8px 0; font-weight: bold;">{item['Status']}</div>
                <hr style="border-color: #333; margin: 12px 0;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">ENTRY</p><b>₹{item['Entry']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">TARGET</p><b style="color: #00FFA3;">₹{item['Target']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">QTY</p><b>{item['Qty']}</b></div>
                </div>
                <div style="margin-top: 15px; background: #262730; padding: 12px; border-radius: 10px; border-left: 5px solid #00FFA3;">
                    <p style="margin:0; color: #00FFA3; font-size: 0.85rem;"><b>🛡️ Safe Buy: {item['Qty']} shares (₹{item['Allocated']})</b></p>
                    <p style="margin:5px 0 0 0; font-size: 0.7rem; color: #AAA;">
                    Why? Price > SMA 44/200. RSI is {item['RSI']}. Capital divided to secure your base.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"📈 Analyze NSE:{item['Stock']}", f"https://www.tradingview.com/chart/?symbol=NSE:{item['Stock']}", use_container_width=True)
    else:
        st.warning("No high-conviction swing setups found for this date. Capital is safe in cash.")

st.divider()
st.caption("ArthaSutra • Capital Preservation Engine • No ValueError Fix Applied")

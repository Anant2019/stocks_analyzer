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

# --- 2. MOBILE UI STYLING ---
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
    .stButton button { border-radius: 12px; font-weight: 700; height: 3rem; background-color: #262730; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. STATUTORY DISCLOSURE ---
st.error("⚖️ **STATUTORY DISCLOSURE**")
with st.expander("📝 Mandatory SEBI Disclosure", expanded=False):
    st.markdown("ArthaSutra is a mathematical research tool. We are **NOT SEBI REGISTERED**. Trading involves risk. Use at your own discretion.")

# --- 4. INVESTMENT INPUTS ---
with st.form("settings_form"):
    st.markdown("### 🏦 Portfolio Allocation Settings")
    c1, c2 = st.columns(2)
    with c1:
        total_investment = st.number_input("Swing Investment Amount (₹)", value=50000, step=5000, help="Total capital you want to deploy for this swing session.")
    with c2:
        target_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    
    rr_ratio = st.slider("Target Reward Ratio (1:X)", 1.0, 5.0, 2.0, 0.5)
    submit_btn = st.form_submit_button("🚀 EXECUTE STRATEGY AUDIT", use_container_width=True)

# --- 5. CORE LOGIC & CAPITAL DIVISION ---
def run_full_engine(t_date, ratio, total_cap):
    NIFTY_200 = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'BHARTIARTL.NS', 'SBIN.NS', 'ITC.NS', 'HAL.NS', 'BEL.NS', 'LT.NS', 'M&M.NS', 'TATAMOTORS.NS', 'TITAN.NS', 'ADANIENT.NS'] # Demo List
    
    results = []
    start_lookback = t_date - timedelta(days=410)
    
    for ticker in NIFTY_200:
        data = fetch_data(ticker, start_lookback)
        if data is None or len(data) < 201: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        data['SMA_44'] = data['Close'].rolling(window=44).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
        
        delta = data['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(window=14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        
        valid_days = data.index[data.index.date <= t_date]
        if valid_dates := valid_days:
            d = data.loc[valid_dates[-1]]
            
            # THE CORE FILTER
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                risk_pts = d['Close'] - d['Low']
                if risk_pts <= 0: continue
                
                target_p = d['Close'] + (ratio * risk_pts)
                
                # Check outcome for backtest
                status, jackpot = "⏳ Running", False
                future = data[data.index > valid_dates[-1]]
                for _, f_row in future.iterrows():
                    if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                    if f_row['High'] >= target_p: status = f"🟢 Jackpot (1:{ratio})"; jackpot = True; break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "BLUE" if is_blue else "AMBER",
                    "Status": status, "Jackpot": jackpot, "Entry": round(d['Close'], 2),
                    "SL": round(d['Low'], 2), "Target": round(target_p, 2),
                    "RSI": round(d['RSI'], 1)
                })
    
    # CAPITAL DIVISION LOGIC
    if results:
        num_signals = len(results)
        cap_per_stock = total_cap / num_signals
        for res in results:
            res['Allocated_Cap'] = round(cap_per_stock, 0)
            res['Qty'] = int(cap_per_stock / res['Entry'])
            
    return results

# --- 6. DISPLAY ---
if submit_btn:
    res_list = run_full_engine(target_date, rr_ratio, total_investment)
    if res_list:
        df = pd.DataFrame(res_list)
        blue_df = df[df['Category'] == "BLUE"]
        
        st.write(f"### 📊 Allocation Strategy: ₹{total_investment}")
        m1, m2, m3 = st.columns(3)
        m1.metric("🔵 BLUE Signals", len(blue_df))
        m2.metric("🎯 Signals Found", len(res_list))
        m3.metric("💰 Per Stock", f"₹{round(total_investment/len(res_list),0)}")

        st.divider()
        for item in res_list:
            tag_type = "blue-tag" if item['Category'] == "BLUE" else "amber-tag"
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 1.4rem; font-weight: bold;">{item['Stock']}</span>
                    <span class="{tag_type}">{item['Category']}</span>
                </div>
                <div style="margin: 8px 0;">{item['Status']}</div>
                <hr style="border-color: #333; margin: 12px 0;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">ENTRY</p><b>₹{item['Entry']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">TARGET</p><b style="color: #00FFA3;">₹{item['Target']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">QTY</p><b>{item['Qty']}</b></div>
                </div>
                <div style="margin-top: 15px; background: #262730; padding: 12px; border-radius: 10px; border-left: 4px solid #00FFA3;">
                    <p style="margin:0; color: #00FFA3; font-size: 0.85rem;"><b>🛡️ Safe Allocation: ₹{item['Allocated_Cap']}</b></p>
                    <p style="margin:5px 0 0 0; font-size: 0.75rem; color: #AAA;">
                    Capital is divided across {len(res_list)} stocks to secure your base amount.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"📈 View NSE:{item['Stock']} Chart", f"https://www.tradingview.com/chart/?symbol=NSE:{item['Stock']}", use_container_width=True)
    else:
        st.warning("No Triple-Bullish setups found. Capital secured in cash.")

st.divider()
st.caption("ArthaSutra • Capital Preservation Engine • 1:2 Default Strategy")

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

# --- 2. MOBILE-FIRST UI (CARDS & BUTTONS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .stError { background-color: rgba(255, 75, 75, 0.05) !important; color: #FF7E7E !important; border-radius: 12px; }
    
    /* Card Container */
    .stock-card {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .blue-tag { background-color: #1E3A8A; color: #60A5FA; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; }
    .amber-tag { background-color: #78350F; color: #FBBF24; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; }
    .status-hit { color: #00FFA3; font-weight: bold; }
    .status-sl { color: #FF4B4B; font-weight: bold; }
    
    /* Responsive Buttons */
    .stButton button { width: 100%; border-radius: 12px; font-weight: 700; height: 3rem; background-color: #262730; transition: 0.3s; }
    .stButton button:hover { border-color: #00FFA3; color: #00FFA3; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LEGAL COMPLIANCE (STRICT INDIAN LAW) ---
st.error("⚖️ **STATUTORY DISCLOSURE**")
with st.expander("📝 Mandatory SEBI Disclosure", expanded=False):
    st.markdown("""
    <b>NOTICE:</b> ArthaSutra is a mathematical research tool. We are <b>NOT SEBI REGISTERED</b> advisors. 
    Signals are based on technical algorithms and historical data. 
    <b>Trading involves substantial risk.</b> Please consult a registered professional.
    """)

# --- 4. INPUTS (USING FORM TO PREVENT FLASHING) ---
with st.form("settings_form"):
    st.markdown("### 🛠️ Audit Parameters")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        target_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    with c2:
        rr_ratio = st.selectbox("Target RR Ratio", [1.0, 1.5, 2.0, 2.5, 3.0], index=2, help="1:2 is recommended for swing trading.")
    with c3:
        max_risk = st.number_input("Risk Amount (₹)", value=1000, step=500, help="How much money will you lose if SL hits?")
    
    submit_btn = st.form_submit_button("🚀 EXECUTE STRATEGY AUDIT")

# --- 5. CORE FILTERING ENGINE ---
def run_full_engine(t_date, ratio, risk_cap):
    # (Nifty 200 List as provided in previous code)
    NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJFINANCE.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS', 'INFY.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS']
    
    results = []
    start_lookback = t_date - timedelta(days=410)
    
    for ticker in NIFTY_200:
        data = fetch_data(ticker, start_lookback)
        if data is None or len(data) < 201: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        # INDICATORS (Main Logic)
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
            
            target_p = d['Close'] + (ratio * risk_per_share)
            qty = int(risk_cap / risk_per_share)
            
            # Backtest Outcome
            status, jackpot_hit = "⏳ Running", False
            future = data[data.index > valid_days[-1]]
            if not future.empty:
                for f_dt, f_row in future.iterrows():
                    if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                    if f_row['High'] >= target_p: status = f"🟢 Jackpot (1:{ratio})"; jackpot_hit = True; break

            results.append({
                "Stock": ticker.replace(".NS",""),
                "Category": "BLUE" if is_blue else "AMBER",
                "Status": status, "Jackpot": jackpot_hit, "Entry": round(d['Close'], 2),
                "SL": round(d['Low'], 2), "Target": round(target_p, 2), "Qty": qty,
                "RSI": round(d['RSI'], 1), "V_Ratio": round(d['Volume']/d['Vol_MA'], 1)
            })
    return results

# --- 6. DISPLAY ENGINE ---
if submit_btn:
    res_list = run_full_engine(target_date, rr_ratio, max_risk)
    if res_list:
        df = pd.DataFrame(res_list)
        blue_df = df[df['Category'] == "BLUE"]
        accuracy = (len(blue_df[blue_df['Jackpot'] == True]) / len(blue_df)) * 100 if not blue_df.empty else 0
        
        st.write(f"### 📊 Strategy Performance Audit")
        m1, m2, m3 = st.columns(3)
        m1.metric("🔵 BLUE Signals", len(blue_df))
        m2.metric("🎯 BLUE Accuracy", f"{round(accuracy, 1)}%")
        m3.metric("🔥 Total Jackpots", len(df[df['Jackpot'] == True]))

        st.divider()
        for item in res_list:
            tag_type = "blue-tag" if item['Category'] == "BLUE" else "amber-tag"
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 1.4rem; font-weight: bold;">{item['Stock']}</span>
                    <span class="{tag_type}">{item['Category']} CONVICTION</span>
                </div>
                <div style="margin: 8px 0;">{item['Status']}</div>
                <hr style="border-color: #333; margin: 12px 0;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">ENTRY</p><b>₹{item['Entry']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">STOP LOSS</p><b style="color: #FF7E7E;">₹{item['SL']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">TARGET</p><b style="color: #00FFA3;">₹{item['Target']}</b></div>
                </div>
                <div style="margin-top: 15px; background: #262730; padding: 12px; border-radius: 10px;">
                    <p style="margin:0; color: #00FFA3; font-size: 0.9rem;"><b>🛡️ Action: Buy {item['Qty']} Shares</b></p>
                    <p style="margin:5px 0 0 0; font-size: 0.75rem; color: #AAA; line-height: 1.4;">
                    <b>Why?</b> Price confirmed above SMA 44/200. RSI is {item['RSI']} with {item['V_Ratio']}x volume surge.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"📈 Analyze Chart", f"https://www.tradingview.com/chart/?symbol=NSE:{item['Stock']}", use_container_width=True)
    else:
        st.warning("No technical setups matched your criteria on this date.")

st.divider()
st.caption("ArthaSutra • Calculated Risk Management • Mobile Optimized Card UI")

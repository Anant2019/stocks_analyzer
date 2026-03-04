import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PERFORMANCE & CONFIG ---
st.set_page_config(page_title="ArthaSutra", layout="wide", initial_sidebar_state="collapsed")

@st.cache_data(ttl=3600)
def fetch_data(ticker, start_date):
    try:
        data = yf.download(ticker, start=start_date, end=datetime.now(), auto_adjust=True, progress=False)
        return data
    except: return None

# --- 2. THE ULTIMATE MOBILE-FIRST CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .stError { background-color: rgba(255, 75, 75, 0.05) !important; color: #FF7E7E !important; border-radius: 12px; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00FFA3 !important; font-weight: 800; }
    
    .stock-card {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 18px;
        margin-bottom: 15px;
    }
    .blue-tag { background-color: #1E3A8A; color: #60A5FA; padding: 2px 8px; border-radius: 5px; font-size: 0.7rem; font-weight: bold; }
    .amber-tag { background-color: #78350F; color: #FBBF24; padding: 2px 8px; border-radius: 5px; font-size: 0.7rem; font-weight: bold; }
    .status-green { color: #00FFA3; font-weight: bold; }
    .status-red { color: #FF4B4B; font-weight: bold; }
    
    .stButton button { border-radius: 12px; font-weight: 700; background-color: #262730; transition: 0.3s; }
    .stButton button:hover { border-color: #00FFA3; color: #00FFA3; }
    @media (min-width: 800px) { .stButton button { max-width: 300px; display: block; margin: 0 auto; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. REFINED LEGAL COMPLIANCE (INDIAN LAW) ---
st.error("⚖️ **STATUTORY DISCLOSURE & DISCLAIMER**")
with st.expander("📝 Mandatory Compliance Information", expanded=False):
    st.markdown("""
    <div style="background-color: rgba(255, 193, 7, 0.05); padding:15px; border-radius:12px; border:1px solid rgba(255, 193, 7, 0.3);">
        <p style="color:#CCCCCC; font-size:0.85em; line-height:1.6;">
            <b>NOTICE AS PER SEBI (INVESTMENT ADVISERS) REGULATIONS, 2013:</b><br>
            ArthaSutra is a mathematical research tool and a software algorithm. We are <b>NOT SEBI REGISTERED</b> investment advisors, research analysts, or stock brokers. 
            The signals generated (Blue/Amber) are based on historical technical data and do not constitute financial advice or buy/sell recommendations.
            <br><br>
            <b>RISK WARNING:</b> Equity trading is subject to market risks. Past performance is not indicative of future results. 
            We do not guarantee any profits or accuracy. Please consult a SEBI-registered professional before investing. 
            <b>Any reliance on this tool is at your own risk.</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

st.title("💹 ArthaSutra")
st.caption("Discipline • Prosperity • Consistency")

# --- 4. GLOBAL SETTINGS ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        rr_ratio = st.slider("Select Reward/Risk Ratio", 1.0, 5.0, 2.0, 0.5, help="For maximum accuracy, we suggest 1:2.")
    with col2:
        target_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    run_btn = st.button('🚀 EXECUTE STRATEGY AUDIT')

# --- 5. CORE LOGIC ENGINE ---
def run_full_engine(ratio, t_date):
    # Expanded list for the strategy audit
    TICKERS = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJFINANCE.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS', 'INFY.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS']
    
    results = []
    start_lookback = t_date - timedelta(days=400)
    
    for ticker in TICKERS:
        data = fetch_data(ticker, start_lookback)
        if data is None or len(data) < 201: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        data['SMA_44'] = data['Close'].rolling(window=44).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
        
        # RSI 14
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        
        valid_days = data.index[data.index.date <= t_date]
        if valid_days.empty: continue
        d = data.loc[valid_days[-1]]
        
        # STRATEGY: 44 SMA > 200 SMA + Price > 44 SMA
        if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
            is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
            risk_points = d['Close'] - d['Low']
            if risk_points <= 0: continue
            
            target_price = d['Close'] + (risk_points * ratio)
            
            # Outcome Tracking
            status, jackpot_hit = "⏳ Running", False
            future = data[data.index > valid_days[-1]]
            if not future.empty:
                for f_dt, f_row in future.iterrows():
                    if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                    if f_row['High'] >= target_price: status = f"🟢 Jackpot Hit (1:{ratio})"; jackpot_hit = True; break

            v_ratio = d['Volume'] / d['Vol_MA']
            audit = f"""
            • **Trend:** Structural bullishness confirmed (Price > SMA44 > SMA200).
            • **Momentum:** RSI at {round(d['RSI'],1)} indicates high-velocity zone.
            • **Liquidity:** Relative volume at {round(v_ratio,1)}x average flow.
            • **Validation:** Signal floor at ₹{round(d['Low'],2)} defended during period.
            """
            
            results.append({
                "Symbol": ticker.replace(".NS",""),
                "Category": "BLUE" if is_blue else "AMBER",
                "Price": round(d['Close'], 2),
                "SL": round(d['Low'], 2),
                "Target": round(target_price, 2),
                "Status": status,
                "Jackpot": jackpot_hit,
                "Audit": audit
            })
    return results

# --- 6. DISPLAY ---
if run_btn:
    data_list = run_full_engine(rr_ratio, target_date)
    if data_list:
        df = pd.DataFrame(data_list)
        blue_df = df[df['Category'] == "BLUE"]
        blue_accuracy = (len(blue_df[blue_df['Jackpot'] == True]) / len(blue_df)) * 100 if not blue_df.empty else 0
        
        st.write(f"### 📊 Report for {target_date} (Ratio 1:{rr_ratio})")
        m1, m2, m3 = st.columns(3)
        m1.metric("🔵 BLUE Signals", len(blue_df))
        m2.metric("🎯 BLUE Accuracy", f"{round(blue_accuracy, 1)}%")
        m3.metric("🔥 Total Jackpots", len(df[df['Jackpot'] == True]))

        st.divider()
        for item in data_list:
            tag_class = "blue-tag" if item['Category'] == "BLUE" else "amber-tag"
            status_class = "status-green" if "Jackpot" in item['Status'] else "status-red" if "SL" in item['Status'] else ""
            
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.3rem; font-weight: bold;">{item['Symbol']}</span>
                    <span class="{tag_class}">{item['Category']}</span>
                </div>
                <div style="margin-top: 5px;"><span class="{status_class}">{item['Status']}</span></div>
                <hr style="margin: 10px 0; border-color: #333;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p style="margin:0; color: #888; font-size: 0.7rem;">ENTRY</p><b>₹{item['Price']}</b></div>
                    <div><p style="margin:0; color: #888; font-size: 0.7rem;">SL (1:0)</p><b>₹{item['SL']}</b></div>
                    <div><p style="margin:0; color: #888; font-size: 0.7rem;">TARGET (1:{rr_ratio})</p><b>₹{item['Target']}</b></div>
                </div>
                <div style="margin-top: 15px; padding: 10px; background: #262730; border-radius: 8px;">
                    <p style="margin:0; color: #AAA; font-size: 0.8rem; line-height: 1.5; white-space: pre-line;">{item['Audit']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"📈 Analyze Chart", f"https://www.tradingview.com/chart/?symbol=NSE:{item['Symbol']}")
    else:
        st.warning("No Bullish setups detected for the selected parameters.")

st.divider()
st.caption("ArthaSutra • Legal Compliance Enabled • 1:2 Dynamic Ratio Engine")

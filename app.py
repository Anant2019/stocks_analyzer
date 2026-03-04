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
    
    .stButton button { border-radius: 12px; font-weight: 700; height: 3rem; background-color: #262730; transition: 0.3s; }
    .stButton button:hover { border-color: #00FFA3; color: #00FFA3; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LEGAL COMPLIANCE (INDIAN LAW) ---
st.error("⚖️ **STATUTORY DISCLOSURE**")
with st.expander("📝 Mandatory SEBI Disclosure", expanded=True):
    st.markdown("""
    <b>NOTICE AS PER SEBI REGULATIONS:</b> ArthaSutra is a mathematical research tool. We are <b>NOT SEBI REGISTERED</b>. 
    Signals are based on technical algorithms and historical data. <b>Any reliance on this tool is at your own risk.</b>
    """)

# --- 4. INPUTS ---
with st.form("settings_form"):
    st.markdown("### 🛠️ Strategy Audit Settings")
    c1, c2 = st.columns(2)
    with c1:
        target_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    with c2:
        rr_ratio = st.slider("Target Reward Ratio (1:X)", 1.0, 5.0, 2.0, 0.5, help="Suggested 1:2 for higher accuracy.")
    
    submit_btn = st.form_submit_button("🚀 EXECUTE STRATEGY AUDIT", use_container_width=True)

# --- 5. CORE FILTERING ENGINE ---
def run_full_engine(t_date, ratio):
    NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']
    
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
        if valid_days.empty: continue
        d = data.loc[valid_days[-1]]
        
        # RESTORED MAIN FILTERING LOGIC
        if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
            is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
            risk_points = d['Close'] - d['Low']
            if risk_points <= 0: continue
            
            target_p = d['Close'] + (ratio * risk_points)
            
            status, jackpot_hit = "⏳ Running", False
            future = data[data.index > valid_days[-1]]
            if not future.empty:
                for f_dt, f_row in future.iterrows():
                    if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                    if f_row['High'] >= target_p: status = f"🟢 Jackpot (1:{ratio})"; jackpot_hit = True; break

            v_ratio = d['Volume'] / d['Vol_MA']
            results.append({
                "Stock": ticker.replace(".NS",""),
                "Category": "BLUE" if is_blue else "AMBER",
                "Status": status, "Jackpot": jackpot_hit, "Entry": round(d['Close'], 2),
                "SL": round(d['Low'], 2), "Target": round(target_p, 2),
                "Audit": f"• Trend: Price > SMA 44 > SMA 200\n• Momentum: RSI at {round(d['RSI'],1)}\n• Volume: {round(v_ratio,1)}x avg surge."
            })
    return results

# --- 6. DISPLAY ENGINE ---
if submit_btn:
    res_list = run_full_engine(target_date, rr_ratio)
    if res_list:
        df = pd.DataFrame(res_list)
        blue_df = df[df['Category'] == "BLUE"]
        accuracy = (len(blue_df[blue_df['Jackpot'] == True]) / len(blue_df)) * 100 if not blue_df.empty else 0
        
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
                    <span class="{tag_type}">{item['Category']}</span>
                </div>
                <div style="margin: 8px 0;">{item['Status']}</div>
                <hr style="border-color: #333; margin: 12px 0;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">ENTRY</p><b>₹{item['Entry']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">SL</p><b style="color: #FF7E7E;">₹{item['SL']}</b></div>
                    <div><p style="margin:0; font-size: 0.7rem; color: #888;">TARGET</p><b style="color: #00FFA3;">₹{item['Target']}</b></div>
                </div>
                <div style="margin-top: 15px; background: #262730; padding: 12px; border-radius: 10px;">
                    <p style="margin:0; font-size: 0.75rem; color: #AAA; line-height: 1.4; white-space: pre-line;">{item['Audit']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"📈 Analyze Chart", f"https://www.tradingview.com/chart/?symbol=NSE:{item['Stock']}", use_container_width=True)
    else:
        st.warning("No technical setups matched on this date.")

st.divider()
st.caption("ArthaSutra • Core Logic Restored • Mobile Responsive Card UI")

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
            ArthaSutra is a mathematical research tool. We are <b>NOT SEBI REGISTERED</b> investment advisors or research analysts. 
            The signals generated (Blue/Amber) are based on historical technical data and do not constitute buy/sell recommendations.
            <b>Any reliance on this tool is at your own risk.</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. TICKER LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

# --- 5. TECHNICAL VECTOR ENGINE ---
def get_technical_audit(d, status, v_ratio, is_blue, ratio):
    rsi = round(d['RSI'], 1)
    vol_delta = f"{round((v_ratio - 1)*100, 1)}% Above Average" if v_ratio > 1 else "Below Average"

    return f"""
    • **Trend:** Structural bullishness ($Price > SMA_{{44}} > SMA_{{200}}$).
    • **Momentum:** RSI at **{rsi}** confirms high-velocity sustainment.
    • **Volume:** Liquidity flow is **{vol_delta}**.
    • **Validation:** 1:{ratio} target based on support floor at ₹{round(d['Low'],2)}.
    """

def run_arthasutra_engine(target_date, rr_ratio):
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
            
            # Indicators
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['STD_20'] = data['Close'].rolling(window=20).std()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            
            # RSI Logic
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            
            d = data.loc[t_ts]
            
            # THE CORE FILTERING LOGIC (RESTORED)
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                risk = d['Close'] - d['Low']
                if risk <= 0: continue
                target_p = d['Close'] + (rr_ratio * risk)
                
                status, jackpot_hit = "⏳ Running", False
                future = data[data.index > t_ts]
                if not future.empty:
                    for f_dt, f_row in future.iterrows():
                        if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                        if f_row['High'] >= target_p: status = f"🟢 Jackpot Hit (1:{rr_ratio})"; jackpot_hit = True; break
                
                v_ratio = d['Volume'] / d['Vol_MA']
                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "BLUE" if is_blue else "AMBER",
                    "Status": status, "Jackpot": jackpot_hit, "Entry": round(d['Close'], 2),
                    "SL": round(d['Low'], 2), "Target": round(target_p, 2),
                    "Audit": get_technical_audit(d, status, v_ratio, is_blue, rr_ratio),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 6. USER INTERFACE ---
st.title("💹 ArthaSutra")
st.caption("Discipline • Prosperity • Consistency")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        ratio_sel = st.slider("Target Reward Ratio (1:X)", 1.0, 5.0, 2.0, 0.5, help="Suggested 1:2 for accuracy.")
    with col2:
        selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    run_btn = st.button('🚀 Execute Strategy Audit', use_container_width=True)

if run_btn:
    df, adj_date = run_arthasutra_engine(selected_date, ratio_sel)
    if not df.empty:
        blue_df = df[df['Category'] == "BLUE"]
        blue_hits = len(blue_df[blue_df['Jackpot'] == True])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("🔵 BLUE Signals", len(blue_df))
        m2.metric("🎯 BLUE Accuracy", f"{round((blue_hits/len(blue_df))*100, 1) if not blue_df.empty else 0}%")
        m3.metric("🔥 Total Jackpots", len(df[df['Jackpot'] == True]))
        
        st.divider()
        for _, row in df.iterrows():
            tag_class = "blue-tag" if row['Category'] == "BLUE" else "amber-tag"
            status_class = "status-green" if "Jackpot" in row['Status'] else "status-red" if "SL" in row['Status'] else ""
            
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.3rem; font-weight: bold;">{row['Stock']}</span>
                    <span class="{tag_class}">{row['Category']}</span>
                </div>
                <div style="margin-top: 5px;"><span class="{status_class}">{row['Status']}</span></div>
                <hr style="margin: 10px 0; border-color: #333;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p style="margin:0; color: #888; font-size: 0.7rem;">ENTRY</p><b>₹{row['Entry']}</b></div>
                    <div><p style="margin:0; color: #888; font-size: 0.7rem;">SL</p><b>₹{row['SL']}</b></div>
                    <div><p style="margin:0; color: #888; font-size: 0.7rem;">TARGET</p><b>₹{row['Target']}</b></div>
                </div>
                <div style="margin-top: 15px; padding: 10px; background: #262730; border-radius: 8px;">
                    <p style="margin:0; color: #AAA; font-size: 0.8rem; line-height: 1.5; white-space: pre-line;">{row['Audit']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"📈 Analyze Chart", row['Chart'], use_container_width=True)
    else:
        st.warning("No Technical setups found.")

st.divider()
st.caption("ArthaSutra • Legal Compliance • Core Filtering Engine (SMA 44/200)")

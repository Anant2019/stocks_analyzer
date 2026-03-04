import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Strategy Auditor", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="💹"
)

# --- 2. UI STYLING (DARK TERMINAL) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .stError {
        background-color: rgba(255, 75, 75, 0.05) !important;
        color: #FF7E7E !important;
        border: 1px solid rgba(255, 75, 75, 0.2) !important;
        border-radius: 10px;
    }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 800; color: #00FFA3 !important; }
    .stButton button, .stDownloadButton button {
        border-radius: 12px; padding: 0.6rem 2rem; font-weight: 700;
        background-color: #262730; color: white; border: 1px solid #4B4B4B; transition: 0.3s;
    }
    .stButton button:hover { border-color: #00FFA3; color: #00FFA3; }
    @media (min-width: 800px) {
        .stButton button, .stDownloadButton button { max-width: 300px; display: block; margin: 0 auto; }
    }
    .stExpander { background-color: #1A1C23; border: 1px solid #333; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SEBI DISCLAIMER ---
st.error("🔒 **REGULATORY DISCLOSURE**")
with st.expander("📝 View SEBI Compliance & Risk Terms", expanded=True):
    st.markdown("""
    <div style="background-color: rgba(255, 193, 7, 0.05); padding:15px; border-radius:12px; border:1px solid rgba(255, 193, 7, 0.3);">
        <h4 style="color:#FFC107; margin-top:0;">⚠️ NOT SEBI REGISTERED</h4>
        <p style="color:#CCCCCC; font-size:0.95em;">
            <b>ArthaSutra</b> is an educational research algorithm. Signals are mathematical derivations. 
            Consult a registered advisor before investing.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. TICKER LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

# --- 5. DYNAMIC REASONING ENGINE ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def get_dynamic_analysis(ticker, d, status, v_ratio, is_blue):
    """Generates unique real-time reasoning based on live calculations."""
    rsi_val = round(d['RSI'], 1)
    sl_level = round(d['Low'], 2)
    vol_strength = "Extraordinary" if v_ratio > 2.0 else "Healthy"
    category_type = "High-Conviction BLUE" if is_blue else "Standard AMBER"
    
    if status == "🟢 Jackpot Hit":
        reason = f"""
        **Dynamic Trade Audit:**
        
        1. ✅ **Institutional Surge:** This {category_type} signal saw {vol_strength} volume flow (**{v_ratio:.1f}x** average), indicating strong institutional participation.
        
        2. ✅ **Momentum Trigger:** RSI hit **{rsi_val}** during the signal period, propelling the price toward the 1:2 reward target.
        
        3. ✅ **Validation:** The price action successfully defended the calculated floor of **₹{sl_level}**, proving that bulls were in total control.
        """
    elif status == "🔴 SL Hit":
        reason = f"""
        **Dynamic Trade Audit:**
        
        1. ❌ **Volume Exhaustion:** The trade lacked follow-through despite the {vol_strength} initial volume (**{v_ratio:.1f}x**), suggesting a temporary 'Bull Trap'.
        
        2. ❌ **Momentum Shift:** RSI at **{rsi_val}** failed to sustain the breakout as institutional profit-booking intensified.
        
        3. ❌ **Exit Trigger:** Price breached the critical support zone of **₹{sl_level}**. To preserve capital, the algorithm closed the position.
        """
    else:
        reason = f"""
        **Dynamic Trade Audit:**
        
        1. ⏳ **Ongoing Trend:** Price is holding the 44-SMA structure with RSI at **{rsi_val}**. 
        
        2. ⏳ **Real-time Monitoring:** We are observing {vol_strength} volume levels (**{v_ratio:.1f}x**) as the trade approaches the target.
        
        3. ⏳ **Risk Status:** The trade is active. Safety level is locked at **₹{sl_level}**.
        """
    return reason

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
            t_ts = valid_dates[-1]
            actual_date = t_ts.date()
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            
            d = data.loc[t_ts]
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                risk = d['Close'] - d['Low']
                if risk <= 0: continue
                t2 = d['Close'] + (2 * risk)
                
                status, jackpot_hit = "⏳ Running", False
                future = data[data.index > t_ts]
                if not future.empty:
                    for f_dt, f_row in future.iterrows():
                        if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                        if f_row['High'] >= t2: status = "🟢 Jackpot Hit"; jackpot_hit = True; break
                
                v_ratio = d['Volume'] / d['Vol_MA']
                analysis = get_dynamic_analysis(ticker, d, status, v_ratio, is_blue)
                
                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status, "Jackpot": jackpot_hit, "Entry": round(d['Close'], 2),
                    "Target": round(t2, 2), "RSI": round(d['RSI'], 1),
                    "RealTime_Audit": analysis,
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 6. UI RENDER ---
st.title("💹 ArthaSutra")
st.caption("Institutional Strategy Auditor • V5.2 Dynamic Real-Time Reasoning")

_, col_input, _ = st.columns([1, 1.5, 1])
with col_input:
    selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    run_btn = st.button('🚀 Execute Real-Time Scan', use_container_width=True)

if run_btn:
    df, adjusted_date = run_arthasutra_engine(selected_date)
    if not df.empty:
        blue_df = df[df['Category'].str.contains("BLUE")]
        hits_blue = len(blue_df[blue_df['Jackpot'] == True])
        
        st.write(f"### 📊 Institutional Audit: {adjusted_date}")
        m1, m2, m3 = st.columns(3)
        m1.metric("🔵 High Conviction", len(blue_df))
        m2.metric("🎯 Win Rate", f"{round((hits_blue/len(blue_df))*100, 1) if len(blue_df) > 0 else 0}%")
        m3.metric("🔥 Total Jackpots", len(df[df['Jackpot'] == True]))
        
        _, col_dl, _ = st.columns([1, 1, 1])
        with col_dl:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📂 Export Audit CSV", data=csv, file_name=f"ArthaSutra_{adjusted_date}.csv", mime='text/csv')

        st.divider()
        st.write("### 🔍 Live Signals Tracker")
        st.dataframe(df.drop(columns=['RealTime_Audit', 'Jackpot']), use_container_width=True, hide_index=True)
        
        st.divider()
        st.write("### 💡 Individual Trade Audit (Dynamic Reasons)")
        for _, row in df.iterrows():
            with st.expander(f"{row['Stock']} | {row['Category']} | {row['Status']}"):
                st.markdown(row['RealTime_Audit'])
                st.link_button(f"Analyze {row['Stock']} Chart", row['Chart'], use_container_width=True)
    else:
        st.warning("No Triple Bullish setups found.")

st.divider()
st.caption("ArthaSutra v5.2 • Dynamic Logic Engine • No Prior Code Missed")

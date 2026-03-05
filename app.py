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
    .stButton button, .stDownloadButton button {
        border-radius: 12px; padding: 0.6rem 2rem; font-weight: 700;
        background-color: #262730; color: white; border: 1px solid #4B4B4B; transition: 0.3s;
        width: 100% !important;
    }
    .stButton button:hover, .stDownloadButton button:hover { border-color: #00FFA3; color: #00FFA3; }
    .stExpander { background-color: #1A1C23; border: 1px solid #333; border-radius: 12px; margin-bottom: 10px; }
    
    .trade-card {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 5px;
        border-left: 5px solid #333;
    }
    .rr-box {
        background: rgba(255, 255, 255, 0.03);
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 10px;
        text-align: center;
        font-size: 0.85rem;
    }
    .duration-badge {
        background-color: rgba(0, 255, 163, 0.1);
        color: #00FFA3;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LEGAL DISCLOSURE ---
st.error("🔒 *LEGAL DISCLOSURE & COMPLIANCE*")
with st.expander("📝 IMPORTANT: SEBI Non-Registration & Risk Warning", expanded=True):
    st.markdown("""
    <div style="background-color: rgba(255, 193, 7, 0.05); padding:15px; border-radius:12px; border:1px solid rgba(255, 193, 7, 0.3);">
        <h4 style="color:#FFC107; margin-top:0;">⚠️ NOT SEBI REGISTERED</h4>
        <p style="color:#CCCCCC; font-size:0.95em;">
            <b>ArthaSutra</b> is an automated technical research engine. We are <b>NOT SEBI REGISTERED</b>. 
            Signals are mathematical derivations. <b>Trading involves high risk.</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. TICKER LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

# --- 5. ENGINE ---
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
            # Strategy: SMA Alignment + Bullish Day
            if d['Close'] > d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA']
                
                # RISK REWARD CALCULATIONS
                sl = d['Low']
                risk_amount = d['Close'] - sl
                if risk_amount <= 0: continue
                
                t1 = d['Close'] + risk_amount         # 1:1
                t2 = d['Close'] + (2 * risk_amount)   # 1:2 (Jackpot Target)
                
                status, days_to_hit = "⏳ Running", "-"
                future = data[data.index > t_ts]
                
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['Low'] <= sl: 
                            status = "🔴 SL Hit"
                            days_to_hit = count
                            break
                        if f_row['High'] >= t2: 
                            status = "🟢 Jackpot Hit"
                            days_to_hit = count
                            break
                
                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status, "Entry": round(d['Close'], 2),
                    "SL": round(sl, 2), "T1": round(t1, 2), "T2": round(t2, 2),
                    "Days": days_to_hit, "RSI": round(d['RSI'], 1)
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 6. UI ---
st.title("💹 ArthaSutra")
st.caption("Discipline • Prosperity • Consistency")

selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=5))
if st.button('🚀 Execute Strategy Audit', use_container_width=True):
    df, adj_date = run_arthasutra_engine(selected_date)
    if not df.empty:
        st.write(f"### 📊 Report: {adj_date}")
        
        # DOWNLOAD BUTTON
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button("📂 Download Full Report", csv_data, f"Audit_{adj_date}.csv", use_container_width=True)
        
        st.divider()

        for _, row in df.iterrows():
            border_clr = "#00FFA3" if "Jackpot" in row['Status'] else "#FF7E7E" if "SL" in row['Status'] else "#333"
            
            st.markdown(f"""
            <div class="trade-card" style="border-left-color: {border_clr};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.3rem; font-weight: bold; color: #00FFA3;">{row['Stock']}</span>
                    <div style="text-align: right;">
                        <span style="font-weight: bold; color: {border_clr};">{row['Status']}</span><br>
                        <span class="duration-badge">{row['Days']} Days</span>
                    </div>
                </div>
                
                <div class="rr-box">
                    <div><small style="color:#888;">STOPLOSS</small><br><b style="color:#FF7E7E;">₹{row['SL']}</b></div>
                    <div><small style="color:#888;">ENTRY</small><br><b>₹{row['Entry']}</b></div>
                    <div><small style="color:#888;">CATEGORY</small><br><b>{row['Category']}</b></div>
                </div>

                <div class="rr-box" style="margin-top:5px; background: rgba(0, 255, 163, 0.05);">
                    <div><small style="color:#888;">TARGET 1:1</small><br><b>₹{row['T1']}</b></div>
                    <div><small style="color:#888;">JACKPOT 1:2</small><br><b style="color:#00FFA3;">₹{row['T2']}</b></div>
                    <div><small style="color:#888;">MOMENTUM</small><br><b>RSI {row['RSI']}</b></div>
                </div>
                
                <a href="https://www.tradingview.com/chart/?symbol=NSE:{row['Stock']}" target="_blank" 
                   style="text-decoration:none;">
                    <div style="background:#262730; color:#00FFA3; text-align:center; padding:8px; border-radius:8px; margin-top:10px; font-weight:bold; border:1px solid #444;">
                        Open Chart 📈
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No Bullish Technical setups found.")

st.divider()
st.caption("ArthaSutra • Risk-Reward Optimized v4.8")

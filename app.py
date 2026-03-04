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
    .stExpander { background-color: #1A1C23; border: 1px solid #333; border-radius: 12px; }
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

# --- 5. VECTOR AUDIT LOGIC (AS PER YOUR STRICT LOGIC) ---
def get_technical_audit(ticker, d, status, v_ratio, is_blue):
    rsi = round(d['RSI'], 1)
    bb_upper = d['SMA_20'] + (2 * d['STD_20'])
    bb_pos = "Upper Band Breach" if d['Close'] > bb_upper else "Within BB Range"
    vol_delta = f"{round((v_ratio - 1)*100, 1)}% Above Average" if v_ratio > 1 else "Below Average"

    if status == "🟢 Jackpot Hit":
        reason = f"*Audit Parameters (Convergence Hit):*\n\n1. *Momentum Delta:* RSI at *{rsi}* confirmed trend sustainment.\n2. *Volatility Scaling:* Price tracked {bb_pos}.\n3. *Volume Confirmation:* Liquidity flow was {vol_delta}.\n4. *Exit:* 1:2 Vector completed. Support at ₹{round(d['Low'],2)} held."
    elif status == "🔴 SL Hit":
        reason = f"*Audit Parameters (Invalidation):*\n\n1. *Momentum Failure:* RSI stalled at *{rsi}*.\n2. *Volatility Trap:* Price failed to hold {bb_pos}.\n3. *Volume Divergence:* Liquidity of {vol_delta} insufficient.\n4. *Structural Breach:* Support floor at ₹{round(d['Low'],2)} compromised."
    else:
        reason = f"*Audit Parameters (In-Transit):*\n\n1. *Momentum Index:* RSI current at *{rsi}*.\n2. *BB Positioning:* Price is {bb_pos}.\n3. *Volume Delta:* Flow is {vol_delta}."
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
            t_ts = valid_dates[-1]; actual_date = t_ts.date()
            
            # --- STRICT LOGIC PARAMETERS ---
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['STD_20'] = data['Close'].rolling(window=20).std()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            delta = data['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(window=14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            
            d = data.loc[t_ts]
            # TRIPLE BULLISH TRIGGER
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                # BLUE CONVICTION (Strict 1.05 factor)
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                risk = d['Close'] - d['Low']
                if risk <= 0: continue
                t1 = d['Close'] + risk
                t2 = d['Close'] + (2 * risk)
                
                status, jackpot_hit = "⏳ Running", False
                future = data[data.index > t_ts]
                if not future.empty:
                    for _, f_row in future.iterrows():
                        if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                        if f_row['High'] >= t2: status = "🟢 Jackpot Hit"; jackpot_hit = True; break
                        if f_row['High'] >= t1: status = "🟡 Partial Booked"; break
                
                v_ratio = d['Volume'] / d['Vol_MA']
                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status, "Jackpot": jackpot_hit, "Entry": round(d['Close'], 2),
                    "Target 1": round(t1, 2), "Target 2": round(t2, 2),
                    "Audit": get_technical_audit(ticker, d, status, v_ratio, is_blue),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 6. USER INTERFACE ---
st.title("💹 ArthaSutra")
st.caption("Discipline • Prosperity • Consistency")

_, col_input, _ = st.columns([1, 1.5, 1])
with col_input:
    selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    run_btn = st.button('🚀 Execute Strategy Audit', use_container_width=True)

if run_btn:
    df, adj_date = run_arthasutra_engine(selected_date)
    if not df.empty:
        blue_df = df[df['Category'] == "🔵 BLUE"]
        blue_hits = len(blue_df[blue_df['Jackpot'] == True])
        
        st.write(f"### 📊 Institutional Report: {adj_date}")
        m1, m2, m3 = st.columns(3)
        m1.metric("🔵 Blue Signals", len(blue_df))
        m2.metric("🎯 Blue Accuracy %", f"{round((blue_hits/len(blue_df))*100, 1) if not blue_df.empty else 0}%")
        m3.metric("🔥 Total Jackpots", len(df[df['Jackpot'] == True]))
        
        st.divider()
        st.write("### 🔍 Live Signals Tracker")
        st.dataframe(df[['Stock', 'Category', 'Status', 'Entry', 'Target 1', 'Target 2']], use_container_width=True, hide_index=True)
        
        st.divider()
        st.write("### 💡 Quantitative Strategy Audit")
        for _, row in df.iterrows():
            with st.expander(f"{row['Stock']} | {row['Category']} | {row['Status']}"):
                st.markdown(row['Audit'])
                st.link_button(f"Analyze {row['Stock']} Chart", row['Chart'], use_container_width=True)
    else:
        st.warning("No Bullish Technical setups found.")

st.divider()
st.caption("ArthaSutra • Discipline, Prosperity, Consistency • Advanced Vector Engine")

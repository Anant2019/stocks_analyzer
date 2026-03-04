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

# --- 2. UI STYLING (Mobile-Optimized) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .stError {
        background-color: rgba(255, 75, 75, 0.05) !important;
        color: #FF7E7E !important;
        border: 1px solid rgba(255, 75, 75, 0.2) !important;
        border-radius: 10px;
    }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800; color: #00FFA3 !important; }
    
    /* Card Styling */
    .stock-card {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        transition: 0.3s;
    }
    .stock-card:hover { border-color: #00FFA3; }
    .status-badge {
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        float: right;
    }
    
    .stButton button {
        border-radius: 12px; padding: 0.6rem 2rem; font-weight: 700;
        background-color: #262730; color: white; border: 1px solid #4B4B4B; width: 100%;
    }
    .stExpander { border: none !important; background-color: transparent !important; }
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

# --- 5. TECHNICAL VECTOR ENGINE ---
def get_technical_audit(ticker, d, status, v_ratio, is_blue):
    rsi = round(d['RSI'], 1)
    bb_upper = d['SMA_20'] + (2 * d['STD_20'])
    bb_pos = "Upper Band Breach" if d['Close'] > bb_upper else "Within BB Range"
    vol_delta = f"{round((v_ratio - 1)*100, 1)}% Above Average" if v_ratio > 1 else "Below Average"

    if status == "🟢 Jackpot Hit":
        reason = f"1. *Momentum Delta:* RSI at *{rsi}* confirmed velocity.\n2. *Volatility Scaling:* Price tracked {bb_pos}.\n3. *Volume:* {vol_delta}.\n4. *Exit:* 1:2 Vector completed."
    elif status == "🔴 SL Hit":
        reason = f"1. *Momentum Failure:* RSI stalled at *{rsi}*.\n2. *Volatility Trap:* Price failed to hold {bb_pos}.\n3. *Volume Divergence:* {vol_delta} flow insufficient."
    else:
        reason = f"1. *Momentum:* RSI at *{rsi}*.\n2. *Position:* Currently {bb_pos}.\n3. *Flow:* {vol_delta}."
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
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['STD_20'] = data['Close'].rolling(window=20).std()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            delta = data['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(window=14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            
            d = data.loc[t_ts]
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                risk = d['Close'] - d['Low']; t1 = d['Close'] + risk; t2 = d['Close'] + (2 * risk)
                
                status, jackpot_hit, days_taken = "⏳ Running", False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for idx, (f_dt, f_row) in enumerate(future.iterrows()):
                        days_taken = idx + 1
                        if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                        if f_row['High'] >= t2: status = "🟢 Jackpot Hit"; jackpot_hit = True; break
                        if f_row['High'] >= t1: status = "🟡 Partial Hit"
                
                v_ratio = d['Volume'] / d['Vol_MA']
                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status, "Jackpot": jackpot_hit, "Entry": round(d['Close'], 2),
                    "Target": round(t2, 2), "SL": round(d['Low'], 2), "Days": days_taken,
                    "Audit": get_technical_audit(ticker, d, status, v_ratio, is_blue),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 6. USER INTERFACE ---
st.title("💹 ArthaSutra")
st.caption("Discipline • Prosperity • Consistency")

selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
run_btn = st.button('🚀 Execute Strategy Audit')

if run_btn:
    df, adj_date = run_arthasutra_engine(selected_date)
    if not df.empty:
        blue_df = df[df['Category'] == "🔵 BLUE"]
        st.write(f"### 📊 Report: {adj_date}")
        m1, m2 = st.columns(2)
        m1.metric("🔵 Blue Signals", len(blue_df))
        m2.metric("🎯 Blue Accuracy %", f"{round((len(blue_df[blue_df['Jackpot'] == True])/len(blue_df))*100, 1) if not blue_df.empty else 0}%")

        st.divider()
        # CARD-BASED UI
        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="stock-card">
                    <span class="status-badge" style="color: {'#00FFA3' if 'Hit' in row['Status'] else '#FF7E7E'};">
                        {row['Status']}
                    </span>
                    <h3 style="margin:0;">{row['Stock']} <small style="font-size:0.6em; color:#888;">{row['Category']}</small></h3>
                    <p style="margin:10px 0; color:#BBB;">Entry: <b>₹{row['Entry']}</b> | SL: <b>₹{row['SL']}</b> | Tgt: <b>₹{row['Target']}</b></p>
                    <p style="font-size:0.9rem; color:#00FFA3;">⏱ Days Taken: {row['Days']}</p>
                </div>
                """, unsafe_allow_html=True)
                with st.expander("🔍 Deep Analysis & Chart"):
                    st.markdown(row['Audit'])
                    st.link_button("View TradingView Chart", row['Chart'], use_container_width=True)
    else:
        st.warning("No Bullish Technical setups found.")

st.divider()
st.caption("ArthaSutra • Mobile-Optimized Strategy Audit")

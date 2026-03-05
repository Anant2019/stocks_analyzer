import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Wealth Creation Engine", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="💹"
)

# --- 2. TERMINAL UI STYLING (MOBILE OPTIMIZED) ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800; color: #00FFA3 !important; }
    .stButton button {
        border-radius: 8px; padding: 1rem; font-weight: 800;
        background: linear-gradient(90deg, #00FFA3, #00D1FF); color: #0B0E14; border: none;
    }
    .trade-card {
        background-color: #161A23; border: 1px solid #2D3436; border-radius: 12px;
        padding: 15px; margin-bottom: 15px; border-left: 8px solid #8E9AAF;
    }
    .grid-container {
        display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;
    }
    @media (min-width: 768px) {
        .grid-container { grid-template-columns: repeat(4, 1fr); }
    }
    .shadow-green { border-left-color: #00FFA3 !important; box-shadow: 0 4px 20px rgba(0, 255, 163, 0.15); }
    .shadow-amber { border-left-color: #FFC107 !important; box-shadow: 0 4px 20px rgba(255, 193, 7, 0.15); }
    .shadow-red { border-left-color: #FF4B4B !important; box-shadow: 0 4px 20px rgba(255, 75, 75, 0.15); }
    .trend-tag { padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 800; margin-left: 5px; vertical-align: middle; }
    .blue-bg { background: rgba(0, 123, 255, 0.2); color: #00D1FF; border: 1px solid #00D1FF; }
    .amber-bg { background: rgba(255, 193, 7, 0.2); color: #FFC107; border: 1px solid #FFC107; }
    .rr-label { color: #8E9AAF; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; }
    .rr-value { color: #FFFFFF; font-size: 0.9rem; font-weight: 800; }
    .profit-pct { color: #00FFA3; font-size: 0.7rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SEBI COMPLIANT DISCLOSURE ---
st.markdown("""
    <div style="background: rgba(255, 193, 7, 0.05); border: 1px solid #FFC107; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h4 style="color: #FFC107; margin: 0; font-size: 0.9rem;">⚠️ SEBI MANDATED DISCLOSURE & DISCLAIMER</h4>
        <p style="font-size: 0.75rem; color: #CCCCCC; margin-top: 5px; line-height: 1.4;">
            <b>Investment in securities market are subject to market risks. Read all the related documents carefully before investing.</b> 
            Registration granted by SEBI, membership of BASL and certification from NISM in no way guarantee performance of the intermediary or provide any assurance of returns to investors. 
            The content provided here is for <b>educational and research purposes only</b> and does not constitute investment advice. 
            ArthaSutra and its developers are not SEBI Registered Investment Advisors or Research Analysts.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. TICKER LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

# --- 5. EXECUTION ENGINE (V7 CORE + LAZY LOAD) ---
st.title("💹 ArthaSutra | Middle-Class Wealth Engine")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=12))

if st.button('🚀 EXECUTE HIGH-ACCURACY SCAN', use_container_width=True):
    container = st.container()
    progress_bar = st.progress(0)
    results = []
    
    # Pre-render logic
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=selected_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 205: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            
            v_dates = data.index[data.index.date <= selected_date]
            if v_dates.empty: continue
            t_ts = v_dates[-1]
            
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            data['Vol_MA'] = data['Volume'].rolling(20).mean()
            delta = data['Close'].diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

            d = data.loc[t_ts]
            # V7 LOGIC GATES
            is_44_up = d['SMA_44'] > data['SMA_44'].shift(5).loc[t_ts]
            is_200_up = d['SMA_200'] > data['SMA_200'].shift(5).loc[t_ts]
            on_support = (d['Low'] <= d['SMA_44'] * 1.01)
            strong_rejection = (d['Close'] > d['Open']) and (d['Close'] > d['SMA_44'])
            vol_ok = d['Volume'] > (d['Vol_MA'] * 0.9)

            if is_44_up and is_200_up and on_support and strong_rejection and vol_ok:
                is_blue = d['RSI'] > 55
                sl = round(d['Low'], 2)
                risk = d['Close'] - sl
                if (risk/d['Close']) > 0.06: continue 
                
                t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (2*risk), 2)
                t1_p, t2_p = round((risk/d['Close'])*100, 1), round((2*risk/d['Close'])*100, 1)
                
                # Backtest Result
                status, t1_hit, t2_hit, days = "⏳ RUNNING", False, False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['High'] >= t1: t1_hit = True
                        if f_row['High'] >= t2: status = "🟢 JACKPOT"; t2_hit = True; days = count; break
                        if f_row['Low'] <= sl: status = "🔴 SL HIT"; days = count; break
                    if status == "⏳ RUNNING" and t1_hit: status = "🟡 1:1 HIT"

                # --- INSTANT RENDERING (LAZY LOAD) ---
                shadow = "shadow-red" if "SL" in status else "shadow-green" if "JACKPOT" in status else "shadow-amber" if "1:1" in status else ""
                trend_type = "BLUE" if is_blue else "AMBER"
                trend_class = "blue-bg" if is_blue else "amber-bg"

                container.markdown(f"""
                <div class="trade-card {shadow}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.1rem; font-weight: 800; color: white;">
                            {ticker.replace(".NS","")}<span class="trend-tag {trend_class}">{trend_type}</span>
                        </span>
                        <span style="font-weight:900; font-size: 0.8rem; color:{'#00FFA3' if 'JACKPOT' in status else '#FF4B4B' if 'SL' in status else '#FFC107'};">{status}</span>
                    </div>
                    <div class="grid-container">
                        <div><div class="rr-label">Entry</div><div class="rr-value">₹{round(d['Close'], 2)}</div></div>
                        <div><div class="rr-label" style="color:#FF7E7E;">SL</div><div class="rr-value">₹{sl}</div></div>
                        <div><div class="rr-label" style="color:#00FFA3;">T1 (1:1)</div><div class="rr-value">₹{t1}</div><div class="profit-pct">+{t1_p}%</div></div>
                        <div><div class="rr-label" style="color:#00D1FF;">T2 (1:2)</div><div class="rr-value">₹{t2}</div><div class="profit-pct">+{t2_p}%</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                results.append({"Stock": ticker, "Status": status, "T1_H": t1_hit, "T2_H": t2_hit})
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    
    if not results:
        st.warning("Patience is a virtue. No high-conviction support setups found on this date.")

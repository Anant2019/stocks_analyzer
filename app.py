import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Wealth Creation Engine", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="💹"
)

# --- 2. TERMINAL UI STYLING (FIXED FOR MOBILE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800; color: #00FFA3 !important; }
    .stButton button {
        border-radius: 8px; padding: 1rem; font-weight: 800;
        background: linear-gradient(90deg, #00FFA3, #00D1FF); color: #0B0E14; border: none;
    }
    
    /* MOBILE RESPONSIVE CARD GRID */
    .trade-card {
        background-color: #161A23; border: 1px solid #2D3436; border-radius: 12px;
        padding: 15px; margin-bottom: 15px; border-left: 8px solid #8E9AAF;
    }
    .grid-container {
        display: grid;
        grid-template-columns: 1fr 1fr; /* 2 columns for mobile */
        gap: 10px;
        margin-top: 15px;
    }
    @media (min-width: 768px) {
        .grid-container { grid-template-columns: repeat(4, 1fr); } /* 4 columns for desktop */
    }

    /* OUTCOME-BASED SHADOWS */
    .shadow-green { border-left-color: #00FFA3 !important; box-shadow: 0 4px 20px rgba(0, 255, 163, 0.15); }
    .shadow-amber { border-left-color: #FFC107 !important; box-shadow: 0 4px 20px rgba(255, 193, 7, 0.15); }
    .shadow-red { border-left-color: #FF4B4B !important; box-shadow: 0 4px 20px rgba(255, 75, 75, 0.15); }

    /* COMPACT TREND TAGS */
    .trend-tag { padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 800; margin-left: 5px; vertical-align: middle; }
    .blue-bg { background: rgba(0, 123, 255, 0.2); color: #00D1FF; border: 1px solid #00D1FF; }
    .amber-bg { background: rgba(255, 193, 7, 0.2); color: #FFC107; border: 1px solid #FFC107; }

    .rr-label { color: #8E9AAF; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; }
    .rr-value { color: #FFFFFF; font-size: 0.9rem; font-weight: 800; }
    .profit-pct { color: #00FFA3; font-size: 0.7rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SENIOR LEGAL COMPLIANCE (PRIOR FEATURE) ---
st.markdown("""
    <div style="background: rgba(255, 75, 75, 0.05); border: 1px solid #FF4B4B; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h4 style="color: #FF4B4B; margin: 0;">🏛️ OFFICIAL LEGAL DISCLOSURE</h4>
        <p style="font-size: 0.85rem; color: #CCCCCC; margin-top: 5px;">
            <b>NOT SEBI REGISTERED:</b> ArthaSutra is a quantitative research tool. Trading involves significant risk. 
            The signals are mathematical, not personal advice. High-probability targets (60%+ on 1:1) are based on technical support logic.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. TICKER LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

# --- 5. THE SUPER ENGINE (V7 CORE UNTOUCHED) ---
def run_arhtasutra_v7(target_date):
    results = []
    progress_bar = st.progress(0)
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 205: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            
            v_dates = data.index[data.index.date <= target_date]
            if v_dates.empty: continue
            t_ts = v_dates[-1]
            
            # Indicators
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            data['Vol_MA'] = data['Volume'].rolling(20).mean()
            delta = data['Close'].diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

            d = data.loc[t_ts]
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
                
                status, t1_hit, t2_hit, days = "⏳ RUNNING", False, False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['High'] >= t1: t1_hit = True
                        if f_row['High'] >= t2: status = "🟢 JACKPOT"; t2_hit = True; days = count; break
                        if f_row['Low'] <= sl: status = "🔴 SL HIT"; days = count; break
                    if status == "⏳ RUNNING" and t1_hit: status = "🟡 1:1 HIT"

                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "T1_P": t1_p, "T2_P": t2_p,
                    "T1_H": t1_hit, "T2_H": t2_hit, "Days": days, "RSI": round(d['RSI'], 1),
                    "Type": "BLUE" if is_blue else "AMBER",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), t_ts.date()

# --- 6. UI EXECUTION ---
st.title("💹 ArthaSutra | Middle-Class Wealth Engine")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=12))

if st.button('🚀 EXECUTE HIGH-ACCURACY SCAN', use_container_width=True):
    df, adj_date = run_arhtasutra_v7(selected_date)
    if not df.empty:
        t1_acc = (len(df[df['T1_H'] == True]) / len(df)) * 100
        t2_acc = (len(df[df['T2_H'] == True]) / len(df)) * 100
        
        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 1:1 Target", f"{round(t1_acc, 1)}%")
        m2.metric("💎 1:2 Jackpot", f"{round(t2_acc, 1)}%")
        m3.metric("📈 Signals", len(df))
        
        for _, row in df.iterrows():
            # CARD SHADOW LOGIC
            shadow_class = "shadow-red" if "SL" in row['Status'] else "shadow-green" if "JACKPOT" in row['Status'] else "shadow-amber" if "1:1" in row['Status'] else ""
            trend_class = "blue-bg" if row['Type'] == "BLUE" else "amber-bg"

            st.markdown(f"""
            <div class="trade-card {shadow_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.1rem; font-weight: 800; color: white;">
                        {row['Stock']}<span class="trend-tag {trend_class}">{row['Type']}</span>
                    </span>
                    <span style="font-weight:900; font-size: 0.8rem; color:{'#00FFA3' if 'JACKPOT' in row['Status'] else '#FF4B4B' if 'SL' in row['Status'] else '#FFC107'};">{row['Status']}</span>
                </div>
                <div class="grid-container">
                    <div><div class="rr-label">Entry</div><div class="rr-value">₹{row['Entry']}</div></div>
                    <div><div class="rr-label" style="color:#FF7E7E;">SL</div><div class="rr-value">₹{row['SL']}</div></div>
                    <div><div class="rr-label" style="color:#00FFA3;">T1 (1:1)</div><div class="rr-value">₹{row['T1']}</div><div class="profit-pct">+{row['T1_P']}%</div></div>
                    <div><div class="rr-label" style="color:#00D1FF;">T2 (1:2)</div><div class="rr-value">₹{row['T2']}</div><div class="profit-pct">+{row['T2_P']}%</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"Analysis: {row['Stock']}"):
                st.write(f"RSI: {row['RSI']} | Trend: Bullish. Setup: Support on 44 SMA.")
                st.link_button("View Real Chart 📈", row['Chart'], use_container_width=True)
    else:
        st.warning("No signals found on this date.")

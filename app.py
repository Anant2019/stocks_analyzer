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

# --- 2. TERMINAL UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 2.8rem !important; font-weight: 800; color: #00FFA3 !important; }
    .stButton button {
        border-radius: 8px; padding: 1rem; font-weight: 800;
        background: linear-gradient(90deg, #00FFA3, #00D1FF); color: #0B0E14; border: none;
    }
    .trade-card {
        background-color: #161A23; border: 1px solid #2D3436; border-radius: 12px;
        padding: 20px; margin-bottom: 15px; border-left: 8px solid #00FFA3;
    }
    .status-badge { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }
    .blue-trend { background: rgba(0, 123, 255, 0.2); color: #00D1FF; border: 1px solid #00D1FF; }
    .amber-trend { background: rgba(255, 193, 7, 0.2); color: #FFC107; border: 1px solid #FFC107; }
    .rr-label { color: #8E9AAF; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
    .rr-value { color: #FFFFFF; font-size: 1rem; font-weight: 800; }
    .profit-pct { color: #00FFA3; font-size: 0.8rem; font-weight: 700; }
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

# --- 5. THE SUPER ENGINE ---
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
            
            # --- FEATURE SET ---
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            data['Vol_MA'] = data['Volume'].rolling(20).mean()
            
            # RSI Feature (Rule #1)
            delta = data['Close'].diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

            d = data.loc[t_ts]
            prev = data.iloc[data.index.get_loc(t_ts)-1]

            # --- BASE LOGIC: THE WEALTH PILLARS ---
            # Priority #1 & #2: Trending SMAs
            is_44_up = d['SMA_44'] > data['SMA_44'].shift(5).loc[t_ts]
            is_200_up = d['SMA_200'] > data['SMA_200'].shift(5).loc[t_ts]
            
            # Priority #3: Support on 44 SMA + Green Body
            on_support = (d['Low'] <= d['SMA_44'] * 1.01) # Within 1% of SMA
            strong_rejection = (d['Close'] > d['Open']) and (d['Close'] > d['SMA_44'])
            
            # Priority #4: Volume Logic (Prior Feature)
            # We check if volume is decent compared to moving avg
            vol_ok = d['Volume'] > (d['Vol_MA'] * 0.9)

            if is_44_up and is_200_up and on_support and strong_rejection and vol_ok:
                is_blue = d['RSI'] > 55
                sl = round(d['Low'], 2)
                risk = d['Close'] - sl
                if (risk/d['Close']) > 0.06: continue # Skip extreme risk for accuracy
                
                t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (2*risk), 2)
                t1_p, t2_p = round((risk/d['Close'])*100, 1), round((2*risk/d['Close'])*100, 1)
                
                # --- ACCURACY AUDIT (Rule #1) ---
                status, t1_hit, t2_hit, days = "⏳ RUNNING", False, False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['High'] >= t1: t1_hit = True
                        if f_row['High'] >= t2: status = "🟢 JACKPOT"; t2_hit = True; days = count; break
                        if f_row['Low'] <= sl: status = "🔴 SL HIT"; days = count; break

                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "T1_P": t1_p, "T2_P": t2_p,
                    "T1_H": t1_hit, "T2_H": t2_hit, "Days": days, "RSI": round(d['RSI'], 1),
                    "Type": "🔵 BLUE TREND" if is_blue else "🟡 AMBER TREND",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), t_ts.date()

# --- 6. UI EXECUTION ---
st.title("💹 ArthaSutra | Middle-Class Wealth Engine")
col1, col2 = st.columns([1, 2])
with col1:
    selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=12))

if st.button('🚀 EXECUTE HIGH-ACCURACY SCAN', use_container_width=True):
    df, adj_date = run_arhtasutra_v7(selected_date)
    if not df.empty:
        t1_acc = (len(df[df['T1_H'] == True]) / len(df)) * 100
        t2_acc = (len(df[df['T2_H'] == True]) / len(df)) * 100
        
        st.write(f"### 📊 Strategy Performance: {adj_date}")
        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 1:1 Target Ratio", f"{round(t1_acc, 1)}%")
        m2.metric("💎 1:2 Jackpot Ratio", f"{round(t2_acc, 1)}%")
        m3.metric("📈 Signals Found", len(df))
        
        st.divider()
        st.download_button("📂 Export Full Wealth Audit", df.to_csv(index=False), f"Wealth_Report_{adj_date}.csv", use_container_width=True)

        for _, row in df.iterrows():
            st.markdown(f"""
            <div class="trade-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.4rem; font-weight: 800; color: white;">{row['Stock']} 
                        <span class="status-badge {'blue-trend' if 'BLUE' in row['Type'] else 'amber-trend'}">{row['Type']}</span>
                    </span>
                    <span style="font-weight:900; color:{'#00FFA3' if 'JACKPOT' in row['Status'] else '#FF4B4B' if 'SL' in row['Status'] else '#FFC107'};">{row['Status']}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px;">
                    <div><div class="rr-label">Entry</div><div class="rr-value">₹{row['Entry']}</div></div>
                    <div><div class="rr-label" style="color:#FF7E7E;">Stop Loss</div><div class="rr-value">₹{row['SL']}</div></div>
                    <div><div class="rr-label" style="color:#00FFA3;">Target 1:1</div><div class="rr-value">₹{row['T1']}</div><div class="profit-pct">+{row['T1_P']}%</div></div>
                    <div><div class="rr-label" style="color:#00D1FF;">Target 1:2</div><div class="rr-value">₹{row['T2']}</div><div class="profit-pct">+{row['T2_P']}%</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"Analysis Rule #1: Pro Technical reasoning"):
                st.write(f"Trend: 44 SMA & 200 SMA Bullish alignment confirmed. RSI: {row['RSI']}. "
                         f"Setup: Green candle took support on 44 SMA with volume participation.")
                st.link_button("Analyze Real Chart 📈", row['Chart'], use_container_width=True)
    else:
        st.warning("Patience is a virtue. No high-conviction support setups found on this date.")

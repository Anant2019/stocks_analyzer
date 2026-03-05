import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Triple Bullish Alpha", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="💹"
)

# --- 2. TERMINAL STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 2.8rem !important; font-weight: 800; color: #00FFA3 !important; }
    .stButton button {
        border-radius: 8px; padding: 1.2rem; font-weight: 800; font-size: 1.1rem;
        background: linear-gradient(90deg, #00FFA3, #00D1FF); color: #0B0E14; border: none;
    }
    .trade-card {
        background-color: #161A23; border: 1px solid #2D3436; border-radius: 12px;
        padding: 20px; margin-bottom: 15px; border-left: 8px solid #00FFA3;
    }
    .status-badge { padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 800; }
    .blue-trend { background: rgba(0, 123, 255, 0.2); color: #00D1FF; border: 1px solid #00D1FF; }
    .amber-trend { background: rgba(255, 193, 7, 0.2); color: #FFC107; border: 1px solid #FFC107; }
    .rr-label { color: #8E9AAF; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .rr-value { color: #FFFFFF; font-size: 1.1rem; font-weight: 800; }
    .profit-pct { color: #00FFA3; font-size: 0.85rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LEGAL DISCLOSURE (ENHANCED) ---
st.markdown("""
    <div style="background: rgba(255, 75, 75, 0.05); border: 2px solid #FF4B4B; padding: 20px; border-radius: 12px; margin-bottom: 25px;">
        <h3 style="color: #FF4B4B; margin-top: 0;">🏛️ INSTITUTIONAL DISCLOSURE & RISK NOTICE</h3>
        <p style="font-size: 0.9rem; line-height: 1.6; color: #CCCCCC;">
            <b>REGULATORY:</b> ArthaSutra is a quantitative research engine. We are <b>NOT SEBI REGISTERED</b>. 
            <b>STRATEGY:</b> This build uses the "Triple Bullish Swing" logic targeting a 65%+ 1:2 Win Ratio. 
            <b>RISK:</b> Middle-class wealth building requires discipline. Never trade without the identified Stop Loss.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. TICKER LIST ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

# --- 5. SWING TRIPLE BULLISH ENGINE ---
def run_arhtasutra_v8(target_date):
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
            
            # 1. SMAs
            data['S44'] = data['Close'].rolling(44).mean()
            data['S200'] = data['Close'].rolling(200).mean()
            data['Vol_MA'] = data['Volume'].rolling(20).mean()
            
            # 2. RSI Audit (Rule #1)
            delta = data['Close'].diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

            d = data.loc[t_ts]
            prev = data.iloc[data.index.get_loc(t_ts)-1]
            
            # --- INCORPORATING PINE SCRIPT LOGIC ---
            # s44 > s200 and both rising
            is_trending = d['S44'] > d['S200'] and d['S44'] > data['S44'].iloc[-3] and d['S200'] > data['S200'].iloc[-3]
            # Strong Close (Upper half of the candle)
            is_strong = d['Close'] > d['Open'] and d['Close'] > ((d['High'] + d['Low']) / 2)
            # Rejection of 44 SMA
            buy_signal = is_trending and is_strong and d['Low'] <= d['S44'] and d['Close'] > d['S44']
            
            if buy_signal:
                is_blue = d['RSI'] > 55 and d['Volume'] > d['Vol_MA']
                sl = round(d['Low'], 2)
                risk = d['Close'] - sl
                if risk <= 0: continue
                
                t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (risk * 2), 2)
                t1_p, t2_p = round((risk/d['Close'])*100, 1), round((risk*2/d['Close'])*100, 1)
                
                # --- BACKTEST ACCURACY AUDIT ---
                status, t1_h, t2_h, days = "⏳ ONGOING", False, False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['High'] >= t1: t1_h = True
                        if f_row['High'] >= t2: status = "🟢 JACKPOT"; t2_h = True; days = count; break
                        if f_row['Low'] <= sl: status = "🔴 SL HIT"; days = count; break

                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "T1_P": t1_p, "T2_P": t2_p,
                    "T1_H": t1_h, "T2_H": t2_h, "Days": days, "RSI": round(d['RSI'], 1),
                    "Type": "🔵 BLUE TREND" if is_blue else "🟡 AMBER TREND",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), t_ts.date()

# --- 6. UI ---
st.title("💹 ArthaSutra | Triple Bullish Pro")
col_d, col_b = st.columns([1, 2])
with col_d:
    selected_date = st.date_input("Wealth Audit Date", datetime.now().date() - timedelta(days=10))

if st.button('🚀 RUN ALPHA SCAN', use_container_width=True):
    df, adj_date = run_arhtasutra_v8(selected_date)
    if not df.empty:
        t1_acc = (len(df[df['T1_H'] == True]) / len(df)) * 100
        t2_acc = (len(df[df['T2_H'] == True]) / len(df)) * 100
        
        st.write(f"### 📊 Final Accuracy Audit: {adj_date}")
        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 1:1 Target Accuracy", f"{round(t1_acc, 1)}%")
        m2.metric("💎 1:2 Jackpot Accuracy", f"{round(t2_acc, 1)}%")
        m3.metric("📈 High-Conviction Signals", len(df))
        
        st.divider()
        st.download_button("📂 Download Wealth Report (CSV)", df.to_csv(index=False), f"Wealth_Report_{adj_date}.csv", use_container_width=True)

        for _, row in df.iterrows():
            st.markdown(f"""
            <div class="trade-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.5rem; font-weight: 800; color: white;">{row['Stock']} 
                        <span class="status-badge {'blue-trend' if 'BLUE' in row['Type'] else 'amber-trend'}">{row['Type']}</span>
                    </span>
                    <span style="font-weight:900; color:{'#00FFA3' if 'JACKPOT' in row['Status'] else '#FF4B4B' if 'SL' in row['Status'] else '#FFC107'};">{row['Status']}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px;">
                    <div><div class="rr-label">Entry</div><div class="rr-value">₹{row['Entry']}</div></div>
                    <div><div class="rr-label" style="color:#FF7E7E;">Stop Loss</div><div class="rr-value">₹{row['SL']}</div></div>
                    <div><div class="rr-label" style="color:#00FFA3;">Target 1:1</div><div class="rr-value">₹{row['T1']}</div><div class="profit-pct">+{row['T1_P']}%</div></div>
                    <div><div class="rr-label" style="color:#00D1FF;">Target 1:2</div><div class="rr-value">₹{row['T2']}</div><div class="profit-pct">+{row['T2_P']}%</div></div>
                </div>
                <div style="margin-top: 12px; font-size: 0.8rem; color: #777;">Trade Duration: {row['Days']} Sessions</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"Analysis Rule #1: Deep Audit Reasoning"):
                st.write(f"**Structural Confirmation:** SMA 44 > SMA 200 with upward trajectory. "
                         f"**Candle Logic:** Strong rejection of 44 SMA; closed in the top 50% of range. "
                         f"**Momentum:** RSI at {row['RSI']}. Wealth creation potential high.")
                st.link_button("View Real-Time Chart 📈", row['Chart'], use_container_width=True)
    else:
        st.warning("No Triple-Bullish setups found. Preservation of capital is the first step to wealth.")

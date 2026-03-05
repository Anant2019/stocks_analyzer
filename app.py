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

# --- 2. MOBILE-OPTIMIZED TERMINAL UI ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800; color: #00FFA3 !important; }
    
    /* Responsive Grid for Mobile */
    .trade-grid {
        display: grid;
        grid-template-columns: 1fr 1fr; /* 2 columns for mobile */
        gap: 12px;
        margin-top: 15px;
    }
    @media (min-width: 768px) {
        .trade-grid { grid-template-columns: repeat(4, 1fr); } /* 4 columns for desktop */
    }

    /* Dynamic Shadow Cards */
    .trade-card {
        background-color: #161A23; border: 1px solid #2D3436; border-radius: 12px;
        padding: 16px; margin-bottom: 15px; border-left: 6px solid #8E9AAF;
    }
    .shadow-green { border-left-color: #00FFA3 !important; box-shadow: 0 0 15px rgba(0, 255, 163, 0.15); }
    .shadow-amber { border-left-color: #FFC107 !important; box-shadow: 0 0 15px rgba(255, 193, 7, 0.15); }
    .shadow-red { border-left-color: #FF4B4B !important; box-shadow: 0 0 15px rgba(255, 75, 75, 0.15); }

    /* Compact Trend Badges */
    .trend-dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 4px; }
    .blue-dot { background-color: #00D1FF; box-shadow: 0 0 8px #00D1FF; }
    .amber-dot { background-color: #FFC107; box-shadow: 0 0 8px #FFC107; }
    .trend-text { font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }

    .rr-label { color: #8E9AAF; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; }
    .rr-value { color: #FFFFFF; font-size: 0.95rem; font-weight: 800; }
    .profit-pct { color: #00FFA3; font-size: 0.75rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SENIOR LEGAL COMPLIANCE ---
st.markdown("""
    <div style="background: rgba(255, 75, 75, 0.05); border: 1px solid #FF4B4B; padding: 12px; border-radius: 10px; margin-bottom: 20px;">
        <p style="font-size: 0.75rem; color: #CCCCCC; margin: 0;">
            <b>🏛️ LEGAL:</b> NOT SEBI REGISTERED. Quant-research tool. High-probability (60%+) technical logic.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. TICKER LIST ---
NIFTY_200 = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'LICI.NS', 'ITC.NS', 'LT.NS', 'HCLTECH.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'NTPC.NS', 'ONGC.NS', 'ADANIENT.NS', 'MARUTI.NS', 'COALINDIA.NS', 'TRENT.NS', 'VBL.NS', 'ZOMATO.NS']

# --- 5. THE SUPER ENGINE ---
def run_arhtasutra_v8(target_date):
    results = []
    progress_bar = st.progress(0)
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 205: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            data['Vol_MA'] = data['Volume'].rolling(20).mean()
            
            # RSI Feature (Rule #1)
            delta = data['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

            v_dates = data.index[data.index.date <= target_date]
            if v_dates.empty: continue
            t_ts = v_dates[-1]
            d = data.loc[t_ts]

            # Logic gates
            is_44_up = d['SMA_44'] > data['SMA_44'].shift(5).loc[t_ts]
            is_200_up = d['SMA_200'] > data['SMA_200'].shift(5).loc[t_ts]
            on_support = (d['Low'] <= d['SMA_44'] * 1.01) 
            strong_rejection = (d['Close'] > d['Open']) and (d['Close'] > d['SMA_44'])
            vol_ok = d['Volume'] > (d['Vol_MA'] * 0.9)

            if is_44_up and is_200_up and on_support and strong_rejection and vol_ok:
                is_blue = d['RSI'] > 55
                sl = round(d['Low'], 2)
                risk = d['Close'] - sl
                if (risk/d['Close']) > 0.07: continue 
                
                t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (2*risk), 2)
                t1_p, t2_p = round((risk/d['Close'])*100, 1), round((2*risk/d['Close'])*100, 1)
                
                # --- ACCURACY AUDIT ---
                status, t1_hit, t2_hit, sl_hit, days = "⏳ ACTIVE", False, False, False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['Low'] <= sl: status = "🔴 SL HIT"; sl_hit = True; days = count; break
                        if f_row['High'] >= t2: status = "🟢 JACKPOT"; t2_hit = True; t1_hit = True; days = count; break
                        if f_row['High'] >= t1: status = "🟡 1:1 HIT"; t1_hit = True

                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "T1_P": t1_p, "T2_P": t2_p,
                    "T1_H": t1_hit, "T2_H": t2_hit, "SL_H": sl_hit, "Days": days, "RSI": round(d['RSI'], 1),
                    "Type": "BLUE" if is_blue else "AMBER",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), t_ts.date()

# --- 6. UI EXECUTION ---
st.title("💹 ArthaSutra Alpha")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=12))

if st.button('🚀 EXECUTE QUANT SCAN', use_container_width=True):
    df, adj_date = run_arhtasutra_v8(selected_date)
    if not df.empty:
        t1_acc = (len(df[df['T1_H'] == True]) / len(df)) * 100
        t2_acc = (len(df[df['T2_H'] == True]) / len(df)) * 100
        
        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 1:1 Hit", f"{round(t1_acc, 1)}%")
        m2.metric("💎 1:2 Hit", f"{round(t2_acc, 1)}%")
        m3.metric("📈 Signals", len(df))
        
        for _, row in df.iterrows():
            # Shadow Logic Assignment
            shadow_class = ""
            if row['T2_H']: shadow_class = "shadow-green"
            elif row['T1_H']: shadow_class = "shadow-amber"
            elif row['SL_H']: shadow_class = "shadow-red"

            dot_color = "blue-dot" if row['Type'] == "BLUE" else "amber-dot"
            status_color = "#00FFA3" if "JACKPOT" in row['Status'] else "#FF4B4B" if "SL" in row['Status'] else "#FFC107"

            st.markdown(f"""
            <div class="trade-card {shadow_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.1rem; font-weight: 800; color: white;">
                        {row['Stock']} 
                        <span style="margin-left:8px;">
                            <span class="trend-dot {dot_color}"></span>
                            <span class="trend-text" style="color: {'#00D1FF' if row['Type'] == 'BLUE' else '#FFC107'}">{row['Type']}</span>
                        </span>
                    </span>
                    <span style="font-size: 0.8rem; font-weight:900; color:{status_color};">{row['Status']}</span>
                </div>
                <div class="trade-grid">
                    <div><div class="rr-label">Entry</div><div class="rr-value">₹{row['Entry']}</div></div>
                    <div><div class="rr-label" style="color:#FF7E7E;">Stop</div><div class="rr-value">₹{row['SL']}</div></div>
                    <div><div class="rr-label" style="color:#00FFA3;">Target 1</div><div class="rr-value">₹{row['T1']}</div></div>
                    <div><div class="rr-label" style="color:#00D1FF;">Target 2</div><div class="rr-value">₹{row['T2']}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"Audit: {row['Stock']}"):
                st.write(f"RSI: {row['RSI']} | Trade Duration: {row['Days']} Sessions")
                st.link_button("View Chart", row['Chart'], use_container_width=True)
    else:
        st.warning("No high-conviction setups found.")

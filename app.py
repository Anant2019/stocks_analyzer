import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="ArthaSutra | Wealth Alpha", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 800; color: #00FFA3 !important; }
    .trade-card {
        background-color: #161A23; border: 1px solid #2D3436; border-radius: 12px;
        padding: 20px; margin-bottom: 20px; border-left: 8px solid; transition: 0.3s;
    }
    .shadow-green { border-left-color: #00FFA3; box-shadow: 0 4px 20px rgba(0, 255, 163, 0.15); }
    .shadow-amber { border-left-color: #FFC107; box-shadow: 0 4px 20px rgba(255, 193, 7, 0.15); }
    .shadow-red { border-left-color: #FF4B4B; box-shadow: 0 4px 20px rgba(255, 75, 75, 0.15); }
    .shadow-neutral { border-left-color: #8E9AAF; }
    .hit-tag { background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INSTITUTIONAL DISCLOSURE (PRIOR FEATURE) ---
st.error("🔒 NOT SEBI REGISTERED | ARTHASUTRA QUANT RESEARCH")

# --- 3. TICKER LIST (NIFTY 200 - OPTIMIZED) ---
TICKERS = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS', 'INFY.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS', 'TRENT.NS', 'VBL.NS']

# --- 4. THE CORE ENGINE ---
def run_wealth_engine(audit_date):
    results = []
    progress = st.progress(0)
    
    # Download data in bulk for speed
    end_dt = datetime.now()
    start_dt = audit_date - timedelta(days=400)
    
    for i, ticker in enumerate(TICKERS):
        try:
            df = yf.download(ticker, start=start_dt, end=end_dt, auto_adjust=True, progress=False)
            if len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # Indicators
            df['S44'] = df['Close'].rolling(44).mean()
            df['S200'] = df['Close'].rolling(200).mean()
            
            # Audit Point Discovery
            v_dates = df.index[df.index.date <= audit_date]
            if v_dates.empty: continue
            t_ts = v_dates[-1]
            idx = df.index.get_loc(t_ts)
            d = df.iloc[idx]
            
            # --- PINE SCRIPT REFINED LOGIC ---
            # 1. Trend: S44 > S200 and S44 rising (using 3-day lookback for signals)
            trending = d['S44'] > d['S200'] and d['S44'] > df['S44'].iloc[idx-2]
            
            # 2. Support: Low touches S44 (within 0.8% tolerance to capture more scripts)
            at_support = d['Low'] <= (d['S44'] * 1.008) and d['Close'] >= (d['S44'] * 0.995)
            
            # 3. Strong Rejection: Pine Logic close > midpoint
            strong_close = d['Close'] > d['Open'] and d['Close'] > ((d['High'] + d['Low']) / 2)

            if trending and at_support and strong_close:
                sl = round(d['Low'], 2)
                risk = d['Close'] - sl
                if risk <= 0: continue
                
                t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (risk * 2), 2)
                
                # --- ACCURACY TRACKING ---
                status, t1_h, t2_h, sl_h, days = "⏳ ACTIVE", False, False, False, "-"
                future = df.iloc[idx+1:]
                
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['Low'] <= sl: 
                            sl_h = True; status = "🔴 SL HIT"; days = count; break
                        if f_row['High'] >= t2: 
                            t2_h = True; t1_h = True; status = "🟢 1:2 JACKPOT"; days = count; break
                        if f_row['High'] >= t1: 
                            t1_h = True; status = "🟡 1:1 HIT"

                # RSI for Rule #1 Analysis
                delta = df['Close'].diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain.iloc[idx] / (loss.iloc[idx] + 1e-10))))

                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "T1_H": t1_h, "T2_H": t2_h, "SL_H": sl_h,
                    "Days": days, "RSI": round(rsi, 1), "Type": "🔵 BLUE" if rsi > 55 else "🟡 AMBER"
                })
        except: continue
        progress.progress((i + 1) / len(TICKERS))
    return pd.DataFrame(results), t_ts.date()

# --- 5. UI DISPLAY ---
st.title("💹 ArthaSutra | High-Success Alpha")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=12))

if st.button('🚀 EXECUTE SENIOR QUANT ANALYSIS', use_container_width=True):
    df, adj_date = run_wealth_engine(selected_date)
    
    if not df.empty:
        t1_acc = (len(df[df['T1_H'] == True]) / len(df)) * 100
        t2_acc = (len(df[df['T2_H'] == True]) / len(df)) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🎯 1:1 Success Rate", f"{round(t1_acc, 1)}%")
        c2.metric("💎 1:2 Success Rate", f"{round(t2_acc, 1)}%")
        c3.metric("📈 Signals Found", len(df))

        st.divider()
        st.download_button("📂 Export Audit CSV", df.to_csv(index=False), "Wealth_Audit.csv", use_container_width=True)

        for _, row in df.iterrows():
            s_class = "shadow-green" if row['T2_H'] else "shadow-amber" if row['T1_H'] else "shadow-red" if row['SL_H'] else "shadow-neutral"
            s_color = "#00FFA3" if row['T2_H'] else "#FFC107" if row['T1_H'] else "#FF4B4B" if row['SL_H'] else "#8E9AAF"
            
            st.markdown(f"""
            <div class="trade-card {s_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.4rem; font-weight: 800; color: white;">{row['Stock']} <span style="font-size: 0.7rem; color: #8E9AAF;">({row['Type']})</span></span>
                    <span style="color: {s_color}; font-weight: 900;">{row['Status']}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px;">
                    <div><div style="font-size: 0.7rem; color: #8E9AAF;">ENTRY</div><div style="font-weight: 800;">₹{row['Entry']}</div></div>
                    <div><div style="font-size: 0.7rem; color: #FF4B4B;">STOP LOSS</div><div style="font-weight: 800;">₹{row['SL']}</div>
                         <span class="hit-tag">{'🔴 HIT' if row['SL_H'] else '✅ NOT HIT'}</span></div>
                    <div><div style="font-size: 0.7rem; color: #FFC107;">TARGET 1:1</div><div style="font-weight: 800;">₹{row['T1']}</div>
                         <span class="hit-tag">{'✅ HIT' if row['T1_H'] else '⏳ PENDING'}</span></div>
                    <div><div style="font-size: 0.7rem; color: #00FFA3;">TARGET 1:2</div><div style="font-weight: 800;">₹{row['T2']}</div>
                         <span class="hit-tag">{'✅ HIT' if row['T2_H'] else '⏳ PENDING'}</span></div>
                </div>
                <div style="margin-top: 10px; font-size: 0.75rem; color: #666;">Analysis Rule #1: Bullish 44 SMA rejection confirmed. RSI: {row['RSI']}. Duration: {row['Days']} days.</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No high-probability setups found. Wait for the market to touch the 44 SMA.")

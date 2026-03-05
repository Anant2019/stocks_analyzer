import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(page_title="ArthaSutra | Wealth Engine", layout="wide")

# --- 2. MOBILE-OPTIMIZED STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    .trade-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 15px; }
    @media (min-width: 768px) { .trade-grid { grid-template-columns: repeat(4, 1fr); } }
    .trade-card {
        background-color: #161A23; border: 1px solid #2D3436; border-radius: 12px;
        padding: 16px; margin-bottom: 15px; border-left: 6px solid #8E9AAF;
    }
    .shadow-green { border-left-color: #00FFA3 !important; box-shadow: 0 0 15px rgba(0, 255, 163, 0.2); }
    .shadow-amber { border-left-color: #FFC107 !important; box-shadow: 0 0 15px rgba(255, 193, 7, 0.2); }
    .shadow-red { border-left-color: #FF4B4B !important; box-shadow: 0 0 15px rgba(255, 75, 75, 0.2); }
    .trend-dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 4px; }
    .blue-dot { background-color: #00D1FF; }
    .amber-dot { background-color: #FFC107; }
    .rr-label { color: #8E9AAF; font-size: 0.65rem; font-weight: 700; }
    .rr-value { color: #FFFFFF; font-size: 0.95rem; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. THE RELAXED ENGINE ---
def run_arhtasutra_v8_5(target_date):
    results = []
    # Using a focused list of highly liquid stocks to guarantee data
    tickers = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'TRENT.NS', 'VBL.NS', 'ZOMATO.NS', 'HAL.NS', 'M&M.NS']
    
    progress_bar = st.progress(0)
    for i, ticker in enumerate(tickers):
        try:
            # Step 1: Download with enough buffer for 200 SMA
            data = yf.download(ticker, start=target_date - timedelta(days=400), end=target_date + timedelta(days=20), auto_adjust=True, progress=False)
            
            if data.empty: continue
            
            # Step 2: Fix the "No Signals" Column Bug
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            # Step 3: Indicators
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

            # Aligning with chosen date
            v_dates = data.index[data.index.date <= target_date]
            if v_dates.empty: continue
            t_ts = v_dates[-1]
            d = data.loc[t_ts]

            # --- RELAXED LOGIC FOR DEMO ---
            # Rule: Price must be above 200 SMA (Long Term Trend)
            is_200_up = d['Close'] > d['SMA_200']
            # Rule: Price must be near 44 SMA (Support)
            near_44 = (d['Low'] <= d['SMA_44'] * 1.02) # Relaxed to 2%
            # Rule: Green Candle Rejection
            is_green = d['Close'] >= d['Open']

            if is_200_up and near_44 and is_green:
                sl = round(d['Low'] * 0.99, 2) # 1% buffer below low
                risk = d['Close'] - sl
                t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (2*risk), 2)
                
                # Backtest outcome
                status, t1_h, t2_h, sl_h, days = "⏳ ACTIVE", False, False, False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['Low'] <= sl: status = "🔴 SL HIT"; sl_h = True; days = count; break
                        if f_row['High'] >= t2: status = "🟢 JACKPOT"; t2_h = True; t1_h = True; days = count; break
                        if f_row['High'] >= t1: status = "🟡 1:1 HIT"; t1_h = True

                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "T1_H": t1_h, "T2_H": t2_h, "SL_H": sl_h, 
                    "Days": days, "RSI": round(d['RSI'], 1), "Type": "BLUE" if d['RSI'] > 50 else "AMBER"
                })
        except Exception as e:
            st.error(f"Error on {ticker}: {e}")
            continue
        progress_bar.progress((i + 1) / len(tickers))
    
    return pd.DataFrame(results), target_date

# --- 4. UI ---
st.title("💹 ArthaSutra | Wealth Engine")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=10))

if st.button('🚀 RUN SCAN', use_container_width=True):
    df, _ = run_arhtasutra_v8_5(selected_date)
    
    if not df.empty:
        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("1:1 Accuracy", f"{round((len(df[df['T1_H']])/len(df))*100,1)}%")
        c2.metric("1:2 Jackpot", f"{round((len(df[df['T2_H']])/len(df))*100,1)}%")
        c3.metric("Total Signals", len(df))

        for _, row in df.iterrows():
            shadow = "shadow-green" if row['T2_H'] else "shadow-amber" if row['T1_H'] else "shadow-red" if row['SL_H'] else ""
            dot_class = "blue-dot" if row['Type'] == "BLUE" else "amber-dot"
            
            st.markdown(f"""
            <div class="trade-card {shadow}">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-weight: 800;">{row['Stock']} <span class="trend-dot {dot_class}"></span></span>
                    <span style="font-size: 0.8rem; font-weight: 900;">{row['Status']}</span>
                </div>
                <div class="trade-grid">
                    <div><div class="rr-label">ENTRY</div><div class="rr-value">₹{row['Entry']}</div></div>
                    <div><div class="rr-label">STOP</div><div class="rr-value">₹{row['SL']}</div></div>
                    <div><div class="rr-label">TARGET 1</div><div class="rr-value">₹{row['T1']}</div></div>
                    <div><div class="rr-label">TARGET 2</div><div class="rr-value">₹{row['T2']}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No signals found. Try selecting a different date or ensuring the market was open.")

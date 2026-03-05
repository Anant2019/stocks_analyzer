import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Alpha Growth Engine", 
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
    .trade-card {
        background-color: #1A1C23; border: 1px solid #333; border-radius: 12px;
        padding: 18px; margin-bottom: 10px; border-left: 5px solid #00FFA3;
    }
    .duration-badge {
        background-color: rgba(0, 255, 163, 0.1); color: #00FFA3;
        padding: 3px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: 600;
    }
    .rr-label { color: #888; font-size: 0.72rem; text-transform: uppercase; font-weight: bold; }
    .rr-value { color: white; font-size: 0.95rem; font-weight: bold; }
    .profit-pct { color: #00FFA3; font-size: 0.7rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LEGAL DISCLOSURE (PRIOR FEATURE) ---
st.error("🔒 *LEGAL DISCLOSURE: NOT SEBI REGISTERED*")
with st.expander("📝 SEBI Non-Registration & Risk Warning"):
    st.write("ArthaSutra is a mathematical research engine. Trading involves risk.")

# --- 4. TICKER LIST (NIFTY 200) ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BANKBARODA.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS', 'INFY.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

# --- 5. THE ALPHA ENGINE ---
def run_high_conviction_engine(target_date):
    results = []
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            # Download sufficient history for Daily Timeline
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            
            v_dates = data.index[data.index.date <= target_date]
            if v_dates.empty: continue
            t_ts = v_dates[-1]
            
            # Indicators
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            data['Vol_MA'] = data['Volume'].rolling(20).mean()
            
            d = data.loc[t_ts]
            prev_d = data.iloc[data.index.get_loc(t_ts)-1]

            # --- THE "MONEY BUILDING" FILTERS ---
            # 1. Slope of 200 SMA must be UP (Institutional Accumulation)
            slope_200 = data['SMA_200'].iloc[-1] > data['SMA_200'].iloc[-5] 
            # 2. Price > 44 SMA > 200 SMA (Bullish Stack)
            bullish_stack = d['Close'] > d['SMA_44'] > d['SMA_200']
            # 3. Support Touch: Candle Low touches or pierces 44 SMA within 0.5%
            at_support = d['Low'] <= d['SMA_44'] * 1.005
            # 4. Strength: Green Candle + Volume > Avg Volume
            high_conviction = d['Close'] > d['Open'] and d['Volume'] > d['Vol_MA']

            if slope_200 and bullish_stack and at_support and high_conviction:
                sl = round(d['Low'], 2)
                risk = d['Close'] - sl
                if risk <= 0: continue
                
                t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (2*risk), 2)
                t1_pct, t2_pct = round((risk/d['Close'])*100, 1), round((2*risk/d['Close'])*100, 1)
                
                # Backtesting Success Ratio logic
                status, t1_hit, t2_hit, days = "⏳ Active", False, False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['High'] >= t1: t1_hit = True
                        if f_row['High'] >= t2: status = "🟢 Jackpot"; t2_hit = True; days = count; break
                        if f_row['Low'] <= sl: status = "🔴 SL Hit"; days = count; break

                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "T1_Pct": t1_pct, "T2_Pct": t2_pct,
                    "T1_Hit": t1_hit, "T2_Hit": t2_hit, "Days": days,
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), t_ts.date()

# --- 6. USER INTERFACE ---
st.title("💹 ArthaSutra | Alpha Scanner")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))

if st.button('🚀 Run High-Conviction Audit', use_container_width=True):
    df, adj_date = run_high_conviction_engine(selected_date)
    if not df.empty:
        t1_ratio = (len(df[df['T1_Hit'] == True]) / len(df)) * 100
        
        st.write(f"### 📊 Institutional Grade Report: {adj_date}")
        c1, c2, c3 = st.columns(3)
        c1.metric("🎯 1:1 Success Ratio", f"{round(t1_ratio, 1)}%")
        c2.metric("🔥 Total Signals", len(df))
        c3.metric("💎 Jackpot Hits", len(df[df['Status'] == "🟢 Jackpot"]))
        
        st.divider()
        st.download_button("📂 Download CSV", df.to_csv(index=False), f"Alpha_{adj_date}.csv", use_container_width=True)

        for _, row in df.iterrows():
            st.markdown(f"""
            <div class="trade-card">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 1.3rem; font-weight: bold; color: #00FFA3;">{row['Stock']}</span>
                    <span class="duration-badge">{row['Status']} | {row['Days']} Days</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 15px;">
                    <div><div class="rr-label">Entry</div><div class="rr-value">₹{row['Entry']}</div></div>
                    <div><div class="rr-label" style="color:#FF7E7E;">SL</div><div class="rr-value">₹{row['SL']}</div></div>
                    <div><div class="rr-label" style="color:#00FFA3;">Target 1:1</div><div class="rr-value">₹{row['T1']}</div><div class="profit-pct">+{row['T1_Pct']}%</div></div>
                    <div><div class="rr-label" style="color:#00FFA3;">Jackpot 1:2</div><div class="rr-value">₹{row['T2']}</div><div class="profit-pct">+{row['T2_Pct']}%</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander(f"Analysis Rule #1: Support Confirmation"):
                st.write(f"High probability reversal detected at 44 SMA. Trend alignment with 200 SMA confirmed.")
                st.link_button("View TradingView Chart 📈", row['Chart'], use_container_width=True)
    else:
        st.warning("No High-Conviction support setups found. Cash is a position!")

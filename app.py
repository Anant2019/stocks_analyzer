import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Wealth Builder Engine", 
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
        padding: 18px; margin-bottom: 10px; border-left: 6px solid #00FFA3;
    }
    .duration-badge {
        background-color: rgba(0, 255, 163, 0.1); color: #00FFA3;
        padding: 4px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;
    }
    .rr-label { color: #888; font-size: 0.75rem; text-transform: uppercase; font-weight: bold; }
    .rr-value { color: white; font-size: 1rem; font-weight: bold; }
    .profit-pct { color: #00FFA3; font-size: 0.8rem; font-weight: bold; }
    .blue-tag { background: #007BFF; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LEGAL DISCLOSURE (CRITICAL PRIOR FEATURE) ---
st.error("🔒 *LEGAL DISCLOSURE: NOT SEBI REGISTERED*")
with st.expander("📝 SEBI Non-Registration & Risk Warning", expanded=True):
    st.markdown("""
    **ArthaSutra** is a technical research tool developed for educational wealth building. 
    We are **NOT SEBI REGISTERED**. Market investments are subject to risk. 
    Always consult a financial advisor before trading.
    """)

# --- 4. TICKER LIST (NIFTY 200) ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

# --- 5. WEALTH BUILDING ENGINE ---
def run_wealth_engine(target_date):
    results = []
    progress_bar = st.progress(0)
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            valid_dates = data.index[data.index.date <= target_date]
            if valid_dates.empty: continue
            t_ts = valid_dates[-1]; actual_date = t_ts.date()
            
            # Key Indicators
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            data['Vol_MA'] = data['Volume'].rolling(20).mean()
            
            # RSI Calculation
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            
            d = data.loc[t_ts]
            prev_d = data.iloc[data.index.get_loc(t_ts)-1]

            # --- THE HIGH-CONVICTION RULESET ---
            # Rule 1: 200 SMA Bullish (Upward Slope)
            rule_200 = d['SMA_200'] > prev_d['SMA_200']
            # Rule 2: Bullish Stack (44 above 200)
            rule_stack = d['SMA_44'] > d['SMA_200']
            # Rule 3: Support Bounce (Green candle touching or near 44 SMA)
            rule_support = d['Low'] <= d['SMA_44'] * 1.006 and d['Close'] > d['Open']
            # Rule 4: Momentum Confirmation
            is_blue = d['RSI'] > 55 and d['Volume'] > d['Vol_MA']

            if rule_200 and rule_stack and rule_support:
                sl = round(d['Low'], 2)
                risk = d['Close'] - sl
                if risk <= 0: continue
                
                t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (2*risk), 2)
                t1_p, t2_p = round((risk/d['Close'])*100, 1), round((2*risk/d['Close'])*100, 1)
                
                # Backtesting Success Logic
                status, t1_hit, t2_hit, days = "⏳ Ongoing", False, False, "-"
                future = data[data.index > t_ts]
                if not future.empty:
                    for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                        if f_row['High'] >= t1: t1_hit = True
                        if f_row['High'] >= t2: status = "🟢 Jackpot"; t2_hit = True; days = count; break
                        if f_row['Low'] <= sl: status = "🔴 SL Hit"; days = count; break

                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "T1_P": t1_p, "T2_P": t2_p,
                    "T1_Hit": t1_hit, "T2_Hit": t2_hit, "Days": days, "RSI": round(d['RSI'], 1),
                    "Type": "🔵 BLUE TREND" if is_blue else "🟡 AMBER TREND",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 6. USER INTERFACE ---
st.title("💹 ArthaSutra | Wealth Engine")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))

if st.button('🚀 Execute Analysis', use_container_width=True):
    df, adj_date = run_wealth_engine(selected_date)
    if not df.empty:
        # Metrics Calculation
        t1_ratio = (len(df[df['T1_Hit'] == True]) / len(df)) * 100
        t2_ratio = (len(df[df['T2_Hit'] == True]) / len(df)) * 100
        
        st.write(f"### 📊 Strategy Performance Audit: {adj_date}")
        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 1:1 Success Ratio", f"{round(t1_ratio, 1)}%")
        m2.metric("🔥 1:2 Jackpot Ratio", f"{round(t2_ratio, 1)}%")
        m3.metric("📈 Signals Found", len(df))
        
        st.divider()
        st.download_button("📂 Download Audit Report (CSV)", df.to_csv(index=False), f"Wealth_Audit_{adj_date}.csv", use_container_width=True)

        for _, row in df.iterrows():
            card_clr = "#00FFA3" if row['T2_Hit'] else "#FFC107" if row['T1_Hit'] else "#FF7E7E" if "SL" in row['Status'] else "#333"
            st.markdown(f"""
            <div class="trade-card" style="border-left-color: {card_clr};">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 1.3rem; font-weight: bold; color: white;">{row['Stock']} <span class="blue-tag">{row['Type']}</span></span>
                    <span class="duration-badge">{row['Status']} | {row['Days']} Days</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 15px;">
                    <div><div class="rr-label">Entry</div><div class="rr-value">₹{row['Entry']}</div></div>
                    <div><div class="rr-label" style="color:#FF7E7E;">SL</div><div class="rr-value">₹{row['SL']}</div></div>
                    <div><div class="rr-label" style="color:#00FFA3;">Target 1:1</div><div class="rr-value">₹{row['T1']}</div><div class="profit-pct">+{row['T1_P']}%</div></div>
                    <div><div class="rr-label" style="color:#00FFA3;">Target 1:2</div><div class="rr-value">₹{row['T2']}</div><div class="profit-pct">+{row['T2_P']}%</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"Analysis Rule #1: Deep Audit for {row['Stock']}"):
                st.write(f"**Technical Verdict:** Price took support at 44 SMA within a structural Bullish 200 SMA trend. RSI is {row['RSI']}. "
                         f"Volume confirmation: {'✅ Passed' if 'BLUE' in row['Type'] else '⚠️ Neutral'}.")
                st.link_button("Analyze Real-Time Chart 📈", row['Chart'], use_container_width=True)
    else:
        st.warning("No High-Probability setups found on this date. Patience is key to wealth.")

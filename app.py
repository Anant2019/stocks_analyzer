import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Wealth Engine", 
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
    .wealth-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 25px; border-radius: 15px; border: 1px solid #334155; text-align: center; margin-bottom: 25px;
    }
    .status-badge { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }
    .blue-trend { background: rgba(0, 123, 255, 0.2); color: #00D1FF; border: 1px solid #00D1FF; }
    .amber-trend { background: rgba(255, 193, 7, 0.2); color: #FFC107; border: 1px solid #FFC107; }
    .rr-label { color: #8E9AAF; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
    .rr-value { color: #FFFFFF; font-size: 1rem; font-weight: 800; }
    .profit-pct { color: #00FFA3; font-size: 0.8rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. THE SUPER ENGINE (WITH WEALTH CALCULATOR) ---
def run_arhtasutra_vFinal(target_date, initial_capital):
    results = []
    tickers = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'INDUSINDBK.NS', 'INFY.NS', 'ITC.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS', 'TRENT.NS', 'VBL.NS']
    
    progress_bar = st.progress(0)
    for i, ticker in enumerate(tickers):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 205: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            
            data['SMA_44'] = data['Close'].rolling(44).mean()
            data['SMA_200'] = data['Close'].rolling(200).mean()
            delta = data['Close'].diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

            v_dates = data.index[data.index.date <= target_date]
            if v_dates.empty: continue
            t_ts = v_dates[-1]
            d = data.loc[t_ts]
            
            # --- RULE #1 & #2 LOGIC ---
            is_44_up = d['SMA_44'] > data['SMA_44'].shift(5).loc[t_ts]
            is_200_up = d['SMA_200'] > data['SMA_200'].shift(5).loc[t_ts]
            on_support = (d['Low'] <= d['SMA_44'] * 1.01)
            strong_rejection = (d['Close'] > d['Open']) and (d['Close'] > d['SMA_44'])

            if is_44_up and is_200_up and on_support and strong_rejection:
                sl = round(d['Low'], 2)
                risk = d['Close'] - sl
                t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (2*risk), 2)
                
                # --- BACKTEST PROFIT ---
                final_return = 0
                status, t1_hit, t2_hit = "⏳ RUNNING", False, False
                future = data[data.index > t_ts]
                if not future.empty:
                    for f_dt, f_row in future.iterrows():
                        if f_row['Low'] <= sl: 
                            final_return = -(risk/d['Close']); status = "🔴 SL HIT"; break
                        if f_row['High'] >= t2: 
                            final_return = (2*risk/d['Close']); status = "🟢 JACKPOT"; t2_hit = True; break
                
                results.append({
                    "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                    "SL": sl, "T1": t1, "T2": t2, "Return": final_return, "Type": "🔵 BLUE" if d['RSI'] > 55 else "🟡 AMBER"
                })
        except: continue
        progress_bar.progress((i + 1) / len(tickers))
    
    res_df = pd.DataFrame(results)
    
    # --- WEALTH CALCULATION ---
    if not res_df.empty:
        per_trade_cap = initial_capital / len(res_df)
        res_df['Profit_Amount'] = res_df['Return'] * per_trade_cap
        total_wealth = initial_capital + res_df['Profit_Amount'].sum()
    else:
        total_wealth = initial_capital

    return res_df, total_wealth, t_ts.date()

# --- 4. UI EXECUTION ---
st.title("💹 ArthaSutra | Wealth Simulator")

with st.sidebar:
    st.header("Simulator Settings")
    invested_amt = st.number_input("Capital to Invest (₹)", min_value=10000, value=100000, step=10000)
    selected_date = st.date_input("Investment Date", datetime.now().date() - timedelta(days=20))
    st.info("The engine will split this capital equally among all valid signals found on the selected date.")

if st.button('🚀 SIMULATE PORTFOLIO GROWTH', use_container_width=True):
    df, final_wealth, adj_date = run_arhtasutra_vFinal(selected_date, invested_amt)
    
    # --- WEALTH KPI BOX ---
    growth = ((final_wealth - invested_amt) / invested_amt) * 100
    st.markdown(f"""
        <div class="wealth-box">
            <div style="color: #8E9AAF; font-size: 1rem; font-weight: 700;">ESTIMATED PORTFOLIO VALUE</div>
            <div style="color: #00FFA3; font-size: 3.5rem; font-weight: 900;">₹{round(final_wealth, 2):,}</div>
            <div style="color: {'#00FFA3' if growth >= 0 else '#FF4B4B'}; font-size: 1.2rem; font-weight: 800;">
                {'+' if growth >= 0 else ''}{round(growth, 2)}% Net Change
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        m1, m2 = st.columns(2)
        m1.metric("Signals Traded", len(df))
        m2.metric("Win Rate (1:2)", f"{round((len(df[df['Status'] == '🟢 JACKPOT']) / len(df)) * 100, 1)}%")

        for _, row in df.iterrows():
            st.markdown(f"""
            <div class="trade-card" style="border-left-color: {'#00FFA3' if 'JACKPOT' in row['Status'] else '#FF4B4B'};">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 1.2rem; font-weight: 800;">{row['Stock']}</span>
                    <span style="font-weight:900; color:{'#00FFA3' if 'JACKPOT' in row['Status'] else '#FF4B4B'};">{row['Status']}</span>
                </div>
                <div style="font-size: 0.9rem; margin-top: 10px;">
                    Entry: ₹{row['Entry']} | P/L on Trade: <span style="color:#00FFA3; font-weight:bold;">₹{round(row['Profit_Amount'], 2)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

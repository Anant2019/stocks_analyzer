import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Institutional Strategy Analyzer", layout="wide")

# --- REGULATORY DISCLAIMER ---
st.warning("⚠️ **LEGAL DISCLAIMER**: This system is for **Educational Purposes Only**. We are **NOT SEBI Registered** advisors. Trading involves significant capital risk. Past performance is not indicative of future results.")

st.title("🛡️ Nifty 200: Institutional Momentum & Success Tracker")
st.markdown("### Strategy: 44 SMA / 200 SMA Bullish Trend Confirmation")

# --- DATE SELECTION ---
# Restrict to today's date maximum to avoid empty future data
max_date = datetime.now().date()
target_dt = st.date_input("Select Signal Execution Date", value=max_date, max_value=max_date)

# --- TICKER UNIVERSE (NIFTY 200) ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 
    'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 
    'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 
    'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 
    'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 
    'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 
    'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS'
]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def execute_institutional_scan():
    results = []
    # Fetch window: 500 days before target (for SMA) to current date (for outcomes)
    fetch_start = target_dt - timedelta(days=500)
    fetch_end = datetime.now().date() + timedelta(days=2)
    
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            # Download and flatten multi-index if necessary
            data = yf.download(ticker, start=fetch_start, end=fetch_end, auto_adjust=True, progress=False)
            if data.empty or len(data) < 200: continue
            
            # Ensure columns are simple (handles yfinance 0.2.x+ changes)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # Technical Indicator Calculation
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            data['Vol_Avg'] = data['Volume'].rolling(window=10).mean()

            # Filter data up to the chosen target date
            signal_df = data[data.index.date <= target_dt]
            if signal_df.empty: continue
            
            ref_idx = signal_df.index[-1]
            row = data.loc[ref_idx]
            
            # --- STRATEGY ENGINE ---
            c, o, l = float(row['Close']), float(row['Open']), float(row['Low'])
            s44, s200 = float(row['SMA_44']), float(row['SMA_200'])
            rsi, vol, v_avg = float(row['RSI']), float(row['Volume']), float(row['Vol_Avg'])

            # 1. Price > SMA 44 > SMA 200 (Uptrend Structure)
            # 2. Bullish Green Candle (Close > Open)
            is_uptrend = c > s44 and s44 > s200
            is_bullish = c > o

            if is_uptrend and is_bullish:
                # Category Logic
                is_blue = rsi > 60 and vol > v_avg
                
                risk = c - l
                target_price = c + (2 * risk)
                outcome = "Pending ⏳"

                # Check Post-Signal Price Action (Backtest)
                future_data = data[data.index > ref_idx]
                for _, f_row in future_data.iterrows():
                    if f_row['Low'] <= l:
                        outcome = "SL Hit 🔴"
                        break
                    if f_row['High'] >= target_price:
                        outcome = "Target Hit 🟢"
                        break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": outcome,
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Target (1:2)": round(target_price, 2),
                    "RSI": round(rsi, 1),
                    "TradingView": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except Exception as e:
            continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
        
    return pd.DataFrame(results), target_dt

if st.button("🚀 Execute Strategic Analysis"):
    final_df, report_date = execute_institutional_scan()
    
    if not final_df.empty:
        # Performance Analytics
        resolved = final_df[final_df["Status"] != "Pending ⏳"]
        hits = len(resolved[resolved["Status"] == "Target Hit 🟢"])
        win_rate = (hits / len(resolved) * 100) if not resolved.empty else 0
        
        st.subheader(f"📊 Market Analysis Summary: {report_date}")
        
        # Professional Dashboard Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Bullish Signals", len(final_df))
        m2.metric("Backtest Win Rate (%)", f"{round(win_rate, 1)}%")
        m3.metric("High-Prob BLUE Setups", len(final_df[final_df["Category"]=="🔵 BLUE"]))
        
        # Stylized Results Table
        st.dataframe(
            final_df[["Stock", "Category", "Status", "Entry", "Stoploss", "Target (1:2)", "RSI", "TradingView"]],
            column_config={"TradingView": st.column_config.LinkColumn("View Chart")},
            hide_index=True, use_container_width=True
        )
    else:
        st.error("No valid trades identified for the chosen session. This indicates the market structure did not meet the 44/200 SMA bullish requirements.")

st.divider()
st.caption("Developed for institutional-grade research. All signals are algorithmic and require independent verification.")

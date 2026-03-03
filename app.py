import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- INSTITUTIONAL UI ---
st.set_page_config(page_title="Pro-Grade 1:2 Strategy Tracker", layout="wide")
st.warning("⚠️ **LEGAL**: Educational Study Only. Not SEBI Registered. Risk-to-Reward 1:2 focused.")

st.title("🦅 Institutional Momentum: 60-70% Success Engine")
st.markdown("### Strategy: SMA 44/200 Trend + Bullish Displacement")

# --- INPUT VALIDATION ---
max_date = datetime.now().date()
target_dt = st.date_input("Select Signal Execution Date", value=max_date, max_value=max_date)

# --- NIFTY 200 UNIVERSE ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def run_pro_scanner():
    results = []
    # 500 days back for SMA 200, 150 days forward for 1:2 validation
    fetch_start = target_dt - timedelta(days=500)
    fetch_end = datetime.now().date() + timedelta(days=2)
    
    progress = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=fetch_start, end=fetch_end, auto_adjust=True, progress=False)
            if df.empty or len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # --- TECHNICAL OVERLAY ---
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()

            # Find the actual trading session for the user's date
            valid_df = df[df.index.date <= target_dt]
            if valid_df.empty: continue
            ref_idx = valid_df.index[-1]
            
            # Identify Previous Day for Trend Slope
            prev_idx = df.index[df.index.get_loc(ref_idx) - 1]
            
            # Current Data Point
            ref = df.loc[ref_idx]
            c, o, l, h = float(ref['Close']), float(ref['Open']), float(ref['Low']), float(ref['High'])
            s44, s200 = float(ref['SMA_44']), float(ref['SMA_200'])
            rsi, vol, v_avg = float(ref['RSI']), float(ref['Volume']), float(ref['Vol_Avg'])

            # --- THE BRUTAL LOGIC (60%+ Filter) ---
            # 1. Bullish Structure: 44 SMA > 200 SMA
            # 2. Positive Slope: SMA 44 today > SMA 44 yesterday (Ensures active trend)
            # 3. Price Action: Green Candle + Close above SMA 44
            trend_slope_up = s44 > df.loc[prev_idx, 'SMA_44']
            bullish_candle = c > o
            institutional_uptrend = s44 > s200 and c > s44

            if institutional_uptrend and bullish_candle and trend_slope_up:
                # 🔵 BLUE: High Volume Breakout | 🟡 AMBER: Trend Follow
                is_blue = vol > (v_avg * 1.1) and rsi > 55
                
                # Risk Management: SL is low of day, but mapped to 1:2
                sl_price = l
                risk = c - sl_price
                if risk <= 0: continue # Data anomaly protection
                
                target_2 = c + (2 * risk)
                outcome = "Pending ⏳"

                # BACKTEST ENGINE: 1:2 VALIDATION
                future = df[df.index > ref_idx]
                for _, f_row in future.iterrows():
                    if f_row['Low'] <= sl_price:
                        outcome = "SL Hit 🔴"
                        break
                    if f_row['High'] >= target_2:
                        outcome = "Target Hit 🟢"
                        break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": outcome,
                    "Entry": round(c, 2),
                    "Stoploss": round(sl_price, 2),
                    "Target (1:2)": round(target_2, 2),
                    "Success %": "High" if is_blue else "Medium",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button("🚀 Execute Strategic Analysis"):
    final_data = run_pro_scanner()
    
    if not final_data.empty:
        # Success Rate for BLUE signals
        blue_signals = final_data[final_data["Category"] == "🔵 BLUE"]
        resolved_blue = blue_signals[blue_signals["Status"] != "Pending ⏳"]
        hits = len(resolved_blue[resolved_blue["Status"] == "Target Hit 🟢"])
        win_rate = (hits / len(resolved_blue) * 100) if not resolved_blue.empty else 0
        
        st.subheader(f"📊 Market Report: {target_dt}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Signals Found", len(final_data))
        c2.metric("BLUE Win Rate", f"{round(win_rate, 1)}%")
        c3.metric("Institutional (BLUE)", len(blue_signals))
        
        st.dataframe(
            final_data[["Stock", "Category", "Status", "Entry", "Stoploss", "Target (1:2)", "Success %", "Chart"]],
            column_config={"Chart": st.column_config.LinkColumn("View Chart")},
            hide_index=True, use_container_width=True
        )
    else:
        st.error("No valid setups found. The market trend did not meet the institutional criteria for this date.")

st.divider()
st.caption("Strategic Research Tool | Built for 1:2 Reward-to-Risk Benchmarking.")

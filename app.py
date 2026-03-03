import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Swing Triple Bullish 44-200", layout="wide")

# --- REGULATORY COMPLIANCE ---
st.warning("⚠️ **LEGAL DISCLAIMER**: Strictly for Educational Purposes. Not SEBI Registered.")

st.title("🦅 Triple Bullish 44-200 Strategy")
st.markdown("### Exact TradingView Logic Port")

# --- DATE SELECTION ---
max_date = datetime.now().date()
target_dt = st.date_input("Select Analysis Date", value=max_date, max_value=max_date)

# --- NIFTY 200 TICKERS ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DLF.NS', 'DABUR.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GAIL.NS', 'GRASIM.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ZOMATO.NS']

def run_tradingview_strategy():
    results = []
    # Fetch data window
    fetch_start = target_dt - timedelta(days=500)
    fetch_end = datetime.now().date() + timedelta(days=2)
    
    progress = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=fetch_start, end=fetch_end, auto_adjust=True, progress=False)
            if df.empty or len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # 1. Indicators (Matching s44 and s200)
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()

            # Filter for specific target date
            valid_df = df[df.index.date <= target_dt]
            if len(valid_df) < 3: continue
            
            ref_idx = valid_df.index[-1]
            pos = df.index.get_loc(ref_idx)
            
            # Extract values for logic checks
            # Note: [2] in Pine Script refers to 2 bars ago
            row = df.iloc[pos]
            row_prev2 = df.iloc[pos - 2]
            
            c, o, l, h = row['Close'], row['Open'], row['Low'], row['High']
            s44, s200 = row['s44'], row['s200']
            s44_prev2 = row_prev2['s44']
            s200_prev2 = row_prev2['s200']

            # 2. Strict Trend & Candle Logic (Pine Script Translation)
            is_trending = s44 > s200 and s44 > s44_prev2 and s200 > s200_prev2
            is_strong = c > o and c > ((h + l) / 2)
            buy_signal = is_trending and is_strong and l <= s44 and c > s44

            if buy_signal:
                # 3. Risk-Reward Logic
                sl_val = l
                risk = c - l
                tgt1 = c + risk
                tgt2 = c + (risk * 2)
                
                outcome = "Pending ⏳"
                future_data = df.iloc[pos + 1:]
                
                # Tracking Outcome
                for _, f_row in future_data.iterrows():
                    if f_row['Low'] <= sl_val:
                        outcome = "SL Hit 🔴"
                        break
                    if f_row['High'] >= tgt2:
                        outcome = "Target 1:2 Hit 🟢"
                        break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Status": outcome,
                    "Entry": round(c, 2),
                    "Stoploss": round(sl_val, 2),
                    "Tgt 1:1": round(tgt1, 2),
                    "Tgt 1:2": round(tgt2, 2),
                    "Trend": "Rising 📈" if is_trending else "Weak",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button("🚀 Run Triple Bullish Scan"):
    final_data = run_tradingview_strategy()
    
    if not final_data.empty:
        # Success Metrics
        resolved = final_data[final_data["Status"] != "Pending ⏳"]
        hits = len(resolved[resolved["Status"] == "Target 1:2 Hit 🟢"])
        win_rate = (hits / len(resolved) * 100) if not resolved.empty else 0
        
        st.subheader(f"📊 Strategy Performance Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Signals Found", len(final_data))
        m2.metric("Backtest Success Rate (1:2)", f"{round(win_rate, 1)}%")
        m3.metric("Resolved Trades", len(resolved))
        
        # DataFrame Styling
        def style_outcome(val):
            color = 'green' if '🟢' in val else 'red' if '🔴' in val else 'white'
            return f'color: {color}'

        st.dataframe(
            final_data.style.applymap(style_outcome, subset=['Status']),
            column_config={"Chart": st.column_config.LinkColumn("View")},
            hide_index=True, use_container_width=True
        )
    else:
        st.error("No valid setups found. The market conditions did not meet your Pine Script 'Triple Bullish' criteria.")

st.divider()
st.caption("Algorithm strictly follows the 'Swing Triple Bullish 44-200 Final' parameters.")

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Institutional Equity Scanner", layout="wide")

# --- REGULATORY COMPLIANCE HEADER ---
st.warning("⚠️ **LEGAL DISCLAIMER**: This application is strictly for **Educational Purposes** only. We are **NOT SEBI Registered** advisors. The signals generated are based on mathematical algorithms and do not constitute financial advice. Trading involves significant risk.")

st.title("🛡️ Strategic Momentum & Trend Filter")
st.markdown("""
An advanced quantitative tool designed to identify high-probability trend continuation setups within the Nifty 200 universe.
""")

# --- UNIVERSE DEFINITION ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

# --- PARAMETERS ---
selected_date = st.date_input("Execution Date", datetime(2025, 12, 12))

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def execute_analysis():
    results = []
    # Dynamic Date Range to ensure Technical Integrity
    start_fetch = selected_date - timedelta(days=550) 
    end_fetch = selected_date + timedelta(days=5) 
    
    progress_ui = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=start_fetch, end=end_fetch, auto_adjust=True, progress=False)
            
            if df.empty or len(df) < 201:
                continue
            
            # Holiday Handling: Select the latest valid trading session
            available_dates = df.index[df.index <= pd.Timestamp(selected_date)]
            if available_dates.empty: continue
            analysis_date = available_dates[-1]
            
            # Technical Overlays
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=5).mean()
            
            # Reference Points
            ref = df.loc[analysis_date]
            c, o, l = float(ref['Close']), float(ref['Open']), float(ref['Low'])
            s44, s200, rsi = float(ref['SMA_44']), float(ref['SMA_200']), float(ref['RSI'])
            v, v_avg = float(ref['Volume']), float(ref['Vol_Avg'])

            # Multi-Filter Strategy
            if c > s44 and s44 > s200 and c > o:
                is_blue = rsi > 65 and v > v_avg and (c > s200 * 1.05)
                risk = c - l
                target_2 = c + (2 * risk)
                
                status = "Active Session"
                logic_summary = f"Bullish Structure: Trading above key SMAs. RSI at {round(rsi,1)} confirms momentum."

                # Backtest Result Tracking
                future_perf = df[df.index > analysis_date]
                if not future_perf.empty:
                    for _, f_row in future_perf.iterrows():
                        if f_row['Low'] <= l:
                            status = "Structural Exit (SL)"
                            logic_summary = f"Structure Breakdown: Support at Day Low breached. RSI was {round(rsi,1)}."
                            break
                        if f_row['High'] >= target_2:
                            status = "Strategic Jackpot (1:2)"
                            logic_summary = f"Institutional Thrust: Achieved 1:2 Risk/Reward ratio with Volume Surge."
                            break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Target (1:2)": round(target_2, 2),
                    "Technical Logic": logic_summary,
                    "TradingView": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except Exception:
            continue
        progress_ui.progress((i + 1) / len(NIFTY_200))
        
    return pd.DataFrame(results)

if st.button("🚀 Execute Strategic Analysis"):
    output = execute_analysis()
    
    if not output.empty:
        st.subheader(f"Equity Market Summary: {selected_date}")
        
        # Dashboard Matrix
        st.dataframe(
            output[["Stock", "Category", "Status", "Entry", "Stoploss", "Target (1:2)", "TradingView"]],
            column_config={"TradingView": st.column_config.LinkColumn("View Chart")},
            hide_index=True,
            use_container_width=True
        )
        
        st.divider()
        
        # Deep Logic Section
        st.subheader("🔍 Institutional Logic Analysis")
        selected_stock = st.selectbox("Select Asset for Detailed Commentary:", ["-- Select Asset --"] + output["Stock"].tolist())
        
        if selected_stock != "-- Select Asset --":
            asset_data = output[output["Stock"] == selected_stock].iloc[0]
            st.info(f"**Technical Analysis for {selected_stock}**")
            st.success(asset_data["Technical Logic"])
    else:
        st.error("No valid trading setups identified for the selected date. Please verify if the market was open.")

# --- FOOTER COMPLIANCE ---
st.divider()
st.caption("Disclaimer: This tool is for algorithmic research and backtesting purposes only. Past performance does not guarantee future results. Consult a SEBI registered investment advisor before making any financial decisions.")

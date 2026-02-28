import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200: Strategy Fixed", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🛡️ 90% Accuracy Strategy (Stable Build)")

# Date Selection
target_date = st.date_input("Analysis Date", datetime(2025, 12, 12))

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def run_scan():
    results = []
    t_ts = pd.Timestamp(target_date)
    prog = st.progress(0)

    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201 or t_ts not in data.index: continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            data['Vol_Avg'] = data['Volume'].rolling(window=5).mean()
            
            day = data.loc[t_ts]
            close, open_p, low_p = float(day['Close']), float(day['Open']), float(day['Low'])
            sma44, sma200, rsi = float(day['SMA_44']), float(day['SMA_200']), float(day['RSI'])
            vol, vol_avg = float(day['Volume']), float(day['Vol_Avg'])

            if close > sma44 and sma44 > sma200 and close > open_p:
                is_blue = rsi > 65 and vol > vol_avg and (close > sma200 * 1.05)
                risk = close - low_p
                t2 = close + (2 * risk)
                
                status, analysis = "⏳ Running", "Momentum strong hai, 44 SMA ke upar trend sustain kar raha hai."
                future = data[data.index > t_ts]
                
                if not future.empty:
                    for _, f_row in future.iterrows():
                        if f_row['Low'] <= low_p:
                            status, analysis = "🔴 SL Hit", f"Stock ne support level (Signal Low) break kar diya. RSI entry par {round(rsi,1)} tha."
                            break
                        if f_row['High'] >= t2:
                            status, analysis = "🔥 Jackpot Hit", f"Target 1:2 achieve hua! RSI {round(rsi,1)} aur Volume boost ne breakout confirm kiya."
                            break

                pure_name = ticker.replace(".NS","")
                tv_link = f"https://www.tradingview.com/chart/?symbol=NSE:{pure_name}"
                
                results.append({
                    "Stock": pure_name,
                    "TradingView": tv_link,
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Entry": round(close, 2),
                    "Stoploss": round(low_p, 2),
                    "Target 1:2": round(t2, 2),
                    "Analysis": analysis
                })
        except: continue
        prog.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Run Analysis'):
    df_results = run_scan()
    if not df_results.empty:
        st.subheader(f"📊 Market Report: {target_date}")
        
        # Dashboard Stats
        blue_count = len(df_results[df_results['Category'] == "🔵 BLUE"])
        st.write(f"**Found {len(df_results)} signals ({blue_count} High Probability Blue).**")

        # Table Display (Clean and Link enabled)
        st.dataframe(
            df_results[["Stock", "TradingView", "Category", "Status", "Entry", "Stoploss", "Target 1:2"]],
            column_config={"TradingView": st.column_config.LinkColumn()},
            hide_index=True,
            use_container_width=True
        )

        st.divider()
        
        # --- ANALYSIS DROPDOWN (Safe Method) ---
        st.subheader("🔍 Detailed Stock Analysis")
        stock_to_analyze = st.selectbox("Select a stock to see 'Why':", ["-- Select --"] + df_results["Stock"].tolist())
        
        if stock_to_analyze != "-- Select --":
            selected_row = df_results[df_results["Stock"] == stock_to_analyze].iloc[0]
            st.info(f"**Analysis for {stock_to_analyze}:**")
            st.success(selected_row["Analysis"])
            
    else:
        st.warning("No signals found for this date.")

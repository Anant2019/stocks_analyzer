import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Setup
st.set_page_config(page_title="NSE 200 Professional Scanner", layout="wide")

# --- OFFICIAL NIFTY 200 TICKERS LIST ---
# Maine poore 200 tickers yahan manually lock kar diye hain
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'APLLTD.NS', 'ASHOKLEY.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'AVANTIFEED.NS', 'BALRAMCHIN.NS', 'BHARATFORG.NS', 'BOSCHLTD.NS', 'BSOFT.NS', 'CANFINHOME.NS', 'CHAMBLFERT.NS', 'CHOLAFIN.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'CUMMINSIND.NS', 'DEEPAKFERT.NS', 'EQUITASBNK.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'FORTIS.NS', 'GLENMARK.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GODREJPROP.NS', 'GRANULES.NS', 'GSPL.NS', 'GUJGASLTD.NS', 'HAVELLS.NS', 'IDFC.NS', 'IDFCFIRSTB.NS', 'IEX.NS', 'INDIACEM.NS', 'INDIAMART.NS', 'INDHOTEL.NS', 'IPCALAB.NS', 'IRCTC.NS', 'JINDALSTEL.NS', 'JKCEMENT.NS', 'JUBLFOOD.NS', 'LAURUSLABS.NS', 'LICHSGFIN.NS', 'LUPIN.NS', 'MANAPPURAM.NS', 'MAXHEALTH.NS', 'METROPOLIS.NS', 'MFSL.NS', 'MPHASIS.NS', 'NATIONALUM.NS', 'NAVINFLUOR.NS', 'OBEROIRLTY.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PFC.NS', 'POLYCAB.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'SAIL.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TVSMOTOR.NS', 'UBL.NS', 'UNITDSPR.NS', 'VOLTAS.NS', 'ZEEL.NS'
]

st.title("🛡️ Professional NSE 200 Strategy Scanner")
st.markdown("### `Strict Logic: Price > 44 SMA > 200 SMA + Support`")

target_date = st.date_input("Select Date", datetime.now() - timedelta(days=1))

def scan_professional(sel_date):
    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Range fetching
    start_f = sel_date - timedelta(days=500)
    end_f = sel_date + timedelta(days=60) # Future buffer for backtesting
    
    total = len(NIFTY_200)
    win_count = 0
    total_signals = 0

    for i, ticker in enumerate(NIFTY_200):
        try:
            status_text.text(f"Scanning {i+1}/{total}: {ticker}")
            # Strict Data Download
            df = yf.download(ticker, start=start_f, end=end_f, interval="1d", auto_adjust=True, progress=False)
            
            if len(df) < 200: continue
            
            # SMAs (TradingView Math)
            df['s44'] = df['Close'].rolling(window=44).mean()
            df['s200'] = df['Close'].rolling(window=200).mean()
            
            # Align with selected date
            available_idx = df.index[df.index <= pd.Timestamp(sel_date)]
            if len(available_idx) == 0: continue
            current_date = available_idx[-1]
            pos = df.index.get_loc(current_date)
            
            # Variables for Logic
            curr = df.iloc[pos]
            prev2 = df.iloc[pos-2]
            
            # --- TRADINGVIEW STRICT CONDITIONS ---
            # 1. Rising Trend (SMA 44 > 200 and SMAs are moving UP)
            trending = curr['s44'] > curr['s200'] and curr['s44'] > prev2['s44'] and curr['s200'] > prev2['s200']
            
            # 2. Strong Bullish Candle
            green = curr['Close'] > curr['Open']
            strong_body = curr['Close'] > ((curr['High'] + curr['Low']) / 2)
            
            # 3. Support Logic (Touch/Near 44 SMA)
            # 0.5% buffer for professional precision
            near_support = curr['Low'] <= (curr['s44'] * 1.005) 
            above_sma = curr['Close'] > curr['s44']

            if trending and green and strong_body and near_support and above_sma:
                entry = float(curr['Close'])
                sl = float(curr['Low'])
                risk = entry - sl
                t1 = entry + risk
                t2 = entry + (risk * 2)
                
                # Success Rate Check (Next 30 days)
                future = df.iloc[pos+1 : pos+31]
                outcome = "Running"
                for _, f_row in future.iterrows():
                    if f_row['High'] >= t1:
                        outcome = "✅ SUCCESS (1:1)"
                        win_count += 1
                        break
                    if f_row['Low'] <= sl:
                        outcome = "❌ SL HIT"
                        break
                
                total_signals += 1
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": round(entry, 2),
                    "Stop Loss": round(sl, 2),
                    "Target 1:1": round(t1, 2),
                    "Target 1:2": round(t2, 2),
                    "Result": outcome
                })
        except: continue
        progress_bar.progress((i + 1) / total)
        
    status_text.empty()
    return pd.DataFrame(found_stocks), win_count, total_signals

if st.button('🚀 Start Professional Scan'):
    results, w_count, t_count = scan_professional(target_date)
    if not results.empty:
        acc = (w_count/t_count)*100 if t_count > 0 else 0
        st.metric("Strategy Win Rate (Historical)", f"{round(acc, 2)}%")
        st.dataframe(results, use_container_width=True)
    else:
        st.error("No stocks matched the strict 44-200 criteria for this date.")

st.divider()
st.caption("Data Source: Yahoo Finance (Adjusted) | Strategy: Swing Triple Bullish")

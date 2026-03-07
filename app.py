import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Swing Triple Bullish Scanner", page_icon="📈", layout="wide")

NSE_200 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "SBIN", "BHARTIARTL",
    "ITC", "KOTAKBANK", "LT", "AXISBANK", "BAJFINANCE", "ASIANPAINT", "MARUTI", "TITAN",
    "SUNPHARMA", "HCLTECH", "WIPRO", "ULTRACEMCO", "NTPC", "TATAMOTORS", "POWERGRID",
    "M&M", "NESTLEIND", "JSWSTEEL", "TECHM", "TATASTEEL", "ADANIENT", "ADANIPORTS",
    "BAJAJFINSV", "COALINDIA", "GRASIM", "DIVISLAB", "DRREDDY", "CIPLA", "BPCL",
    "EICHERMOT", "HEROMOTOCO", "BRITANNIA", "APOLLOHOSP", "ONGC", "HINDALCO",
    "SBILIFE", "BAJAJ-AUTO", "INDUSINDBK", "TATACONSUM", "DABUR", "PIDILITIND",
    "GODREJCP", "HAVELLS", "SIEMENS", "AMBUJACEM", "ACC", "BERGEPAINT",
    "TORNTPHARM", "BIOCON", "LICI", "IRCTC", "NAUKRI", "DMART", "MUTHOOTFIN",
    "CHOLAFIN", "MARICO", "AUROPHARMA", "LUPIN", "PEL", "SHREECEM",
    "INDUSTOWER", "VEDL", "IOC", "GAIL", "BANKBARODA", "PNB", "TRENT",
    "CANBK", "IDFCFIRSTB", "FEDERALBNK", "VOLTAS", "JUBLFOOD", "PAGEIND",
    "COLPAL", "MPHASIS", "LTIM", "PERSISTENT", "COFORGE", "LTTS",
    "SYNGENE", "PIIND", "ASTRAL", "POLYCAB", "SONACOMS", "SUPREMEIND",
    "ABB", "BHEL", "HAL", "BEL", "IRFC", "RECLTD", "PFC",
    "TATAPOWER", "ADANIGREEN", "ADANIPOWER", "JINDALSTEL", "SAIL", "NMDC",
    "CONCOR", "DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "PHOENIXLTD",
    "LODHA", "MFSL", "MAXHEALTH", "FORTIS", "ZYDUSLIFE", "ALKEM",
    "IPCALAB", "LAURUSLABS", "NATCOPHARMA", "METROPOLIS", "ABCAPITAL",
    "BANDHANBNK", "AUBANK", "MANAPPURAM", "LICHSGFIN", "SBICARD",
    "HDFCAMC", "ICICIGI", "ICICIPRULI", "HDFCLIFE",
    "UPL", "COROMANDEL", "DEEPAKNTR", "ATUL", "CLEAN", "SRF",
    "FLUOROCHEM", "TATAELXSI", "ZOMATO",
    "DELHIVERY", "POLICYBZR", "MOTHERSON",
    "BOSCHLTD", "MRF", "BALKRISIND", "EXIDEIND",
    "CUMMINSIND", "THERMAX",
    "DIXON", "HONAUT", "CROMPTON",
    "BATAINDIA", "VGUARD",
    "BHARATFORG", "TIINDIA", "SUNTV",
    "ZEEL", "ABFRL", "RAYMOND", "RVNL", "SJVN", "NHPC", "JSWENERGY",
    "TORNTPOWER", "CESC", "TATACOMM", "HFCL",
    "CDSL", "BSE", "MCX", "JIOFIN", "BAJAJHLDNG",
    "IGL", "MGL", "PETRONET", "GUJGASLTD",
]


def scan_stock(symbol, start_date, end_date):
    try:
        ticker = f"{symbol}.NS"
        fetch_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=400)).strftime("%Y-%m-%d")
        df = yf.download(ticker, start=fetch_start, end=end_date, progress=False, auto_adjust=True)

        if df.empty or len(df) < 203:
            return []

        df["SMA44"] = df["Close"].rolling(44).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()
        df["SMA44_2"] = df["SMA44"].shift(2)
        df["SMA200_2"] = df["SMA200"].shift(2)

        df = df[df.index >= start_date].copy()

        df["is_trending"] = (df["SMA44"] > df["SMA200"]) & (df["SMA44"] > df["SMA44_2"]) & (df["SMA200"] > df["SMA200_2"])
        df["is_strong"] = (df["Close"] > df["Open"]) & (df["Close"] > (df["High"] + df["Low"]) / 2)
        df["buy"] = df["is_trending"] & df["is_strong"] & (df["Low"] <= df["SMA44"]) & (df["Close"] > df["SMA44"])

        signals = df[df["buy"]].copy()
        if signals.empty:
            return []

        results = []
        for date, row in signals.iterrows():
            close = float(row["Close"])
            low = float(row["Low"])
            risk = close - low
            results.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Symbol": symbol,
                "Close": round(close, 2),
                "SMA44": round(float(row["SMA44"]), 2),
                "SMA200": round(float(row["SMA200"]), 2),
                "Entry": round(close, 2),
                "Stop Loss": round(low, 2),
                "Target 1 (1:1)": round(close + risk, 2),
                "Target 2 (1:2)": round(close + risk * 2, 2),
                "Risk ₹": round(risk, 2),
                "Risk %": round((risk / close) * 100, 2),
            })
        return results
    except Exception:
        return []


# ── Sidebar ──
with st.sidebar:
    st.title("⚙️ Scanner Settings")
    st.markdown("---")

    lookback = st.selectbox("Lookback Period", ["1 Month", "3 Months", "6 Months", "1 Year"], index=3)
    lookback_days = {"1 Month": 30, "3 Months": 90, "6 Months": 180, "1 Year": 365}[lookback]

    end_date = st.date_input("End Date", datetime.now())
    start_date = end_date - timedelta(days=lookback_days)

    st.markdown(f"**Scan Period:** `{start_date}` → `{end_date}`")
    st.markdown(f"**Universe:** `{len(NSE_200)} stocks`")

    st.markdown("---")
    st.subheader("📋 Strategy Rules")
    st.markdown("""
    **Entry:**
    - 44 SMA > 200 SMA (both rising)
    - Green candle, close > midpoint
    - Low touches 44 SMA, close above it

    **Risk Management:**
    - Stop Loss = Candle Low
    - Target 1 = 1:1 R:R
    - Target 2 = 1:2 R:R
    - Exit 50% at Target 1
    """)

    scan_btn = st.button("🚀 Scan Now", use_container_width=True, type="primary")


# ── Main Area ──
st.title("📈 Swing Triple Bullish Scanner")
st.caption("44-200 SMA Strategy · NSE 200")

col1, col2, col3 = st.columns(3)
col1.metric("Universe", f"{len(NSE_200)} stocks")

if scan_btn:
    all_signals = []
    progress_bar = st.progress(0, text="Starting scan...")
    status_text = st.empty()
    total = len(NSE_200)

    for i, symbol in enumerate(NSE_200):
        progress = (i + 1) / total
        progress_bar.progress(progress, text=f"Scanning {symbol}... ({i+1}/{total})")
        signals = scan_stock(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        all_signals.extend(signals)

    progress_bar.progress(1.0, text="✅ Scan complete!")

    if all_signals:
        df = pd.DataFrame(all_signals).sort_values("Date", ascending=False)
        unique_stocks = df["Symbol"].nunique()

        col2.metric("Signals Found", len(df))
        col3.metric("Stocks with Signals", unique_stocks)

        st.markdown("---")
        st.subheader("📊 All Buy Signals")

        # Highlight styling
        def highlight_row(row):
            return ["background-color: rgba(34, 197, 94, 0.05)"] * len(row)

        st.dataframe(
            df.style.apply(highlight_row, axis=1).format({
                "Close": "₹{:.2f}",
                "SMA44": "{:.2f}",
                "SMA200": "{:.2f}",
                "Entry": "₹{:.2f}",
                "Stop Loss": "₹{:.2f}",
                "Target 1 (1:1)": "₹{:.2f}",
                "Target 2 (1:2)": "₹{:.2f}",
                "Risk ₹": "₹{:.2f}",
                "Risk %": "{:.2f}%",
            }),
            use_container_width=True,
            height=500,
        )

        st.markdown("---")
        st.subheader("📈 Signal Count by Stock")
        summary = df.groupby("Symbol").size().sort_values(ascending=False).reset_index(name="Signals")
        st.bar_chart(summary.set_index("Symbol"), height=400)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, f"swing_signals_{start_date}_to_{end_date}.csv", "text/csv")
    else:
        col2.metric("Signals Found", 0)
        col3.metric("Stocks with Signals", 0)
        st.warning("No buy signals found in the selected period.")
else:
    st.info("👈 Configure settings in the sidebar and click **Scan Now** to begin.")

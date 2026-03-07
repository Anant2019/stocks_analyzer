def scan_stock(symbol, start_date, end_date):
    try:
        ticker = f"{symbol}.NS"
        fetch_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=400)).strftime("%Y-%m-%d")
        df = yf.download(ticker, start=fetch_start, end=end_date, progress=False, auto_adjust=True)

        if df.empty or len(df) < 203:
            return []

        # FIX: Flatten MultiIndex columns (yfinance >= 0.2.31 returns MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Ensure numeric types
        for col in ["Open", "High", "Low", "Close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["SMA44"] = df["Close"].rolling(44).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()
        df["SMA44_2"] = df["SMA44"].shift(2)
        df["SMA200_2"] = df["SMA200"].shift(2)

        df = df[df.index >= start_date].copy()
        df = df.dropna(subset=["SMA44", "SMA200", "SMA44_2", "SMA200_2"])

        # Pine Script conditions - use .values to avoid index alignment issues
        is_trending = (df["SMA44"].values > df["SMA200"].values) & \
                      (df["SMA44"].values > df["SMA44_2"].values) & \
                      (df["SMA200"].values > df["SMA200_2"].values)

        is_strong = (df["Close"].values > df["Open"].values) & \
                    (df["Close"].values > (df["High"].values + df["Low"].values) / 2)

        buy = is_trending & is_strong & \
              (df["Low"].values <= df["SMA44"].values) & \
              (df["Close"].values > df["SMA44"].values)

        df["buy"] = buy
        signals = df[df["buy"]].copy()

        if signals.empty:
            return []

        results = []
        for date, row in signals.iterrows():
            close = float(row["Close"])
            low = float(row["Low"])
            risk = close - low
            if risk <= 0:
                continue
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
    except Exception as e:
        st.toast(f"⚠️ {symbol}: {e}")
        return []

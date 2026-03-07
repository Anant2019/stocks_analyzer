# swing_screener.py
# Swing Triple Bullish 44-200 Scanner - NSE 200
# Requirements: pip install yfinance pandas tabulate

import yfinance as yf
import pandas as pd
from tabulate import tabulate
from datetime import datetime, timedelta

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
    "IGL", "MGL", "PETRONET", "GUJGASLTD"
]


def scan_stock(symbol: str, start_date: str, end_date: str):
    """Scan a single stock for all buy signals in the date range."""
    try:
        ticker = f"{symbol}.NS"
        # Fetch extra data before start_date for SMA calculation
        fetch_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=400)).strftime("%Y-%m-%d")
        df = yf.download(ticker, start=fetch_start, end=end_date, progress=False, auto_adjust=True)

        if df.empty or len(df) < 203:
            return []

        df["SMA44"] = df["Close"].rolling(44).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()
        df["SMA44_2"] = df["SMA44"].shift(2)
        df["SMA200_2"] = df["SMA200"].shift(2)

        # Filter to analysis period only
        df = df[df.index >= start_date].copy()

        # Pine Script conditions
        df["is_trending"] = (df["SMA44"] > df["SMA200"]) & (df["SMA44"] > df["SMA44_2"]) & (df["SMA200"] > df["SMA200_2"])
        df["is_strong"] = (df["Close"] > df["Open"]) & (df["Close"] > (df["High"] + df["Low"]) / 2)
        df["buy"] = df["is_trending"] & df["is_strong"] & (df["Low"] <= df["SMA44"]) & (df["Close"] > df["SMA44"])

        signals = df[df["buy"]].copy()
        if signals.empty:
            return []

        results = []
        for date, row in signals.iterrows():
            risk = float(row["Close"] - row["Low"])
            results.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Symbol": symbol,
                "Close": round(float(row["Close"]), 2),
                "SMA44": round(float(row["SMA44"]), 2),
                "SMA200": round(float(row["SMA200"]), 2),
                "Entry": round(float(row["Close"]), 2),
                "SL": round(float(row["Low"]), 2),
                "Tgt1 (1:1)": round(float(row["Close"]) + risk, 2),
                "Tgt2 (1:2)": round(float(row["Close"]) + risk * 2, 2),
                "Risk": round(risk, 2),
                "Risk%": round((risk / float(row["Close"])) * 100, 2),
            })
        return results

    except Exception as e:
        print(f"  ⚠ Error scanning {symbol}: {e}")
        return []


def main():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    print("=" * 80)
    print("  SWING TRIPLE BULLISH 44-200 SCANNER")
    print(f"  Period: {start_date} → {end_date} | Universe: NSE 200")
    print("=" * 80)

    all_signals = []
    total = len(NSE_200)

    for i, symbol in enumerate(NSE_200, 1):
        print(f"\r  Scanning [{i}/{total}] {symbol:<20}", end="", flush=True)
        signals = scan_stock(symbol, start_date, end_date)
        all_signals.extend(signals)

    print(f"\n\n{'=' * 80}")
    print(f"  RESULTS: {len(all_signals)} buy signals found across {len(set(s['Symbol'] for s in all_signals))} stocks")
    print(f"{'=' * 80}\n")

    if all_signals:
        df_results = pd.DataFrame(all_signals).sort_values("Date", ascending=False)
        print(tabulate(df_results, headers="keys", tablefmt="fancy_grid", showindex=False))

        # Save to CSV
        csv_file = f"swing_signals_{start_date}_to_{end_date}.csv"
        df_results.to_csv(csv_file, index=False)
        print(f"\n  ✅ Results saved to {csv_file}")

        # Summary by stock
        print(f"\n{'=' * 80}")
        print("  SIGNAL COUNT BY STOCK")
        print(f"{'=' * 80}")
        summary = df_results.groupby("Symbol").size().sort_values(ascending=False)
        for sym, count in summary.items():
            print(f"  {sym:<20} {'█' * count} ({count})")
    else:
        print("  No buy signals found in the given period.")


if __name__ == "__main__":
    main()

# Select the latest and previous rows
latest = data.iloc[-1]
prev = data.iloc[-2]

# Fix: Extract raw float values to avoid label comparison errors
price_close = float(latest['Close'].iloc[0]) if isinstance(latest['Close'], pd.Series) else float(latest['Close'])
price_open = float(latest['Open'].iloc[0]) if isinstance(latest['Open'], pd.Series) else float(latest['Open'])
price_low = float(latest['Low'].iloc[0]) if isinstance(latest['Low'], pd.Series) else float(latest['Low'])
sma44_now = float(latest['SMA44'].iloc[0]) if isinstance(latest['SMA44'], pd.Series) else float(latest['SMA44'])
sma44_prev = float(prev['SMA44'].iloc[0]) if isinstance(prev['SMA44'], pd.Series) else float(prev['SMA44'])
sma200_now = float(latest['SMA200'].iloc[0]) if isinstance(latest['SMA200'], pd.Series) else float(latest['SMA200'])
sma200_prev = float(prev['SMA200'].iloc[0]) if isinstance(prev['SMA200'], pd.Series) else float(prev['SMA200'])

# Logic: SMAs rising and Green Candle
is_sma44_rising = sma44_now > sma44_prev
is_sma200_rising = sma200_now > sma200_prev
is_green_candle = price_close > price_open

# Support check: Low of the candle is near or touching the 44 SMA
is_at_support = price_low <= (sma44_now * 1.01) 

if is_sma44_rising and is_sma200_rising and is_green_candle and is_at_support:
    # Your append logic here...

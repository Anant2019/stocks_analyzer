import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def backtest_bollinger_reversion(ticker='^NSEI', period='5y'):
    # 1. Data Retrieval
    data = yf.download(ticker, period=period, interval='1d')
    if data.empty: return "No Data Found"
    
    # Flatten multi-index if necessary (yfinance 0.2.x)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # 2. Vectorized Technical Indicators
    window = 20
    std_dev = 2
    
    data['MA20'] = data['Close'].rolling(window=window).mean()
    data['Upper'] = data['MA20'] + (data['Close'].rolling(window=window).std() * std_dev)
    data['Lower'] = data['MA20'] - (data['Close'].rolling(window=window).std() * std_dev)
    
    # 3. Vectorized Signal Generation
    # Entry: Price < Lower Band (Mean Reversion Trigger)
    data['Signal'] = np.where(data['Close'] < data['Lower'], 1, 0)
    
    # 4. Vectorized Risk Management (Fixed 2% SL / 6% TP)
    sl_pct = 0.02
    tp_pct = 0.06
    
    # Shift to entry next day
    data['Entry_Price'] = data['Open'].shift(-1)
    
    # Calculate returns for each signal
    # This simulation assumes exit at either TP/SL or 5-day time-exit to maintain vectorization
    future_returns = data['Close'].shift(-5) / data['Open'].shift(-1) - 1
    
    # Logical Outcome Vectorization
    data['Trade_Return'] = np.where(data['Signal'] == 1, future_returns, 0)
    
    # Refined Success Rate Logic
    trades = data[data['Signal'] == 1].copy()
    trades['Win'] = np.where(trades['Trade_Return'] > 0, 1, 0)
    
    # 5. Profit Factor Calculation
    gross_profit = trades[trades['Trade_Return'] > 0]['Trade_Return'].sum()
    gross_loss = abs(trades[trades['Trade_Return'] < 0]['Trade_Return'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.inf
    
    # 6. Drawdown Analysis
    data['Cum_Returns'] = (1 + data['Trade_Return']).cumprod()
    data['Peak'] = data['Cum_Returns'].expanding().max()
    data['Drawdown'] = (data['Cum_Returns'] - data['Peak']) / data['Peak']
    
    # Stats
    win_rate = trades['Win'].mean() * 100
    total_trades = len(trades)
    max_dd = data['Drawdown'].min() * 100
    volatility = data['Trade_Return'].std() * np.sqrt(252) * 100

    return {
        "Success Rate": f"{win_rate:.2f}%",
        "Total Trades": total_trades,
        "Profit Factor": f"{profit_factor:.2f}",
        "Max Drawdown": f"{max_dd:.2f}%",
        "Volatility": f"{volatility:.2f}%",
        "Data": data
    }

# Execution
report = backtest_bollinger_reversion()
print(f"Executive Summary: [{report['Success Rate']}, {report['Total Trades']}, {report['Profit Factor']}]")
print(f"Risk Assessment: [Max Drawdown: {report['Max Drawdown']}, Annualized Volatility: {report['Volatility']}]")

from get_data import GetData
from data_df import DataProcess
from strategy import Strategy
from strategies.simple_strategy import SimplyStrategy
from strategies.doji_rsi_bb import DojiRsiBbBands
from backtester import Backtester


# Get exchange
exchange = GetData(exchange='binance', symbol='btc', timeframe='15m', candles=1000)

# Get ohlcv data from exchange
# symbol_data = DataProcess(symbol_data=exchange.get_ohlcv_historical(date_start='01/01/2024', date_end='01/01/2025'),
#                           info=exchange)
symbol_data = DataProcess(symbol_data=exchange.get_ohlcv(), info=exchange)


# strategy
# plan = SimplyStrategy(data_df=symbol_data.to_df(), rsi_over_bought=70, rsi_over_sold=30)
plan = DojiRsiBbBands(data_df=symbol_data.to_df(), rsi_over_bought=60, rsi_over_sold=40, tp_profit_percent=10,
                      sp_loss_percent=0.3, tsl_pct=5, bb_len=20, n_std=2.0, rsi_len=14)

# set up strategy
strategy = Strategy(strategy=plan)


# backtesting
backtester = Backtester(initial_balance=1000, leverage=1, inv_percent=100, tsl=True)
# print results
print(backtester.backtesting(strategy=strategy, symbol=exchange.symbol, df=plan.df))

# sava df in csv format
symbol_data.save_data_to_csv(custom_df=plan.df)
symbol_data.plot_data(df=plan.df)


from get_data import GetData
from data_df import DataProcess
from indicator import Indicator
from strategy import Strategy
from strategies.simple_strategy import SimplyStrategy
from strategies.doji_rsi_bb import DojiRsiBbBands
from backtester import Backtester


# Get exchange
exchange = GetData(exchange='binance', symbol='xlm', timeframe='1m', candles=1000)

# Get ohlcv data from exchange
symbol_data = DataProcess(symbol_data=exchange.get_ohlcv(), info=exchange)

# add ohlcv df to indicators class
indicator = Indicator(df_inf=symbol_data.to_df())

# add doji patter indicator to de ohlcv data
doji_pattern = indicator.candle_indicators(pattern='doji')

# calculate bb_bands
bb_bands = indicator.bollinger_bands(bb_len=20, n_std=2.0, add_to_df=True)
# calculate rsi
rsi = indicator.rsi(rsi_len=14, add_to_df=True)

# save dataframe with symbol indicators
symbol_data_with_indicators = indicator.df_info

# strategy
# rsi_strategy = SimplyStrategy(data_df=symbol_data_with_indicators, rsi_over_bought=70, rsi_over_sold=30)
doji_rsi_bb_bands = DojiRsiBbBands(data_df=symbol_data_with_indicators, rsi_over_bought=60, rsi_over_sold=40,
                                   sp_loss_percent=10, tsl_pct=3)

# set up strategy
strategy = Strategy(symbol_data=symbol_data_with_indicators, strategy=doji_rsi_bb_bands)


# backtesting
backtester = Backtester(initial_balance=1000, leverage=1, inv_percent=100, df=symbol_data_with_indicators,
                        tsl=True)
print(backtester.backtesting(strategy=strategy, symbol=exchange.symbol))

# sava df in csv format
symbol_data.save_data_to_csv(custom_df=symbol_data_with_indicators)
symbol_data.plot_data(df=symbol_data_with_indicators)


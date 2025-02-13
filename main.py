from get_data import GetData
from data_df import DataProcess
from indicator import Indicator
from strategy import Strategy


# Get exchange
exchange = GetData(exchange='binance', symbol='eth', timeframe='15m', candles=100)

# Get ohlcv data from exchange
symbol_data = DataProcess(symbol_data=exchange.get_ohlcv(), info=exchange)

# add ohlcv df to indicators class
indicator = Indicator(df_inf=symbol_data.to_df())

# add doji patter indicator to de ohlcv data
# doji_pattern = indicator.candle_indicators(pattern='doji')

# calculate bb_bands
bb_bands = indicator.bollinger_bands(bb_len=20, n_std=2.0, add_to_df=True)
# calculate rsi
rsi = indicator.rsi(rsi_len=14, add_to_df=True)

# save dataframe with symbol indicators
symbol_data_with_indicators = indicator.df_info

# set up strategy
strategy = Strategy(symbol_data=symbol_data_with_indicators)

# start strategy
strategy.check_long_signal(over_bought_rsi=60, over_sold_rsi=40)

# sava df in csv format
symbol_data.save_data_to_csv(custom_df=symbol_data_with_indicators)


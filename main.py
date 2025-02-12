from get_data import GetData
from data_df import DataProcess
from Indicator import Indicator

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
rsi = indicator.rsi(rsi_len=14, add_to_df=True)


# sava df in csv format
symbol_data.save_data_to_csv(custom_df=indicator.df_info)
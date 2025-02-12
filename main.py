from get_data import GetData
from data_df import DataProcess
from Indicator import Indicator
# Get exchange
exchange = GetData(exchange='binance', symbol='ltc', timeframe='15m', candles=300)
# Get ohlcv data from exchange
symbol_data = DataProcess(symbol_data=exchange.get_ohlcv(), info=exchange)
# add ohlcv df to indicators class
indicator = Indicator(df_inf=symbol_data.to_df())
# add doji patter indicator to de ohlcv data
doji_pattern = indicator.candle_indicators(pattern='doji')
# sava df in csv format
symbol_data.save_data_to_csv(custom_df=doji_pattern)

from get_data import GetData
from data_df import DataProcess
from Indicator import Indicator

exchange = GetData(exchange='binance', symbol='eth', timeframe='5m', candles=300)
symbol_data = DataProcess(symbol_data=exchange.get_ohlcv(), info=exchange)
indicator = Indicator(df_inf=symbol_data.to_df())

doji_pattern = indicator.candle_indicators(pattern='doji')

symbol_data.save_data_to_csv(custom_df=doji_pattern)

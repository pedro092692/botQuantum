from get_data import GetData
from data_df import DataProcess
from strategy import Strategy

btc_info = GetData(exchange='binance', symbol='eth', timeframe='1d', candles=500)
data = DataProcess(symbol_data=btc_info.price_data(), info=btc_info)
data.save_data_to_csv()
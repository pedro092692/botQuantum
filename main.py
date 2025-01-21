from get_data import GetData
from data_df import DataProcess

btc_info = GetData(exchange='binance', symbol='btc', timeframe='5m', candles=450)
data = DataProcess(symbol_data=btc_info.price_data(), info=btc_info)
data.save_data_to_csv()

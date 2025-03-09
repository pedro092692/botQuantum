import ccxt
import os
from binance.client import Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class GetData:
    def __init__(self, exchange, symbol: str, timeframe, candles):
        self.exchange = exchange
        self.symbol = symbol.upper() + '/USDT'
        self.timeframe = timeframe
        self.candles = candles
        self.client = Client(os.getenv('KEY'), os.getenv('SECRET'))

    def exchange_info(self):
        exchange_name = self.exchange
        exchange_class = getattr(ccxt, exchange_name)
        return exchange_class()

    def get_ohlcv(self):
        ohlcv = self.exchange_info().fetch_ohlcv(self.symbol, self.timeframe, limit=self.candles)
        return ohlcv

    def get_ohlcv_historical(self, date_start: str, date_end: str):

        # convert string in ms
        start_ts = int(datetime.strptime(date_start, '%d/%m/%Y').timestamp() * 1000)
        end_ts = int(datetime.strptime(date_end, '%d/%m/%Y').timestamp() * 1000)
        symbol = self.symbol.replace('/', '')
        data = self.client.get_historical_klines(symbol, self.timeframe, start_ts, end_ts)
        ohlcv = [[
            int(k[0]),
            float(k[1]),
            float(k[2]),
            float(k[3]),
            float(k[4]),
            float(k[5])
        ] for k in data]
        return ohlcv









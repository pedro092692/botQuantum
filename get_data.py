import ccxt
import os
import time
from binance.client import Client
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


def drop_unclosed_candles(ohlcv, timeframe, now_ms=None):
    """
    Remove candles that are not closed yet (the exchange returns the current candle too).
    Using a candle that is still open is look-ahead in a backtest and repainting in live trading.
    """
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    tf_ms = ccxt.Exchange.parse_timeframe(timeframe) * 1000
    return [candle for candle in ohlcv if candle[0] + tf_ms <= now_ms]


class GetData:
    def __init__(self, exchange, symbol: str, timeframe, candles):
        self.exchange = exchange
        self.symbol = symbol.upper() + '/USDT'
        self.timeframe = timeframe
        self.candles = candles

    def exchange_info(self):
        exchange_name = self.exchange
        exchange_class = getattr(ccxt, exchange_name)
        return exchange_class()

    def get_ohlcv(self):
        ohlcv = self.exchange_info().fetch_ohlcv(self.symbol, self.timeframe, limit=self.candles)
        return drop_unclosed_candles(ohlcv, self.timeframe)

    def get_ohlcv_historical(self, date_start: str, date_end: str):
        # public endpoint, the keys are optional
        client = Client(os.getenv('KEY'), os.getenv('SECRET'))

        # convert string (UTC) in ms
        start_ts = int(datetime.strptime(date_start, '%d/%m/%Y').replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ts = int(datetime.strptime(date_end, '%d/%m/%Y').replace(tzinfo=timezone.utc).timestamp() * 1000)
        symbol = self.symbol.replace('/', '')
        data = client.get_historical_klines(symbol, self.timeframe, start_ts, end_ts)
        ohlcv = [[
            int(k[0]),
            float(k[1]),
            float(k[2]),
            float(k[3]),
            float(k[4]),
            float(k[5])
        ] for k in data]
        return drop_unclosed_candles(ohlcv, self.timeframe)

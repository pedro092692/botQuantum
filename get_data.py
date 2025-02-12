import ccxt


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
        return ohlcv










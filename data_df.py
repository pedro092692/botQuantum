import pandas as pd
import mplfinance as mpf

OHLCV_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume']


def load_csv(path) -> pd.DataFrame:
    """Load candles saved in markets_data/ (only OHLCV, old indicator columns are dropped)."""
    df = pd.read_csv(path)
    return df[OHLCV_COLUMNS].reset_index(drop=True)


def train_test_split(df: pd.DataFrame, train_pct=70):
    """
    Split by time: the first part to optimize (train) and the last one to validate (test).
    Never shuffle candles, the test must always be AFTER the train.
    """
    split = int(len(df) * train_pct / 100)
    train = df.iloc[:split].reset_index(drop=True)
    test = df.iloc[split:].reset_index(drop=True)
    return train, test


class DataProcess:
    def __init__(self, symbol_data, info):
        self.symbol_data = symbol_data
        self.info = info

    def to_df(self) -> pd.DataFrame:
        dataframe = pd.DataFrame(self.symbol_data)
        dataframe.columns = OHLCV_COLUMNS
        # convert timestamp in datetime object (UTC)
        dataframe.date = pd.to_datetime(dataframe.date, unit='ms')
        dataframe.date = dataframe.date.dt.strftime('%d-%m-%Y %H:%M')
        return dataframe

    def save_data_to_csv(self, custom_df=pd.DataFrame()):
        if custom_df.empty:
            df = self.to_df()
        else:
            df = custom_df
        time = df.date.iloc[-1][0:10]
        df.to_csv(f'markets_data/{self.info.symbol.replace('/', '-')}-{self.info.timeframe}-{time}.csv',
                  sep=',', header=True, index=False)

    def plot_data(self, df: pd.DataFrame):
        style = mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='green', down='red'))
        dataframe = df.copy()
        dataframe.date = pd.to_datetime(dataframe.date, dayfirst=True)
        dataframe = dataframe.set_index('date')
        long_markers = dataframe['open'].where(dataframe['long_signal'] == 'buy', None)
        sell_markets = dataframe['close'].where(dataframe['profit'] == 'True', None)
        loss_operation = dataframe['close'].where(dataframe['loss'] == 'True', None)
        markers = [long_markers, sell_markets, loss_operation]
        active_markers = [mpf.make_addplot(maker, type='scatter', markersize=150, marker='^', color=color)
                          for maker, color in zip(markers, ['blue', 'green', 'red']) if not maker.dropna().empty]

        mpf.plot(dataframe, type='candle', style=style, figsize=(100, 60),
                 savefig=f'markets_data/operations-{self.info.symbol.replace('/', '-')}.png',
        warn_too_much_data=1001,
        addplot=active_markers
        )

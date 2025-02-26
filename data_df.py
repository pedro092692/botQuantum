import pandas as pd
import mplfinance as mpf


class DataProcess:
    def __init__(self, symbol_data, info):
        self.symbol_data = symbol_data
        self.info = info

    def to_df(self) -> pd.DataFrame:
        dataframe = pd.DataFrame(self.symbol_data)
        dataframe.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        # convert timestamp in datetime object
        dataframe.date = pd.to_datetime(dataframe.date, unit='ms')
        dataframe.date = dataframe.date.dt.strftime('%d-%m-%Y %H:%M')
        return dataframe

    def save_data_to_csv(self, custom_df=pd.DataFrame()):
        if custom_df.empty:
            df = self.to_df()
            new_order = ['open', 'high', 'low', 'close', 'date', 'volume']
            df = df[new_order]
        else:
            df = custom_df
        time = df.date.iloc[-1][0:10]
        df.to_csv(f'markets_data/{self.info.symbol.replace('/', '-')}-{self.info.timeframe}-{time}.csv',
                  sep=',', header=True, index=False)

    @staticmethod
    def plot_data(df: pd.DataFrame):
        style = mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='green', down='red'))
        dataframe = df
        dataframe.date = pd.to_datetime(df.date, dayfirst=True)
        dataframe = dataframe.set_index('date')
        long_markers = df['close'].where(df['long_signal'] == 'buy', None)
        sell_markets = df['close'].where(df['profit'] == 'True', None)
        mpf.plot(dataframe, type='candle', style=style, figsize=(100, 60), savefig='operations.png',
        warn_too_much_data=1001,
        addplot=[mpf.make_addplot(long_markers, type='scatter', markersize=150, marker='^', color='orange'),
                 mpf.make_addplot(sell_markets, type='scatter', markersize=150, marker='^', color='green'),
                ]
        )


import pandas as pd


class DataProcess:
    def __init__(self, symbol_data, info):
        self.symbol_data = symbol_data
        self.info = info

    def convert_data(self) -> pd.DataFrame:
        dataframe = pd.DataFrame(self.symbol_data)
        dataframe.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        # convert timestamp in datetime object
        dataframe.date = pd.to_datetime(dataframe.date, unit='ms')
        dataframe.date = dataframe.date.dt.strftime('%d-%m-%Y %H:%M')
        return dataframe

    def save_data_to_csv(self):
        df = self.convert_data()
        new_order = ['open', 'high', 'low', 'close', 'date', 'volume']
        df = df[new_order]
        time = df.date.iloc[-1][0:10]
        df.to_csv(f'markets_data/{self.info.symbol.replace('/', '-')}-{self.info.timeframe}-{time}.csv',
                  sep=',', header=True, index=False)
import pandas as pd
import pandas_ta as ta


class Indicator:

    def __init__(self, df_inf, log=True):
        self.df_info = df_inf
        self.log = log

    def candle_indicators(self, pattern: str):
        self.df_info.ta.cdl_pattern(name=pattern, append=True)
        if self.log:
            print('Add doji pattern to data frame')
        return self.df_info

    def bollinger_bands(self, bb_len, n_std, add_to_df=False):
        bb = ta.bbands(
            self.df_info['close'],
            length=bb_len,
            std=n_std
        )
        if add_to_df:
            # add actual indicator to current symbol data
            self.df_info['lbb'] = bb.iloc[:, 0]
            self.df_info['mbb'] = bb.iloc[:, 1]
            self.df_info['ubb'] = bb.iloc[:, 2]
            if self.log:
                print('Bollinger Bands Added to symbol data frame')
        else:
            return bb

    def rsi(self, rsi_len: int, add_to_df=False):
        rsi = ta.rsi(
            self.df_info['close'],
            length=rsi_len
        )

        if add_to_df:
            # add actual indicator to current symbol data
            self.df_info['rsi'] = rsi
            if self.log:
                print('RSI Added to symbol data frame')
        else:
            return rsi

    def super_trend(self, length=10, factor=3, add_to_df=False):
        super_trend = ta.supertrend(
            high=self.df_info['high'],
            low=self.df_info['low'],
            close=self.df_info['close'],
            length=length,
            multiplier=factor
        )
        if add_to_df:
            self.df_info['upper_band'] = super_trend[:, 0]
            self.df_info['lower_band'] = super_trend[:, 1]

        if self.log:
            print('Super_trend Added to symbol data frame')


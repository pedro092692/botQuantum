import pandas as pd
import pandas_ta as ta


class Strategy:

    def __init__(self, df_inf):
        self.df_info = df_inf

    def candle_indicators(self):
        self.df_info.ta.cdl_pattern(name='doji', append=True)
        return self.df_info

import pandas as pd
import pandas_ta as ta


class Indicator:

    def __init__(self, df_inf):
        self.df_info = df_inf

    def candle_indicators(self, pattern: str):
        self.df_info.ta.cdl_pattern(name=pattern, append=True)
        return self.df_info

from indicator import Indicator

class DojiRsiBbBands:
    def __init__(self, data_df, rsi_over_bought, rsi_over_sold, tp_profit_percent=0.7, sp_loss_percent=10,
                 tsl_pct=5):
        self.df = data_df
        self.rsi_over_bought = rsi_over_bought
        self.rsi_over_sold = rsi_over_sold
        self.tp_profit = tp_profit_percent
        self.sp_loss = sp_loss_percent
        self.tsl_pct = tsl_pct
        self.indicators = Indicator(df_inf=self.df)
        self.add_indicators()

    def add_indicators(self):
        # calc indicators
        self.indicators.candle_indicators(pattern='doji')
        # bb bands
        self.indicators.bollinger_bands(bb_len=20, n_std=2.0, add_to_df=True)
        # rsi
        self.indicators.rsi(rsi_len=14, add_to_df=True)
        # update dataframe
        self.df = self.indicators.df_info

    def check_long_signal(self, index):
        over_bought_rsi = self.rsi_over_bought
        over_sold_rsi = self.rsi_over_sold
        # check for long signal in data
        if (over_bought_rsi > self.df['rsi'].iloc[index] > over_sold_rsi) and \
                (self.df['low'].iloc[index - 1] < self.df['lbb'].iloc[index - 1]) and \
                (self.df['low'].iloc[index] > self.df['lbb'].iloc[index]):

            # check if last 5 candles there was a doji
            for i in range(1, 5):
                if self.df['CDL_DOJI_10_0.1'].iloc[index - i] == 100:
                    return True

from indicator import Indicator


class SimplyStrategy:
    def __init__(self, data_df, rsi_over_bought, rsi_over_sold, tp_profit_percent=0.7, sp_loss_percent=10,
                 tsl_pct=5):
        self.df = data_df
        self.over_bought = rsi_over_bought
        self.over_sold = rsi_over_sold
        self.tp_profit = tp_profit_percent
        self.sp_loss = sp_loss_percent
        self.tsl_pct = tsl_pct
        self.indicators = Indicator(df_inf=self.df)
        self.add_indicators()

    def add_indicators(self):
        # rsi
        self.indicators.rsi(rsi_len=14, add_to_df=True)
        # update dataframe
        self.df = self.indicators.df_info

    def check_long_signal(self, index):
        if self.over_sold > self.df['rsi'].iloc[index]:
            return True

    def check_short_signal(self, index):
        if self.over_sold < self.df['rsi'].iloc[index]:
            return True

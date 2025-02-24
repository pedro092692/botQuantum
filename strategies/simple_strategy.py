class SimplyStrategy:
    def __init__(self, data_df, rsi_over_bought, rsi_over_sold, tp_profit_percent=3, sp_loss_percent=1):
        self.over_bought = rsi_over_bought
        self.over_sold = rsi_over_sold
        self.data_df = data_df
        self.tp_profit = tp_profit_percent
        self.sp_loss = sp_loss_percent

    def check_long_signal(self, index):
        if self.over_sold >= self.data_df['rsi'].iloc[index]:
            return True

    def check_short_signal(self, index):
        if self.over_bought <= self.data_df['rsi'].iloc[index]:
            return True

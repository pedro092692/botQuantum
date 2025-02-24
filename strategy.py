class Strategy:
    def __init__(self, symbol_data, strategy):
        self.df = symbol_data
        self.strategy = strategy
        self.tp_profit = strategy.tp_profit
        self.sp_loss = strategy.sp_loss

    def check_long_signal(self, index):
        return self.strategy.check_long_signal(index)

    def check_short_signal(self, index):
        return self.strategy.check_short_signal(index)

    def save_results_in_df(self):
        # add long signal column to df
        self.df['long_signal'] = ''
        self.df['short_signal'] = ''
        for index in range(len(self.df)):
            if self.check_long_signal(index=index):
                self.df.loc[index, 'long_signal'] = 'Buy'

            if self.check_short_signal(index=index):
                self.df.loc[index, 'short_signal'] = 'Sell'

class Strategy:
    def __init__(self, symbol_data, strategy):
        self.df = symbol_data
        self.strategy = strategy
        self.tp_profit = strategy.tp_profit
        self.sp_loss = strategy.sp_loss
        self.tsl_pct = strategy.tsl_pct

    def check_long_signal(self, index):
        return self.strategy.check_long_signal(index)

    def save_results_in_df(self):
        # add long signal column to df
        self.df['long_signal'] = ''
        for index in range(len(self.df)):
            if self.check_long_signal(index=index):
                self.df.loc[index, 'long_signal'] = 'Buy'

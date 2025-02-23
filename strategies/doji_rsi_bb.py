class DojiRsiBbBands:
    def __init__(self, symbol_data, rsi_over_bought, rsi_over_sold, tp_profit=1.007, sp_loss=0.9):
        self.df = symbol_data
        self.rsi_over_bought = rsi_over_bought
        self.rsi_over_sold = rsi_over_sold
        self.tp_profit = tp_profit
        self.sp_loss = sp_loss

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

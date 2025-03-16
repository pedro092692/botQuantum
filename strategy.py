class Strategy:
    def __init__(self,strategy):
        self.strategy = strategy
        self.tp_profit = strategy.tp_profit
        self.sp_loss = strategy.sp_loss
        self.tsl_pct = strategy.tsl_pct

    def check_long_signal(self, index):
        return self.strategy.check_long_signal(index)


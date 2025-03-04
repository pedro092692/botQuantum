def calc_trailing_stop_loss(df, i, price, sl_long):
    df.loc[i, 'trail_stop_loss'] = price * (1 - sl_long/100)


class Backtester:
    def __init__(self, initial_balance, leverage, inv_percent,  df, tsl=False):
        self.balance = initial_balance
        self.leverage = leverage
        self.amount = 0
        self.fee_cost = 0.02 / 100
        self.percent_inv = self.balance * (inv_percent / 100) * self.leverage
        self.profit = []
        self.drawdown = []
        self.wined_operations = 0
        self.lost_operations = 0
        self.total_operations = 0
        self.num_longs = 0
        self.num_shorts = 0
        self.is_long = False
        self.is_short = False
        self.open_price = 0
        self.take_profit_price = 0
        self.stop_loss_price = 0
        self.trailing_stop_loss = tsl
        self.df = df

    def open_position(self, price):
        # open position
        self.is_long = True
        self.total_operations += 1
        self.num_longs += 1
        self.open_price = price
        self.amount = self.percent_inv/self.open_price

    def close_position(self, price):
        if self.is_long:
            result = self.amount * (price - self.open_price)
            self.profit.append(result)
            self.balance += result

            if result > 0:
                self.wined_operations += 1
                self.drawdown.append(0)
            else:
                self.lost_operations += 1
                self.drawdown.append(result)

            self.is_long = False
            self.open_price = 0

    def set_take_profit(self, price, tp_long):
        self.take_profit_price = price * (1 + (tp_long / 100))

    def set_stop_loss(self, price, sl_long):
        self.stop_loss_price = price * (1 - (sl_long / 100))

    def reset_results(self):
        self.balance = self.balance
        self.amount = 0
        self.profit = []
        self.drawdown = []
        self.wined_operations = 0
        self.lost_operations = 0
        self.total_operations = 0
        self.num_longs = 0
        self.num_shorts = 0
        self.is_long = False
        self.is_short = False
        self.open_price = 0

    def results(self, symbol):
        profit = sum(self.profit)
        drawdown = sum(self.drawdown)

        fess = abs(profit) * self.fee_cost * self.total_operations

        results = {
            'symbol': symbol,
            'start_date': self.df['date'][0],
            'end_date': self.df['date'].iloc[-1],
            'balance': self.balance,
            'profit': profit - fess,
            'drawdown': drawdown,
            'num_operations': self.total_operations,
            'num_long': self.num_longs,
            'wined': self.wined_operations,
            'lossed': self.lost_operations,
            'winrate': 0,
            'fitness_function': 0
        }

        if self.total_operations > 0:
            winrate = self.wined_operations / self.total_operations
            results['winrate'] = winrate
            results['fitness_function'] = ((profit - abs(drawdown)) * winrate) / self.total_operations

        return results

    def backtesting(self, strategy, symbol):
        df = self.df
        high = df['high']
        close = df['close']
        low = df['low']
        df['long_signal'] = ''
        df['profit'] = ''
        df['loss'] = ''
        if self.trailing_stop_loss:
            df['trail_stop_loss'] = ''

        for i in range(len(df)):
            if self.balance > 0:
                if strategy.check_long_signal(index=i) and not self.is_long:
                    df.loc[i, 'long_signal'] = 'buy'
                    self.open_position(price=close[i])
                    self.set_take_profit(price=close[i], tp_long=strategy.tp_profit)
                    if not self.trailing_stop_loss:
                        self.set_stop_loss(price=close[i], sl_long=strategy.sp_loss)

                if self.is_long:
                    if self.trailing_stop_loss:
                        # save trailing stop loss value in df
                        calc_trailing_stop_loss(df, i=i, price=df['close'].iloc[i], sl_long=strategy.tsl_pct)
                        # calc new stop loss price
                        self.set_stop_loss(price=close[i], sl_long=strategy.tsl_pct)

                        if high[i] >= self.take_profit_price:
                            self.close_position(price=self.take_profit_price)
                            df.loc[i, 'profit'] = 'True'

                        elif low[i] < self.stop_loss_price:
                            if self.open_price < self.stop_loss_price:
                                df.loc[i, 'profit'] = 'True'
                            else:
                                df.loc[i, 'loss'] = 'True'
                            self.close_position(price=self.stop_loss_price)
                    else:
                        if high[i] >= self.take_profit_price:
                            self.close_position(price=self.take_profit_price)
                            df.loc[i, 'profit'] = 'True'
                        elif low[i] < self.stop_loss_price:
                            self.close_position(price=self.stop_loss_price)
                            df.loc[i, 'loss'] = 'True'

        return self.results(symbol)


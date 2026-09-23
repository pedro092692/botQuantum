class Backtester:
    """
    Backtester for long positions, without look-ahead bias:

    - The signal is evaluated at the close of candle i (candle already closed).
    - The entry happens at the OPEN of candle i+1 (the first price available after the signal).
    - TP / SL are only checked on candles after the entry (high/low of the entry candle
      happen after its open, so the entry candle itself is valid).
    - If TP and SL are both touched in the same candle we assume SL first (conservative).
    - If the candle opens beyond the TP / SL (gap) the fill happens at the open price.
    - The trailing stop only moves up and is computed with closes already known
      (the stop used on candle i comes from closes up to i-1).
    - Fees are charged on the notional of every entry and every exit.
    """

    def __init__(self, initial_balance, leverage, inv_percent, df, tsl=False, fee_pct=0.1, slippage_pct=0.0,
                 min_trades=5):
        self.initial_balance = initial_balance
        self.leverage = leverage
        self.inv_percent = inv_percent
        # fee per side in % (binance spot taker = 0.1%, with BNB = 0.075%, futures maker = 0.02%)
        self.fee_cost = fee_pct / 100
        self.slippage = slippage_pct / 100
        self.min_trades = min_trades
        self.trailing_stop_loss = tsl
        self.df = df
        self.reset_results()

    def reset_results(self):
        self.balance = self.initial_balance
        self.amount = 0
        self.profit = []
        self.fees_paid = 0
        self.equity_curve = []
        self.wined_operations = 0
        self.lost_operations = 0
        self.total_operations = 0
        self.num_longs = 0
        self.num_shorts = 0
        self.is_long = False
        self.is_short = False
        self.open_price = 0
        self.entry_fee = 0
        self.take_profit_price = 0
        self.stop_loss_price = 0

    def open_position(self, price):
        # buy a bit worse than the price because of slippage
        price = price * (1 + self.slippage)
        notional = self.balance * (self.inv_percent / 100) * self.leverage
        self.is_long = True
        self.total_operations += 1
        self.num_longs += 1
        self.open_price = price
        self.amount = notional / price
        self.entry_fee = notional * self.fee_cost
        self.fees_paid += self.entry_fee
        self.balance -= self.entry_fee

    def close_position(self, price):
        if not self.is_long:
            return None
        # sell a bit worse than the price because of slippage
        price = price * (1 - self.slippage)
        exit_fee = self.amount * price * self.fee_cost
        self.fees_paid += exit_fee
        gross = self.amount * (price - self.open_price)
        self.balance += gross - exit_fee
        # net result of the trade includes entry and exit fees
        result = gross - exit_fee - self.entry_fee
        self.profit.append(result)

        if result > 0:
            self.wined_operations += 1
        else:
            self.lost_operations += 1

        self.is_long = False
        self.open_price = 0
        self.amount = 0
        self.entry_fee = 0
        return result

    def set_take_profit(self, price, tp_long):
        self.take_profit_price = price * (1 + (tp_long / 100))

    def set_stop_loss(self, price, sl_long):
        self.stop_loss_price = price * (1 - (sl_long / 100))

    def update_trailing_stop(self, price, tsl_pct):
        # trailing stop only moves up, never down
        new_stop = price * (1 - (tsl_pct / 100))
        self.stop_loss_price = max(self.stop_loss_price, new_stop)

    def max_drawdown(self):
        """Biggest drop of the equity curve from a previous peak (absolute value and %)."""
        peak = self.initial_balance
        max_dd = 0
        max_dd_pct = 0
        for equity in self.equity_curve:
            peak = max(peak, equity)
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd / peak * 100
        return max_dd, max_dd_pct

    def results(self, symbol):
        profit = sum(self.profit)
        max_dd, max_dd_pct = self.max_drawdown()
        close = self.df['close']

        results = {
            'symbol': symbol,
            'start_date': self.df['date'].iloc[0],
            'end_date': self.df['date'].iloc[-1],
            'balance': self.balance,
            'profit': profit,
            'profit_pct': profit / self.initial_balance * 100,
            'buy_and_hold_pct': (close.iloc[-1] / close.iloc[0] - 1) * 100,
            'fees_paid': self.fees_paid,
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd_pct,
            'num_operations': self.total_operations,
            'num_long': self.num_longs,
            'wined': self.wined_operations,
            'lossed': self.lost_operations,
            'winrate': 0,
            'fitness_function': float('-inf')
        }

        if self.total_operations > 0:
            results['winrate'] = self.wined_operations / self.total_operations
        # with very few trades the result is luck, not a strategy
        if self.total_operations >= self.min_trades:
            results['fitness_function'] = profit - max_dd

        return results

    def backtesting(self, strategy, symbol):
        self.reset_results()
        df = self.df
        open_ = df['open'].to_numpy()
        high = df['high'].to_numpy()
        low = df['low'].to_numpy()
        close = df['close'].to_numpy()
        df['long_signal'] = ''
        df['profit'] = ''
        df['loss'] = ''
        if self.trailing_stop_loss:
            df['trail_stop_loss'] = ''

        pending_entry = False
        n = len(df)

        for i in range(n):
            # 1) entry at the open of the candle after the signal
            if pending_entry:
                pending_entry = False
                self.open_position(price=open_[i])
                df.loc[i, 'long_signal'] = 'buy'
                self.set_take_profit(price=self.open_price, tp_long=strategy.tp_profit)
                sl_pct = strategy.tsl_pct if self.trailing_stop_loss else strategy.sp_loss
                self.set_stop_loss(price=self.open_price, sl_long=sl_pct)

            # 2) exits, checked with this candle's prices (all happen after the entry)
            if self.is_long:
                if self.trailing_stop_loss:
                    df.loc[i, 'trail_stop_loss'] = self.stop_loss_price

                exit_price = None
                # stop loss first: if both are touched in the same candle we can't know the order
                if open_[i] <= self.stop_loss_price:
                    exit_price = open_[i]  # gap down: filled at the open, not at the stop
                elif low[i] <= self.stop_loss_price:
                    exit_price = self.stop_loss_price
                elif open_[i] >= self.take_profit_price:
                    exit_price = open_[i]  # gap up: filled at the open
                elif high[i] >= self.take_profit_price:
                    exit_price = self.take_profit_price

                if exit_price is not None:
                    result = self.close_position(price=exit_price)
                    df.loc[i, 'profit' if result > 0 else 'loss'] = 'True'
                elif self.trailing_stop_loss:
                    # the close of this candle is known now, the new stop applies from the next candle
                    self.update_trailing_stop(price=close[i], tsl_pct=strategy.tsl_pct)

            # 3) equity at the close of the candle (mark to market)
            equity = self.balance
            if self.is_long:
                equity += self.amount * (close[i] - self.open_price)
            self.equity_curve.append(equity)

            # 4) signal with the closed candle i -> entry at candle i+1
            if not self.is_long and self.balance > 0 and i < n - 1:
                if strategy.check_long_signal(index=i):
                    pending_entry = True

        # close any position still open at the last close
        if self.is_long:
            result = self.close_position(price=close[-1])
            df.loc[n - 1, 'profit' if result > 0 else 'loss'] = 'True'
            self.equity_curve[-1] = self.balance

        return self.results(symbol)

from indicator import Indicator


class DojiRsiBbBands:
    def __init__(self, data_df, rsi_over_bought, rsi_over_sold, tp_profit_percent=0.7, sp_loss_percent=10,
                 tsl_pct=5, bb_len=20, n_std=2.0, rsi_len=14, log=True):
        self.df = data_df
        self.rsi_over_bought = rsi_over_bought
        self.rsi_over_sold = rsi_over_sold
        self.tp_profit = tp_profit_percent
        self.sp_loss = sp_loss_percent
        self.tsl_pct = tsl_pct
        self.indicators = Indicator(df_inf=self.df, log=log)
        self.bb_len = bb_len
        self.n_std = n_std
        self.rsi_len = rsi_len
        self.add_indicators()
        self.signals = self.calc_long_signals()

    def add_indicators(self):
        # calc indicators
        self.indicators.candle_indicators(pattern='doji')
        # bb bands
        self.indicators.bollinger_bands(bb_len=self.bb_len, n_std=self.n_std, add_to_df=True)
        # rsi
        self.indicators.rsi(rsi_len=self.rsi_len, add_to_df=True)
        # update dataframe
        self.df = self.indicators.df_info

    def calc_long_signals(self):
        # only shift(1) (previous candle) is allowed here, never shift(-1): that would read the future.
        # NaN comparisons (indicator warm-up and first candle) are False, so no signal there
        df = self.df
        rsi_ok = (df['rsi'] < self.rsi_over_bought) & (df['rsi'] > self.rsi_over_sold)
        prev_low_below_bb = df['low'].shift(1) < df['lbb'].shift(1)
        low_back_inside_bb = df['low'] > df['lbb']
        # check if last 5 candles there was a doji
        # doji_recent = (df['CDL_DOJI_10_0.1'].shift(1).rolling(4).max() == 100)
        return (rsi_ok & prev_low_below_bb & low_back_inside_bb).to_numpy()

    def check_long_signal(self, index):
        return bool(self.signals[index])

import unittest

import numpy as np
import pandas as pd

from backtester import Backtester
from data_df import train_test_split
from genetic_algorithm import Individual, Population
from get_data import drop_unclosed_candles
from strategies.doji_rsi_bb import DojiRsiBbBands


def make_df(candles):
    """candles: list of (open, high, low, close)."""
    df = pd.DataFrame(candles, columns=['open', 'high', 'low', 'close'])
    df['date'] = [f'c{i}' for i in range(len(df))]
    df['volume'] = 1.0
    return df


def random_walk_df(n=600, seed=1):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[100], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.003, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.003, n))
    return make_df(list(zip(open_, high, low, close)))


class FakeStrategy:
    def __init__(self, signal_indexes, tp=1.0, sl=1.0, tsl=1.0):
        self.signal_indexes = set(signal_indexes)
        self.tp_profit = tp
        self.sp_loss = sl
        self.tsl_pct = tsl

    def check_long_signal(self, index):
        return index in self.signal_indexes


def backtest(df, strategy, **kwargs):
    params = dict(initial_balance=1000, leverage=1, inv_percent=100, df=df, fee_pct=0)
    params.update(kwargs)
    bt = Backtester(**params)
    return bt, bt.backtesting(strategy, 'TEST')


class BacktesterTest(unittest.TestCase):

    def test_entry_is_next_open_and_signal_candle_high_is_ignored(self):
        # signal candle 0 has a high 1% above its close: before it was a fake +TP
        df = make_df([(100, 101, 99.9, 100), (100.2, 100.3, 100.1, 100.2), (100.2, 100.3, 100.1, 100.2)])
        bt, res = backtest(df, FakeStrategy([0], tp=0.7, sl=0.3))
        self.assertEqual(bt.df.loc[0, 'long_signal'], '')
        self.assertEqual(bt.df.loc[1, 'long_signal'], 'buy')
        self.assertEqual(bt.df.loc[0, 'profit'], '')
        # position closed at the last close: 100.2 -> 100.2
        self.assertAlmostEqual(res['profit'], 0)

    def test_signal_on_last_candle_does_not_trade(self):
        df = make_df([(100, 101, 99, 100), (100, 101, 99, 100)])
        _, res = backtest(df, FakeStrategy([1]))
        self.assertEqual(res['num_operations'], 0)

    def test_stop_loss_first_when_tp_and_sl_in_same_candle(self):
        # entry 100 on candle 1, candle 2 touches both TP (101) and SL (99)
        df = make_df([(100, 100, 100, 100), (100, 100.5, 99.5, 100), (100, 102, 98, 100)])
        _, res = backtest(df, FakeStrategy([0], tp=1, sl=1))
        self.assertEqual(res['lossed'], 1)
        self.assertAlmostEqual(res['profit'], 10 * (99 - 100))

    def test_gap_down_fills_at_open_not_at_stop(self):
        df = make_df([(100, 100, 100, 100), (100, 100.5, 99.5, 100), (95, 96, 94, 95)])
        _, res = backtest(df, FakeStrategy([0], tp=1, sl=1))
        self.assertAlmostEqual(res['profit'], 10 * (95 - 100))

    def test_trailing_stop_uses_previous_close_and_never_goes_down(self):
        closes = [100, 100, 102, 104, 103, 101, 100]
        candles = [(c, c + 0.1, c - 0.1, c) for c in closes]
        df = make_df(candles)
        bt, _ = backtest(df, FakeStrategy([0], tp=50, tsl=5), tsl=True)
        stops = [s for s in bt.df['trail_stop_loss'] if s != '']
        self.assertEqual(stops, sorted(stops))
        # stop used on candle 4 comes from the max close up to candle 3 (104), not from close[4]
        self.assertAlmostEqual(bt.df.loc[4, 'trail_stop_loss'], 104 * 0.95)

    def test_fees_charged_on_entry_and_exit(self):
        df = make_df([(100, 100, 100, 100), (100, 100.5, 99.5, 100), (100, 101.5, 100, 101)])
        bt, res = backtest(df, FakeStrategy([0], tp=1, sl=1), fee_pct=0.1)
        # 10 BTC: gross +10, fees 1000*0.001 + 1010*0.001
        self.assertAlmostEqual(res['fees_paid'], 1.0 + 1.01)
        self.assertAlmostEqual(res['profit'], 10 - 2.01)
        self.assertAlmostEqual(res['balance'], 1000 + 10 - 2.01)

    def test_max_drawdown_from_equity_curve(self):
        bt = Backtester(1000, 1, 100, make_df([(1, 1, 1, 1)]))
        bt.equity_curve = [1000, 1100, 900, 1200, 1000]
        dd, dd_pct = bt.max_drawdown()
        self.assertAlmostEqual(dd, 200)
        self.assertAlmostEqual(dd_pct, 200 / 1100 * 100)

    def test_reset_results_restores_balance(self):
        df = make_df([(100, 100, 100, 100), (100, 100.5, 99.5, 100), (95, 96, 94, 95)])
        bt, first = backtest(df, FakeStrategy([0]))
        second = bt.backtesting(FakeStrategy([0]), 'TEST')
        self.assertEqual(first['balance'], second['balance'])


class StrategyLookAheadTest(unittest.TestCase):

    def test_signals_do_not_change_when_future_candles_are_removed(self):
        # if a signal at candle i uses the future, cutting the data after i would change it
        df = random_walk_df()
        full = DojiRsiBbBands(df.copy(), rsi_over_bought=70, rsi_over_sold=30, log=False).signals
        self.assertTrue(full.any(), 'the synthetic data should produce some signals')
        for k in (100, 250, 400, 599):
            partial = DojiRsiBbBands(df.iloc[:k].copy(), rsi_over_bought=70, rsi_over_sold=30, log=False).signals
            np.testing.assert_array_equal(partial, full[:k])

    def test_trades_do_not_change_when_future_candles_are_removed(self):
        df = random_walk_df(seed=7)
        def entries(data):
            plan = DojiRsiBbBands(data.copy(), rsi_over_bought=70, rsi_over_sold=30, tp_profit_percent=0.5,
                                  sp_loss_percent=0.5, log=False)
            bt = Backtester(1000, 1, 100, plan.df, fee_pct=0.1)
            bt.backtesting(plan, 'TEST')
            return list(bt.df.index[bt.df['long_signal'] == 'buy'])
        full = entries(df)
        partial = entries(df.iloc[:300])
        self.assertEqual(partial, [i for i in full if i < 300])


class DataTest(unittest.TestCase):

    def test_drop_unclosed_candles(self):
        minute = 60_000
        ohlcv = [[0, 1, 1, 1, 1, 1], [minute, 1, 1, 1, 1, 1], [2 * minute, 1, 1, 1, 1, 1]]
        # at 2.5 minutes the third candle is still open
        self.assertEqual(len(drop_unclosed_candles(ohlcv, '1m', now_ms=int(2.5 * minute))), 2)
        self.assertEqual(len(drop_unclosed_candles(ohlcv, '1m', now_ms=3 * minute)), 3)

    def test_train_test_split_keeps_time_order(self):
        df = random_walk_df(n=100)
        train, test = train_test_split(df, train_pct=70)
        self.assertEqual(len(train), 70)
        self.assertEqual(len(test), 30)
        self.assertEqual(train.date.iloc[-1], 'c69')
        self.assertEqual(test.date.iloc[0], 'c70')


class GeneticAlgorithmTest(unittest.TestCase):

    def test_each_individual_has_its_own_fitness(self):
        P = Population(10, 3, [(0, 100)] * 3, n_best=4, mutation_rate=0.3)
        P.evaluate(lambda genes: {'fitness_function': sum(genes)})
        fitness = [ind.fitness for ind in P.population]
        self.assertEqual(fitness, sorted(fitness, reverse=True))
        self.assertEqual(P.best().fitness, max(sum(ind.genes) for ind in P.population))

    def test_crossover_does_not_modify_parents_and_keeps_elite(self):
        np.random.seed(0)
        P = Population(10, 3, [(0, 100)] * 3, n_best=4, mutation_rate=1, n_elite=1)
        P.evaluate(lambda genes: {'fitness_function': sum(genes)})
        parents = P.selection()
        parents_genes = [list(p.genes) for p in parents]
        P.crossover()
        self.assertEqual([list(p.genes) for p in parents], parents_genes)
        self.assertEqual(len(P.population), 10)
        self.assertEqual(P.population[0].genes, parents_genes[0])
        P.mutation()
        self.assertEqual(P.population[0].genes, parents_genes[0])

    def test_individual_genes_are_copied(self):
        genes = [1, 2, 3]
        ind = Individual(3, [(0, 10)] * 3, genes=genes)
        ind.genes[0] = 9
        self.assertEqual(genes, [1, 2, 3])


if __name__ == '__main__':
    unittest.main()

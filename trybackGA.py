from genetic_algorithm import Population
from get_data import GetData
from data_df import DataProcess, load_csv, train_test_split
from strategies.doji_rsi_bb import DojiRsiBbBands
from strategy import Strategy
from backtester import Backtester

# ---------------- config ----------------
SYMBOL = 'btc'
TIMEFRAME = '15m'
# 'historical': DATE_START -> DATE_END | 'csv': file in CSV_PATH
DATA_SOURCE = 'csv'
DATE_START = '01/01/2025'
DATE_END = '01/04/2025'
CSV_PATH = 'markets_data/BTC-USDT-15m-01-04-2025.csv'
TRAIN_PCT = 70
GENERATIONS = 30
GENERATION_SIZE = 50
# -----------------------------------------

# genes: rsi_over_bought, rsi_over_sold, bb_len, n_std (x10), rsi_len
GENE_RANGES = [(50, 100), (0, 50), (10, 60), (10, 31), (5, 40)]


def decode(genes):
    return dict(rsi_over_bought=genes[0], rsi_over_sold=genes[1], bb_len=genes[2],
                n_std=genes[3] / 10, rsi_len=genes[4])


def run(df, genes):
    plan = DojiRsiBbBands(data_df=df.copy(), tp_profit_percent=0.7, sp_loss_percent=0.3, tsl_pct=3,
                          log=False, **decode(genes))
    backtester = Backtester(initial_balance=1000, leverage=1, inv_percent=100, df=plan.df,
                            tsl=True, fee_pct=0.1, slippage_pct=0.02)
    return backtester.backtesting(strategy=Strategy(strategy=plan), symbol=SYMBOL)


if __name__ == '__main__':
    exchange = GetData(exchange='binance', symbol=SYMBOL, timeframe=TIMEFRAME, candles=1000)
    if DATA_SOURCE == 'historical':
        df = DataProcess(symbol_data=exchange.get_ohlcv_historical(date_start=DATE_START, date_end=DATE_END),
                         info=exchange).to_df()
    else:
        df = load_csv(CSV_PATH)

    # the GA only sees the train data, the test data is used once at the end
    train_df, test_df = train_test_split(df, train_pct=TRAIN_PCT)
    print(f'train: {train_df.date.iloc[0]} -> {train_df.date.iloc[-1]} ({len(train_df)} candles)')
    print(f'test:  {test_df.date.iloc[0]} -> {test_df.date.iloc[-1]} ({len(test_df)} candles)')

    P = Population(
        generation_size=GENERATION_SIZE,
        n_genes=len(GENE_RANGES),
        gene_ranges=GENE_RANGES,
        n_best=10,
        mutation_rate=0.2,
        n_elite=2
    )

    for x in range(GENERATIONS):
        P.evaluate(lambda genes: run(train_df, genes))
        best = P.best()
        print(f'GENERATION {x}: best fitness={best.fitness:.2f} profit={best.results["profit"]:.2f} '
              f'trades={best.results["num_operations"]} genes={decode(best.genes)}')
        if x < GENERATIONS - 1:
            P.crossover()
            P.mutation()

    best = P.best()
    print('\nBEST INDIVIDUAL', decode(best.genes))
    print('TRAIN (in-sample):', best.results)
    # if the test is much worse than the train, the parameters are overfitted
    print('TEST (out-of-sample):', run(test_df, best.genes))

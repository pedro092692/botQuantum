from genetic_algorithm import Population
from get_data import GetData
from data_df import DataProcess, load_csv, train_test_split
from strategies.doji_rsi_bb import DojiRsiBbBands
from strategy import Strategy
from backtester import Backtester

# ---------------- config (only when running this file directly, the CLI asks for it) ----------------
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
# ----------------------------------------------------------------------------------------------------

# genes: rsi_over_bought, rsi_over_sold, bb_len, n_std (x10), rsi_len
GENE_RANGES = [(50, 100), (0, 50), (10, 60), (10, 31), (5, 40)]
# fixed parameters (not optimized yet)
FIXED_PARAMS = dict(tp_profit_percent=0.7, sp_loss_percent=0.3, tsl_pct=3)


def decode(genes):
    return dict(rsi_over_bought=int(genes[0]), rsi_over_sold=int(genes[1]), bb_len=int(genes[2]),
                n_std=genes[3] / 10, rsi_len=int(genes[4]))


def run(df, genes, symbol='-'):
    plan = DojiRsiBbBands(data_df=df.copy(), log=False, **FIXED_PARAMS, **decode(genes))
    backtester = Backtester(initial_balance=1000, leverage=1, inv_percent=100, df=plan.df,
                            tsl=True, fee_pct=0.1, slippage_pct=0.02)
    return backtester.backtesting(strategy=Strategy(strategy=plan), symbol=symbol)


def optimize(df, generations=GENERATIONS, generation_size=GENERATION_SIZE, train_pct=TRAIN_PCT,
             on_generation=None):
    """
    Optimize the genes with the train data (first train_pct %) and validate the best individual
    once with the test data (the rest). on_generation(number, best_individual) is called every generation.
    """
    # the GA only sees the train data, the test data is used once at the end
    train_df, test_df = train_test_split(df, train_pct=train_pct)

    P = Population(
        generation_size=generation_size,
        n_genes=len(GENE_RANGES),
        gene_ranges=GENE_RANGES,
        n_best=min(10, generation_size),
        mutation_rate=0.2,
        n_elite=2
    )

    for x in range(generations):
        P.evaluate(lambda genes: run(train_df, genes))
        if on_generation:
            on_generation(x, P.best())
        if x < generations - 1:
            P.crossover()
            P.mutation()

    best = P.best()
    return {
        'params': {**decode(best.genes), **FIXED_PARAMS},
        'train': best.results,
        # if the test is much worse than the train, the parameters are overfitted
        'test': run(test_df, best.genes),
    }


if __name__ == '__main__':
    exchange = GetData(exchange='binance', symbol=SYMBOL, timeframe=TIMEFRAME, candles=1000)
    if DATA_SOURCE == 'historical':
        df = DataProcess(symbol_data=exchange.get_ohlcv_historical(date_start=DATE_START, date_end=DATE_END),
                         info=exchange).to_df()
    else:
        df = load_csv(CSV_PATH)

    def log_generation(x, best):
        print(f'GENERATION {x}: best fitness={best.fitness:.2f} profit={best.results["profit"]:.2f} '
              f'trades={best.results["num_operations"]} genes={decode(best.genes)}')

    result = optimize(df, on_generation=log_generation)
    print('\nBEST INDIVIDUAL', result['params'])
    print('TRAIN (in-sample):', result['train'])
    print('TEST (out-of-sample):', result['test'])

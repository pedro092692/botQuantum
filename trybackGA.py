from genetic_algorithm import Population
from get_data import GetData
from data_df import DataProcess
from strategies.doji_rsi_bb import DojiRsiBbBands
from strategy import Strategy

# Get exchange
exchange = GetData(exchange='binance', symbol='xrp', timeframe='1m', candles=1000)

# Get ohlcv data from exchange
symbol_data = DataProcess(symbol_data=exchange.get_ohlcv(), info=exchange)
df = symbol_data.to_df()

# strategy blueprint (the class itself)
strategy_blueprint = DojiRsiBbBands

P = Population(
    generation_size=20,
    n_genes=5,
    gene_ranges=[(50, 100), (0, 50), (20, 100), (10, 30), (8, 100)],
    n_best=10,
    mutation_rate=0.3,
    strategy_blueprint=strategy_blueprint
)

number_of_generations = 20

print('first test algo strategy')

for x in range(number_of_generations):
    # Evaluate fitness and select the best individuals
    P.selection(df=df)

    print('\n GENERATION ', x)
    print('__________________')
    print('\n\n')
    print('BEST INDIVIDUAL')
    best_individual = P.population[0]
    genes_best = best_individual.genes
    plan_best = strategy_blueprint(data_df=df,
                                     rsi_over_bought=genes_best[0],
                                     rsi_over_sold=genes_best[1],
                                     bb_len=genes_best[2],
                                     n_std=genes_best[3] / 10,
                                     rsi_len=genes_best[4],
                                     log_indicators=False)
    strategy_best = Strategy(strategy=plan_best)
    print(best_individual.backtester.results(symbol='-', df=strategy_best.df))
    print(genes_best)

    print('WORST INDIVIDUAL')
    worst_individual = P.population[-1]
    genes_worst = worst_individual.genes
    plan_worst = strategy_blueprint(data_df=df,
                                      rsi_over_bought=genes_worst[0],
                                      rsi_over_sold=genes_worst[1],
                                      bb_len=genes_worst[2],
                                      n_std=genes_worst[3] / 10,
                                      rsi_len=genes_worst[4],
                                      log_indicators=False)
    strategy_worst = Strategy(strategy=plan_worst)
    print(worst_individual.backtester.results(symbol='-', df=strategy_worst.df))
    print(genes_worst)
    print('\n\n')

    P.crossover(df=df)
    P.mutation()
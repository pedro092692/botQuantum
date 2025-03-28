from genetic_algorithm import Population
from get_data import GetData
from data_df import DataProcess
from strategies.doji_rsi_bb import DojiRsiBbBands
from strategy import Strategy
from backtester import Backtester

# Get exchange
exchange = GetData(exchange='binance', symbol='btc', timeframe='1m', candles=1000)

# Get ohlcv data from exchange
# symbol_data = DataProcess(symbol_data=exchange.get_ohlcv_historical(date_start='09/03/2025', date_end='15/03/2025'),
#                           info=exchange)
symbol_data = DataProcess(symbol_data=exchange.get_ohlcv(), info=exchange)


# strategy
# plan = SimplyStrategy(data_df=symbol_data.to_df(), rsi_over_bought=70, rsi_over_sold=30)
plan = DojiRsiBbBands(data_df=symbol_data.to_df(), rsi_over_bought=60, rsi_over_sold=40, tp_profit_percent=0.7,
                      sp_loss_percent=0.3, tsl_pct=3)

backtester = Backtester(initial_balance=1000, leverage=1, inv_percent=100, df=plan.df,
                        tsl=True)

P = Population(
    generation_size=50,
    n_genes=5,
    gene_ranges=[(50, 100), (0, 50), (20, 100), (10, 30), (8, 100)],
    n_best=10,
    mutation_rate=0.3,
    backtester=backtester
)

population = P.population
number_of_generations = 50

print('first test algo strategy')

for x in range(number_of_generations):
    for individual in population:
        individual.backtester.reset_results()
        genes = individual.genes
        plan = DojiRsiBbBands(data_df=symbol_data.to_df(),
                                  rsi_over_bought=genes[0],
                                  rsi_over_sold=genes[1],
                                  bb_len=genes[2],
                                  n_std=genes[3],
                                  rsi_len=genes[4])
        strategy = Strategy(strategy=plan)
        individual.backtester.backtesting(strategy=strategy, symbol='-')

    P.crossover()
    P.mutation()
    print('\n GENERATION ', x)
    print('__________________')
    print('\n\n')
    print('BEST INDIVIDUAL')
    print(P.population[0].backtester.results(symbol='-'))
    print('WORST INDIVIDUAL')
    print(P.population[-1].backtester.results(symbol='-'))
    print('\n\n')
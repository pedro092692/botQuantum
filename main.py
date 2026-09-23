from get_data import GetData
from data_df import DataProcess, load_csv
from strategy import Strategy
from strategies.simple_strategy import SimplyStrategy
from strategies.doji_rsi_bb import DojiRsiBbBands
from backtester import Backtester

# ---------------- config ----------------
SYMBOL = 'btc'
TIMEFRAME = '15m'
# 'live': last CANDLES candles | 'historical': DATE_START -> DATE_END | 'csv': file in CSV_PATH
DATA_SOURCE = 'historical'
CANDLES = 1000
DATE_START = '01/01/2025'
DATE_END = '01/04/2025'
CSV_PATH = 'markets_data/BTC-USDT-15m-01-04-2025.csv'
SAVE_CSV = True
PLOT = False
# -----------------------------------------

# Get exchange
exchange = GetData(exchange='binance', symbol=SYMBOL, timeframe=TIMEFRAME, candles=CANDLES)

# Get ohlcv data
if DATA_SOURCE == 'live':
    symbol_data = DataProcess(symbol_data=exchange.get_ohlcv(), info=exchange)
    df = symbol_data.to_df()
elif DATA_SOURCE == 'historical':
    symbol_data = DataProcess(symbol_data=exchange.get_ohlcv_historical(date_start=DATE_START, date_end=DATE_END),
                              info=exchange)
    df = symbol_data.to_df()
    if SAVE_CSV:
        # save raw candles to reuse them offline with DATA_SOURCE = 'csv'
        symbol_data.save_data_to_csv()
else:
    symbol_data = DataProcess(symbol_data=None, info=exchange)
    df = load_csv(CSV_PATH)

# strategy
# plan = SimplyStrategy(data_df=df, rsi_over_bought=70, rsi_over_sold=30)
plan = DojiRsiBbBands(data_df=df, rsi_over_bought=60, rsi_over_sold=40, tp_profit_percent=0.7,
                      sp_loss_percent=0.3, tsl_pct=3)

# set up strategy
strategy = Strategy(strategy=plan)

# backtesting
backtester = Backtester(initial_balance=1000, leverage=1, inv_percent=100, df=plan.df,
                        tsl=True, fee_pct=0.1, slippage_pct=0.02)
# print results
for key, value in backtester.backtesting(strategy=strategy, symbol=exchange.symbol).items():
    print(f'{key:>18}: {value}')

# save operations and plot them
if PLOT:
    symbol_data.plot_data(df=plan.df)

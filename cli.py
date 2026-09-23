"""
Interactive menu to use the bot without editing code:
    python main.py
"""
import glob
import os
import subprocess
import sys
from datetime import datetime
from types import SimpleNamespace

MARKETS_DIR = 'markets_data'
TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
LINE = '-' * 60


# ---------------- input helpers ----------------

def ask(label, default=None, cast=str, validate=None):
    """Ask for a value. Enter keeps the default. Repeats until the value is valid."""
    suffix = f' [{default}]' if default is not None else ''
    while True:
        raw = input(f'{label}{suffix}: ').strip()
        if raw == '' and default is not None:
            raw = str(default)
        if raw == '':
            print('  Este valor es obligatorio.')
            continue
        try:
            value = cast(raw)
        except ValueError:
            print(f'  Valor invalido: "{raw}"')
            continue
        if validate:
            error = validate(value)
            if error:
                print(f'  {error}')
                continue
        return value


def ask_number(label, default):
    # the type comes from the default: 20 -> int, 2.0 -> float
    cast = int if isinstance(default, int) else lambda raw: float(raw.replace(',', '.'))
    return ask(label, default, cast)


def ask_yes_no(label, default=False):
    answer = ask(f'{label} (s/n)', 's' if default else 'n', lambda raw: raw.lower(),
                 lambda v: None if v in ('s', 'si', 'y', 'n', 'no') else 'Responde s o n')
    return answer in ('s', 'si', 'y')


def ask_choice(label, options):
    """options: list of (value, text). Returns the chosen value."""
    print(label)
    for i, (_, text) in enumerate(options, start=1):
        print(f'  {i}. {text}')
    index = ask('Opcion', None, int,
                lambda v: None if 1 <= v <= len(options) else f'Elige un numero entre 1 y {len(options)}')
    return options[index - 1][0]


def parse_date(raw):
    return datetime.strptime(raw, '%d/%m/%Y')


# ---------------- output helpers ----------------

RESULT_LABELS = [
    ('symbol', 'Simbolo', '{}'),
    ('start_date', 'Desde', '{}'),
    ('end_date', 'Hasta', '{}'),
    ('balance', 'Balance final', '{:.2f} USDT'),
    ('profit', 'Ganancia neta', '{:.2f} USDT'),
    ('profit_pct', 'Ganancia neta %', '{:.2f} %'),
    ('buy_and_hold_pct', 'Comprar y mantener %', '{:.2f} %'),
    ('fees_paid', 'Comisiones pagadas', '{:.2f} USDT'),
    ('max_drawdown_pct', 'Max. drawdown %', '{:.2f} %'),
    ('num_operations', 'Operaciones', '{}'),
    ('wined', 'Ganadoras', '{}'),
    ('lossed', 'Perdedoras', '{}'),
    ('winrate', 'Winrate', '{:.1%}'),
]


def print_results(results, title='RESULTADOS'):
    print(f'\n{title}\n{LINE}')
    for key, label, fmt in RESULT_LABELS:
        print(f'  {label:<22} {fmt.format(results[key])}')
    if results['num_operations'] < 30:
        print('  ! Menos de 30 operaciones: el resultado puede ser pura suerte.')
    if results['profit_pct'] < results['buy_and_hold_pct']:
        print('  ! La estrategia no supera a comprar y mantener.')


def list_csv_files():
    files = sorted(glob.glob(os.path.join(MARKETS_DIR, '*.csv')))
    # operations-*.csv are backtest outputs, not market data
    return [f for f in files if not os.path.basename(f).startswith('operations-')]


def choose_csv():
    files = list_csv_files()
    if not files:
        print('No hay datos descargados. Usa primero la opcion "Descargar datos".')
        return None
    return ask_choice('Datos a usar:', [(f, os.path.basename(f)) for f in files])


# ---------------- actions ----------------

def download_data():
    from get_data import GetData
    from data_df import DataProcess

    print(f'\nDESCARGAR DATOS DE BINANCE\n{LINE}')
    symbol = ask('Moneda (se compara contra USDT)', 'btc', lambda raw: raw.lower())
    timeframe = ask('Timeframe (' + ', '.join(TIMEFRAMES) + ')', '15m', str,
                    lambda v: None if v in TIMEFRAMES else 'Timeframe no soportado')
    start = ask('Fecha inicio (dd/mm/aaaa)', None, parse_date)
    today = datetime.now().strftime('%d/%m/%Y')
    end = ask('Fecha fin (dd/mm/aaaa)', today, parse_date,
              lambda v: None if v > start else 'La fecha fin debe ser posterior a la de inicio')

    exchange = GetData(exchange='binance', symbol=symbol, timeframe=timeframe, candles=1000)
    print('Descargando... (varios meses en 1m puede tardar unos minutos)')
    ohlcv = exchange.get_ohlcv_historical(date_start=start.strftime('%d/%m/%Y'),
                                          date_end=end.strftime('%d/%m/%Y'))
    if not ohlcv:
        print('Binance no devolvio velas para ese rango.')
        return
    path = DataProcess(symbol_data=ohlcv, info=exchange).save_data_to_csv()
    print(f'Listo: {len(ohlcv)} velas guardadas en {path}')


def run_backtest():
    from backtester import Backtester
    from data_df import DataProcess, load_csv
    from strategies import STRATEGIES
    from strategy import Strategy

    print(f'\nBACKTEST\n{LINE}')
    path = choose_csv()
    if not path:
        return
    key = ask_choice('Estrategia:', [(k, s['name']) for k, s in STRATEGIES.items()])
    spec = STRATEGIES[key]

    print('\nParametros de la estrategia (Enter = valor por defecto)')
    params = {name: ask_number(f'  {label}', default) for name, label, default in spec['params']}

    print('\nParametros del backtester')
    balance = ask_number('  Balance inicial USDT', 1000.0)
    tsl = ask_yes_no('  Usar trailing stop en vez de stop loss fijo?', True)
    fee = ask_number('  Comision por lado % (spot 0.1, BNB 0.075, futuros maker 0.02)', 0.1)
    slippage = ask_number('  Slippage %', 0.02)

    df = load_csv(path)
    plan = spec['cls'](data_df=df, log=False, **params)
    backtester = Backtester(initial_balance=balance, leverage=1, inv_percent=100, df=plan.df,
                            tsl=tsl, fee_pct=fee, slippage_pct=slippage)
    stem = os.path.splitext(os.path.basename(path))[0]
    results = backtester.backtesting(strategy=Strategy(strategy=plan), symbol=stem)
    print_results(results)

    if ask_yes_no('\nGuardar las operaciones en CSV?'):
        out = os.path.join(MARKETS_DIR, f'operations-{stem}.csv')
        plan.df.to_csv(out, index=False)
        print(f'Guardado en {out}')
    if ask_yes_no('Generar grafico de las operaciones? (tarda con muchos datos)'):
        DataProcess(symbol_data=None, info=SimpleNamespace(symbol=stem)).plot_data(df=plan.df)
        print(f'Guardado en {MARKETS_DIR}/operations-{stem}.png')


def run_optimizer():
    from data_df import load_csv
    from trybackGA import optimize, decode

    print(f'\nOPTIMIZAR (algoritmo genetico, estrategia RSI + Bandas de Bollinger)\n{LINE}')
    path = choose_csv()
    if not path:
        return
    generations = ask('Generaciones', 30, int, lambda v: None if v >= 1 else 'Minimo 1')
    size = ask('Individuos por generacion', 50, int, lambda v: None if v >= 4 else 'Minimo 4')
    train_pct = ask('% de datos para entrenar (el resto es test)', 70, int,
                    lambda v: None if 10 <= v <= 90 else 'Entre 10 y 90')

    def log_generation(x, best):
        print(f'  Generacion {x + 1}/{generations}: ganancia={best.results["profit"]:.2f} '
              f'operaciones={best.results["num_operations"]} {decode(best.genes)}')

    print('Optimizando... (Ctrl+C para cancelar)')
    result = optimize(load_csv(path), generations=generations, generation_size=size,
                      train_pct=train_pct, on_generation=log_generation)

    print(f'\nMEJORES PARAMETROS\n{LINE}')
    for name, value in result['params'].items():
        print(f'  {name:<22} {value}')
    print_results(result['train'], 'TRAIN (datos con los que se optimizo)')
    print_results(result['test'], 'TEST (datos que el algoritmo nunca vio)')
    print('\nSi TEST es mucho peor que TRAIN, los parametros estan sobreajustados.')


def run_tests():
    subprocess.run([sys.executable, '-m', 'unittest', '-v'])


MENU = [
    ('Descargar datos de Binance', download_data),
    ('Backtest de una estrategia', run_backtest),
    ('Optimizar parametros (algoritmo genetico)', run_optimizer),
    ('Correr tests', run_tests),
    ('Salir', None),
]


def main():
    os.makedirs(MARKETS_DIR, exist_ok=True)
    while True:
        print(f'\n{LINE}\n botQuantum\n{LINE}')
        try:
            action = ask_choice('Que quieres hacer?', [(fn, text) for text, fn in MENU])
        except (KeyboardInterrupt, EOFError):
            action = None
        if action is None:
            print('\nHasta luego!')
            return
        try:
            action()
        except KeyboardInterrupt:
            print('\nCancelado.')
        except Exception as error:
            # keep the menu alive if something fails (bad symbol, no internet...)
            print(f'\nError: {error}')
        try:
            input('\nEnter para volver al menu...')
        except (KeyboardInterrupt, EOFError):
            print('\nHasta luego!')
            return


if __name__ == '__main__':
    main()

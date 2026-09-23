from strategies.doji_rsi_bb import DojiRsiBbBands
from strategies.simple_strategy import SimplyStrategy

# strategies available in the CLI: class + parameters (name, label, default value)
# the type of each parameter is taken from its default value
STRATEGIES = {
    'doji_rsi_bb': {
        'name': 'RSI + Bandas de Bollinger (rebote en banda inferior)',
        'cls': DojiRsiBbBands,
        'params': [
            ('rsi_over_bought', 'RSI maximo para comprar', 60),
            ('rsi_over_sold', 'RSI minimo para comprar', 40),
            ('bb_len', 'Periodo Bandas de Bollinger', 20),
            ('n_std', 'Desviaciones estandar de las bandas', 2.0),
            ('rsi_len', 'Periodo RSI', 14),
            ('tp_profit_percent', 'Take profit %', 0.7),
            ('sp_loss_percent', 'Stop loss fijo %', 0.3),
            ('tsl_pct', 'Trailing stop %', 3.0),
        ],
    },
    'simple_rsi': {
        'name': 'RSI simple (compra en sobreventa)',
        'cls': SimplyStrategy,
        'params': [
            ('rsi_over_bought', 'RSI sobrecompra', 70),
            ('rsi_over_sold', 'RSI sobreventa (compra por debajo)', 30),
            ('tp_profit_percent', 'Take profit %', 0.7),
            ('sp_loss_percent', 'Stop loss fijo %', 10.0),
            ('tsl_pct', 'Trailing stop %', 5.0),
        ],
    },
}

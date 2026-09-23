# botQuantum

Bot para estudiar el mercado de Binance, buscar señales de compra (long) y probarlas con un
backtester sin *look-ahead bias*. Todavía **no ejecuta órdenes reales**: solo descarga velas,
calcula indicadores, simula operaciones y optimiza parámetros.

## 1. Instalación

Requiere **Python 3.12 o superior** (por los f-strings de `data_df.py`).

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

> `pandas_ta 0.3.14b0` no funciona con numpy 2, por eso `requirements.txt` fija `numpy==1.26.4`.

Las claves de Binance **no son necesarias** para descargar velas (son endpoints públicos). Si
algún día las usas, van en un archivo `.env` (ya está en `.gitignore`):

```
KEY=tu_api_key
SECRET=tu_api_secret
```

## 2. Estructura

| Archivo | Qué hace |
|---|---|
| `get_data.py` | Descarga velas de Binance (últimas N con ccxt o un rango de fechas con python-binance). Descarta la vela que todavía no cerró. |
| `data_df.py` | Convierte las velas a DataFrame, guarda/carga CSV, separa train/test y dibuja las operaciones. |
| `indicator.py` | Indicadores con `pandas_ta`: RSI, Bandas de Bollinger, patrones de velas (doji). |
| `strategies/` | Estrategias. Cada una calcula sus indicadores y responde `check_long_signal(index)`. |
| `strategy.py` | Envoltorio que le pasa la estrategia al backtester. |
| `backtester.py` | Simula las operaciones: TP, SL, trailing stop, comisiones, slippage, drawdown. |
| `genetic_algorithm.py` | Algoritmo genético para buscar los mejores parámetros de una estrategia. |
| `main.py` | Backtest de una estrategia con parámetros fijos. |
| `trybackGA.py` | Optimiza parámetros con el algoritmo genético (train) y valida en datos nuevos (test). |
| `tests/` | Tests que comprueban que no hay look-ahead bias. |
| `markets_data/` | CSV de velas y gráficos generados (ignorados por git). |

## 3. Flujo de trabajo recomendado

### Paso 1: descargar datos una vez y guardarlos

En `main.py`, al principio del archivo:

```python
SYMBOL = 'btc'
TIMEFRAME = '15m'
DATA_SOURCE = 'historical'
DATE_START = '01/01/2025'   # dd/mm/aaaa, UTC
DATE_END = '01/04/2025'
SAVE_CSV = True
```

```bash
python main.py
```

Se crea `markets_data/BTC-USDT-15m-01-04-2025.csv` (símbolo, timeframe y fecha de la última vela).
Usa **varios meses** de datos, que incluyan mercado alcista, bajista y lateral. Unas cuantas horas
de velas no dicen nada.

### Paso 2: probar una estrategia sin volver a descargar

```python
DATA_SOURCE = 'csv'
CSV_PATH = 'markets_data/BTC-USDT-15m-01-04-2025.csv'
PLOT = True   # guarda markets_data/operations-BTC-USDT.png
```

Los parámetros de la estrategia y del backtester se cambian en el mismo `main.py`:

```python
plan = DojiRsiBbBands(data_df=df, rsi_over_bought=60, rsi_over_sold=40,
                      tp_profit_percent=0.7, sp_loss_percent=0.3, tsl_pct=3)

backtester = Backtester(initial_balance=1000, leverage=1, inv_percent=100, df=plan.df,
                        tsl=True, fee_pct=0.1, slippage_pct=0.02)
```

- `tsl=True` usa el trailing stop (`tsl_pct`); `tsl=False` usa un stop fijo (`sp_loss_percent`).
- `fee_pct` es la comisión **por lado** en %: spot taker = 0.1, spot con BNB = 0.075, futuros maker = 0.02.
- `slippage_pct` empeora un poco cada precio de entrada y de salida.

### Paso 3: optimizar con el algoritmo genético

En `trybackGA.py` configura `DATA_SOURCE`, `CSV_PATH`, `TRAIN_PCT`, `GENERATIONS` y `GENE_RANGES`.

```bash
python trybackGA.py
```

- El genético **solo ve el 70% inicial** de los datos (train).
- Al final se prueba el mejor individuo **una sola vez** con el 30% final (test), que nunca vio.
- Si el resultado de test es mucho peor que el de train, los parámetros están sobreajustados
  (memorizaron el pasado).
- No repitas el ciclo "optimizo → miro test → cambio algo → vuelvo a mirar test" muchas veces:
  así el test también termina sobreajustado. Guarda un periodo final que no toques hasta el final.

Genes actuales: `rsi_over_bought`, `rsi_over_sold`, `bb_len`, `n_std` (x10, o sea 10 → 1.0),
`rsi_len`.

### Paso 4: correr los tests

```bash
python -m unittest -v
```

Corre siempre los tests después de tocar el backtester o una estrategia.

## 4. Cómo leer los resultados

| Campo | Significado |
|---|---|
| `profit` / `profit_pct` | Ganancia neta, **ya descontadas** comisiones y slippage. |
| `buy_and_hold_pct` | Lo que habrías ganado comprando al inicio y vendiendo al final. **La estrategia tiene que superarlo.** |
| `fees_paid` | Total pagado en comisiones. En timeframes cortos suele comerse la ganancia. |
| `max_drawdown` / `max_drawdown_pct` | Mayor caída del capital desde un máximo anterior. |
| `winrate` | % de operaciones ganadoras. Un winrate alto con TP pequeño y SL grande puede perder dinero igual. |
| `fitness_function` | `profit - max_drawdown`. Vale `-inf` si hubo menos de `min_trades` (5) operaciones. |

Con menos de ~30 operaciones el resultado es casi pura suerte.

## 5. Reglas contra el look-ahead bias (cómo funciona el backtester)

1. **La señal se calcula con la vela `i` ya cerrada** y la compra se hace al **open de la vela `i+1`**.
2. **TP y SL solo se revisan después de entrar.** El high/low de la vela de la señal ocurrió antes
   de la compra, así que no cuenta.
3. **Si una vela toca TP y SL a la vez, se asume que tocó primero el SL** (con velas no se puede
   saber el orden).
4. **Gaps:** si la vela abre por debajo del stop (o por encima del TP), se ejecuta al open.
5. **El trailing stop solo sube**, y el stop que se usa en la vela `i` sale de los cierres hasta `i-1`.
6. **Se descarta la vela en curso** que devuelve el exchange: no ha cerrado y sus valores van a cambiar.
7. **Train y test se separan por tiempo:** test siempre va después de train y nunca se mezclan.

### Al crear una estrategia nueva

- Para ver velas pasadas usa solo `shift(1)`, `shift(2)`, `rolling(...)`, etc. **Nunca `shift(-1)`**:
  eso lee el futuro.
- Calcula las señales vectorizadas en `__init__` (mira `strategies/doji_rsi_bb.py`) y devuelve
  `bool` en `check_long_signal(index)`.
- La estrategia necesita los atributos `tp_profit`, `sp_loss` y `tsl_pct`.
- Agrega la estrategia a `StrategyLookAheadTest` en `tests/test_lookahead.py`: comprueba que las
  señales no cambian cuando se borran las velas futuras.

## 6. Pendientes / ideas

- Comparar contra una estrategia aleatoria con el mismo TP/SL (si no la supera, no hay señal real).
- Walk-forward: optimizar en el mes 1, probar en el mes 2, avanzar un mes y repetir.
- Agregar TP / SL / trailing como genes del algoritmo genético.
- Ejecución real (primero en testnet de Binance).

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
| `strategies/` | Estrategias. Cada una calcula sus indicadores y responde `check_long_signal(index)`. `strategies/__init__.py` tiene el registro `STRATEGIES` que usa el menú. |
| `strategy.py` | Envoltorio que le pasa la estrategia al backtester. |
| `backtester.py` | Simula las operaciones: TP, SL, trailing stop, comisiones, slippage, drawdown. |
| `genetic_algorithm.py` | Algoritmo genético para buscar los mejores parámetros de una estrategia. |
| `trybackGA.py` | `optimize()`: optimiza con el algoritmo genético (train) y valida en datos nuevos (test). |
| `cli.py` | Menú interactivo. |
| `main.py` | Abre el menú. |
| `tests/` | Tests de look-ahead bias y del menú. |
| `markets_data/` | CSV de velas, operaciones y gráficos generados (ignorados por git). |

## 3. Uso: el menú

```bash
python main.py
```

```
 botQuantum
Que quieres hacer?
  1. Descargar datos de Binance
  2. Backtest de una estrategia
  3. Optimizar parametros (algoritmo genetico)
  4. Correr tests
  5. Salir
```

En cada pregunta, el valor entre `[corchetes]` es el valor por defecto: **Enter lo acepta**.
`Ctrl+C` cancela la acción en curso y te devuelve al menú.

### 1. Descargar datos de Binance

Pide moneda (se compara contra USDT), timeframe y rango de fechas (`dd/mm/aaaa`, en UTC). Guarda
las velas en `markets_data/`, por ejemplo `ETH-USDT-1h-01-01-2025_01-06-2025.csv`.
Descarga una vez y reutiliza el CSV todas las veces que quieras.

Usa **varios meses** de datos, que incluyan mercado alcista, bajista y lateral. Unas cuantas horas
de velas no dicen nada.

### 2. Backtest de una estrategia

1. Elige un CSV de `markets_data/` y una estrategia.
2. Ajusta los parámetros de la estrategia (Enter = valor por defecto).
3. Ajusta el backtester:
   - **Trailing stop** (`s`) o **stop loss fijo** (`n`).
   - **Comisión por lado** en %: spot taker = 0.1, spot con BNB = 0.075, futuros maker = 0.02.
   - **Slippage** %: empeora un poco cada precio de entrada y de salida.
4. Muestra los resultados y avisa si hubo pocas operaciones o si no le ganó a comprar y mantener.
5. Opcional: guarda las operaciones en `markets_data/operations-<datos>.csv` y el gráfico en
   `markets_data/operations-<datos>.png`.

### 3. Optimizar parámetros

Pide el CSV, el número de generaciones, los individuos por generación y el % de datos de train.
Por ahora optimiza la estrategia **RSI + Bandas de Bollinger**; los genes están en
`GENE_RANGES` de `trybackGA.py` (TP, SL y trailing son fijos, en `FIXED_PARAMS`).

- El genético **solo ve el primer X%** de los datos (train).
- Al final prueba el mejor individuo **una sola vez** con el resto (test), que nunca vio.
- Si test es mucho peor que train, los parámetros están sobreajustados (memorizaron el pasado).
- No repitas el ciclo "optimizo → miro test → cambio algo → vuelvo a mirar test" muchas veces:
  así el test también termina sobreajustado. Guarda un periodo final que no toques hasta el final.

Con 30 generaciones de 50 individuos y 3 meses de velas de 15m tarda unos 2 minutos.

### 4. Correr tests

Equivale a:

```bash
python -m unittest -v
```

Corre siempre los tests después de tocar el backtester o una estrategia.

### Sin menú

`python trybackGA.py` corre el optimizador con la configuración que está al principio del archivo.

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
- La estrategia necesita los atributos `tp_profit`, `sp_loss` y `tsl_pct`, y aceptar `log=False`.
- Regístrala en `STRATEGIES` (`strategies/__init__.py`) con sus parámetros y valores por defecto
  para que aparezca en el menú.
- Agrega la estrategia a `StrategyLookAheadTest` en `tests/test_lookahead.py`: comprueba que las
  señales no cambian cuando se borran las velas futuras.

## 6. Pendientes / ideas

- Comparar contra una estrategia aleatoria con el mismo TP/SL (si no la supera, no hay señal real).
- Walk-forward: optimizar en el mes 1, probar en el mes 2, avanzar un mes y repetir.
- Agregar TP / SL / trailing como genes del algoritmo genético.
- Ejecución real (primero en testnet de Binance).

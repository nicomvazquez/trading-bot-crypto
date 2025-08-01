# config.py

import os

# --- Configuración General del Bot ---
# Símbolo de trading (ej. "BTCUSDT", "ETHUSDT")
SYMBOL = "BTCUSDT"
# Intervalo de las velas (ej. "1" para 1 minuto, "5" para 5 minutos, "60" para 1 hora, "D" para 1 día)
INTERVAL = 1
CHECK_INTERVAL_SECONDS = 60 # O el valor que prefieras, por ejemplo, 30, 120, etc.
# Cantidad de la operación (ej. 0.001 BTC, 0.01 ETH). Ajusta según el par y el capital.
TRADE_QUANTITY = 0.1

# --- Configuración de Conexión a Bybit ---
# ¡IMPORTANTE! Asegúrate de que estas variables estén configuradas en tu archivo .env
# o como variables de entorno del sistema.
# TESTNET = True para operar en la red de pruebas de Bybit, False para la red real.
TESTNET = True 

# --- Configuración de Backtesting ---

# Ruta al archivo CSV con datos históricos para el backtest.
# Asegúrate de que esta ruta sea correcta y que el archivo exista.
HISTORICAL_DATA_FILE = "data/historical_data/ETHUSDT_1m_2023-06-01_to_2023-12-31.csv" # <--- ¡AJUSTA ESTA RUTA!
# Capital inicial para la simulación del backtest.
BACKTEST_INITIAL_CAPITAL = 10000.0 
# Tasa de comisión por operación (ej. 0.00075 para 0.075% de taker fee en Bybit).
BACKTEST_COMMISSION_RATE = 0.00075 

# --- Rutas de Logs ---
# Carpeta base para logs de trading en vivo y backtesting.
# Los logs se guardarán aquí (ej. data/live_trade_log_...csv, data/backtest_log_...csv)
LOG_FOLDER = "data" 

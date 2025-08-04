# backtesting/backtester.py

import pandas as pd
import os
import sys
from datetime import datetime
import re # Importar el módulo de expresiones regulares

# Importar las configuraciones
import config

# Importar los servicios y la estrategia
from services.bybit_client import SimulatedBybitClient
from services.trade_logger import log_trade
from strategies.rsi_strategy import generate_signal

def run_backtest():
    """
    Ejecuta el proceso de backtesting utilizando datos históricos
    y la estrategia definida en simple_ma_strategy.py.
    """
    print("--- INICIANDO BACKTEST DE LA ESTRATEGIA ---")
    print(f"Cargando datos históricos desde: {config.HISTORICAL_DATA_FILE}")

    # --- Extraer el símbolo del nombre del archivo histórico ---
    # Esto es más robusto si descargas datos para diferentes símbolos.
    # El nombre del archivo es típicamente "SYMBOL_INTERVAL_START_TO_END.csv"
    filename = os.path.basename(config.HISTORICAL_DATA_FILE)
    match = re.match(r"([A-Z]+[A-Z]+)_\d+m_.*\.csv", filename)
    extracted_symbol = config.SYMBOL # Valor por defecto si no se puede extraer
    if match:
        extracted_symbol = match.group(1)
    else:
        print(f"Advertencia: No se pudo extraer el símbolo del nombre del archivo '{filename}'. Usando el símbolo de config.py: {config.SYMBOL}")
    
    # Usaremos extracted_symbol para el logging y mensajes
    current_backtest_symbol = extracted_symbol
    print(f"Símbolo para el backtest (extraído de datos): {current_backtest_symbol}")


    try:
        df_historical = pd.read_csv(config.HISTORICAL_DATA_FILE)
        
        # --- Modificación para manejar FutureWarning de to_datetime ---
        # Asegurarse de que la columna 'Timestamp' sea numérica antes de convertir a datetime con unit
        df_historical['Timestamp'] = pd.to_datetime(df_historical['Timestamp'])
        # --- Fin de la modificación ---

        # Asegurarse de que el nombre de la columna del precio de cierre sea 'close' (minúsculas)
        if 'Close' in df_historical.columns and 'close' not in df_historical.columns:
            df_historical.rename(columns={'Close': 'close'}, inplace=True)
        
        df_historical = df_historical.sort_values('Timestamp').reset_index(drop=True)
        

        print(f"Datos históricos cargados: {len(df_historical)} velas desde {df_historical['Timestamp'].min()} hasta {df_historical['Timestamp'].max()}")

    except FileNotFoundError:
        print(f"ERROR: Archivo de datos históricos no encontrado en {config.HISTORICAL_DATA_FILE}. Por favor, verifica la ruta en config.py.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR al cargar o procesar datos históricos: {e}")
        sys.exit(1)

    # Inicializar cliente Bybit simulado
    simulated_bybit_client = SimulatedBybitClient(
        historical_data_df=df_historical, # Pasar el DataFrame completo al cliente simulado
        initial_capital=config.BACKTEST_INITIAL_CAPITAL,
        commission_rate=config.BACKTEST_COMMISSION_RATE
    )
    
    # Preparar el archivo de log para este backtest, usando el símbolo extraído
    backtest_log_filename = os.path.join(config.LOG_FOLDER, f"backtest_log_{current_backtest_symbol}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
    
    # Escribir encabezado inicial al log del backtest (esto se registra una sola vez al inicio del backtest)
    log_trade(current_backtest_symbol, "START_BACKTEST", "N/A", 0, 0, 0, simulated_bybit_client.current_balance, "N/A", "INITIALIZED", is_backtest=True)
    print(f"Log de backtest se guardará en: {backtest_log_filename}")

    # Bucle principal del Backtest
    for i in range(len(df_historical)):
        # La estrategia necesita un historial de velas hasta el momento actual
        current_data_slice = df_historical.iloc[0:i+1]
    

        current_candle_close = df_historical.iloc[i]['close']
        current_candle_timestamp = df_historical.iloc[i]['Timestamp']

        # Generar señal usando la estrategia
        signal = generate_signal(current_data_slice.copy()) # Pasa una copia para evitar SettingWithCopyWarning

        # Lógica de Simulación de Trading
        current_position_size, current_position_side, current_entry_price = simulated_bybit_client.get_current_position(current_backtest_symbol)


        if signal == "BUY":
            # Si no hay posición LONG, ejecutar orden de COMPRA
            if current_position_side != "Long":
                # Si hay una posición SHORT, primero cerramos esa posición
                if current_position_side == "Short":
                    print(f"[{current_candle_timestamp}] Señal BUY: Cerrando SHORT existente...")
                    # current_position_size es la cantidad de la posición que ya tenemos
                    close_res = simulated_bybit_client.execute_order(current_backtest_symbol, "Buy", current_position_size, current_candle_close, current_candle_timestamp)
                    if close_res and close_res['success']:
                        log_trade(current_backtest_symbol, "CLOSE_POSITION", "Buy", current_position_size, current_candle_close, close_res['pnl'], close_res['balance_after_trade'], close_res['order_id'], "CLOSED_SHORT", is_backtest=True)
                    else:
                        print(f"[{current_candle_timestamp}] Error al cerrar posición SHORT. {close_res}")
                
                # Luego, abrimos la nueva posición LONG (o se abre directamente si no había posición previa)
                print(f"[{current_candle_timestamp}] Señal BUY: Abriendo LONG...")
                open_res = simulated_bybit_client.execute_order(current_backtest_symbol, "Buy", config.TRADE_QUANTITY, current_candle_close, current_candle_timestamp)
                if open_res and open_res['success']:
                    log_trade(current_backtest_symbol, "OPEN_POSITION", "Buy", config.TRADE_QUANTITY, current_candle_close, 0.0, open_res['balance_after_trade'], open_res['order_id'], "EXECUTED_LONG", is_backtest=True)
                else:
                    print(f"[{current_candle_timestamp}] Error al abrir posición LONG. {open_res}")

        elif signal == "SELL":
            # Si no hay posición SHORT, ejecutar orden de VENTA
            if current_position_side != "Short":
                # Si hay una posición LONG, primero cerramos esa posición
                if current_position_side == "Long":
                    print(f"[{current_candle_timestamp}] Señal SELL: Cerrando LONG existente...")
                    close_res = simulated_bybit_client.execute_order(current_backtest_symbol, "Sell", current_position_size, current_candle_close, current_candle_timestamp)
                    if close_res and close_res['success']:
                        log_trade(current_backtest_symbol, "CLOSE_POSITION", "Sell", current_position_size, current_candle_close, close_res['pnl'], close_res['balance_after_trade'], close_res['order_id'], "CLOSED_LONG", is_backtest=True)
                    else:
                        print(f"[{current_candle_timestamp}] Error al cerrar posición LONG. {close_res}")

                # Luego, abrimos la nueva posición SHORT (o se abre directamente si no había posición previa)
                print(f"[{current_candle_timestamp}] Señal SELL: Abriendo SHORT...")
                open_res = simulated_bybit_client.execute_order(current_backtest_symbol, "Sell", config.TRADE_QUANTITY, current_candle_close, current_candle_timestamp)
                if open_res and open_res['success']:
                    log_trade(current_backtest_symbol, "OPEN_POSITION", "Sell", config.TRADE_QUANTITY, current_candle_close, 0.0, open_res['balance_after_trade'], open_res['order_id'], "EXECUTED_SHORT", is_backtest=True)
                else:
                    print(f"[{current_candle_timestamp}] Error al abrir posición SHORT. {open_res}")

        elif signal == "HOLD":
            print(f"DEBUG: {current_candle_timestamp} - Señal: HOLD (No hay acción)")
            pass # No se hace nada, se mantiene la posición actual si la hay.
        
        # Las señales "HOLD" y "WAIT" no requieren acción si la posición ya es la deseada o no hay suficientes datos.

    # --- Finalización del Backtest ---
    # Asegurarse de cerrar cualquier posición abierta al final del backtest
    final_position_size, final_position_side, final_entry_price = simulated_bybit_client.get_current_position(current_backtest_symbol)

    if final_position_side != "None":
        final_candle_close = df_historical.iloc[-1]['close']
        final_candle_timestamp = df_historical.iloc[-1]['Timestamp']
        
        sim_res = None
        if final_position_side == "Long":
            print(f"[{final_candle_timestamp}] Final del backtest: Cerrando posición LONG abierta.")
            sim_res = simulated_bybit_client.execute_order(current_backtest_symbol, "Sell", final_position_size, final_candle_close, final_candle_timestamp)
            log_trade(current_backtest_symbol, "CLOSE_POSITION", "Sell", final_position_size, final_candle_close, sim_res['pnl'], sim_res['balance_after_trade'], "SIM_FINAL_CLOSE_LONG", "CLOSED_AT_END", is_backtest=True)
        elif final_position_side == "Short":
            print(f"[{final_candle_timestamp}] Final del backtest: Cerrando posición SHORT abierta.")
            sim_res = simulated_bybit_client.execute_order(current_backtest_symbol, "Buy", final_position_size, final_candle_close, final_candle_timestamp)
            log_trade(current_backtest_symbol, "CLOSE_POSITION", "Buy", final_position_size, final_candle_close, sim_res['pnl'], sim_res['balance_after_trade'], "SIM_FINAL_CLOSE_SHORT", "CLOSED_AT_END", is_backtest=True)

    print("\n--- Resumen del Backtest ---")
    print(f"Símbolo: {current_backtest_symbol}")
    print(f"Capital Inicial: {config.BACKTEST_INITIAL_CAPITAL:.2f}")
    print(f"Capital Final: {simulated_bybit_client.current_balance:.2f}")
    print(f"PNL Neto Total: {(simulated_bybit_client.current_balance - config.BACKTEST_INITIAL_CAPITAL):.2f}")
    print(f"Resultados guardados en: {backtest_log_filename}")

# Este bloque asegura que run_backtest() se ejecute cuando el script es llamado directamente
if __name__ == "__main__":
    run_backtest()
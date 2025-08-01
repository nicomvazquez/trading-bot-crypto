# services/trade_logger.py
import csv
import os
from datetime import datetime
import config # Assuming config.py defines LOG_FOLDER

# Define la carpeta donde se guardarán los logs usando config.LOG_FOLDER
# Asegúrate de que config.py tenga: LOG_FOLDER = "data/logs" o similar
# Si config.py no tiene LOG_FOLDER, puedes definirlo aquí directamente:
# LOG_FOLDER = "data/logs" 

# Variable global para el nombre del archivo de log de la sesión actual.
# Se inicializará a None y se establecerá la primera vez que se llame a log_trade en una sesión.
session_log_filename = None

def log_trade(symbol, action, side, quantity, price, pnl=0.0, balance_after_trade=0.0, order_id='', status='', is_backtest=False):
    """
    Registra la información de la operación en un archivo CSV.
    Cada vez que el bot arranca (o se llama esta función por primera vez en una sesión),
    se genera un nuevo archivo de log con un timestamp único.
    Los valores numéricos son formateados para una mejor legibilidad.

    Args:
        symbol (str): Símbolo de trading (ej. "BTCUSDT").
        action (str): Acción realizada (ej. "OPEN_POSITION", "CLOSE_POSITION", "START_BACKTEST", "LIVE_TRADE_INIT").
        side (str): Lado de la operación ("Buy", "Sell", "N/A").
        quantity (float): Cantidad de la operación.
        price (float): Precio al que se ejecutó la operación.
        pnl (float): Ganancia o pérdida de la operación (0.0 para aperturas).
        balance_after_trade (float): Balance del capital después de la operación.
        order_id (str): ID de la orden (real o simulado).
        status (str): Estado o descripción adicional (ej. "EXECUTED_LONG", "CLOSED_SHORT").
        is_backtest (bool): Indica si la operación es parte de un backtest.
    """
    global session_log_filename # Permite modificar la variable global

    # Determinar el folder de logs, usando config.LOG_FOLDER si está definido, sino un valor por defecto
    log_folder_path = getattr(config, 'LOG_FOLDER', 'data/logs') # Lee de config o usa 'data/logs'

    # Asegurarse de que la carpeta de logs exista
    if not os.path.exists(log_folder_path):
        os.makedirs(log_folder_path)
        print(f"DEBUG: Carpeta '{log_folder_path}/' creada para logs.")

    # Genera el nombre completo del archivo de log para esta sesión si aún no se ha hecho
    if session_log_filename is None:
        timestamp_file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Ajusta el nombre del archivo según si es backtest o live
        if is_backtest:
            # Para backtest, el nombre del archivo incluirá un prefijo específico
            session_log_filename = os.path.join(log_folder_path, f'backtest_log_{symbol}_{timestamp_file_name}.csv')
        else:
            # Para trading en vivo
            session_log_filename = os.path.join(log_folder_path, f'live_trade_log_{symbol}_{timestamp_file_name}.csv')
        
        # Crea el nuevo archivo y escribe el encabezado
        with open(session_log_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header = ['Timestamp', 'Symbol', 'Action', 'Side', 'Quantity', 'Price', 'PNL', 'BalanceAfterTrade', 'OrderID', 'Status']
            writer.writerow(header)
        print(f"Nuevo archivo de log creado para esta sesión: {session_log_filename}")

    # Timestamp para la entrada individual del log (puede incluir milisegundos para mayor precisión del evento)
    timestamp_log_entry = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # Trunca a milisegundos

    # --- Formateo de los valores numéricos para mejor legibilidad ---
    # Usamos .rstrip('0').rstrip('.') para eliminar ceros y el punto decimal si el número es entero
    formatted_quantity = f"{quantity:.8f}".rstrip('0').rstrip('.') if isinstance(quantity, (int, float)) else str(quantity)
    formatted_price = f"{price:.2f}".rstrip('0').rstrip('.') if isinstance(price, (int, float)) else str(price)
    formatted_pnl = f"{pnl:.2f}".rstrip('0').rstrip('.') if isinstance(pnl, (int, float)) else str(pnl)
    formatted_balance_after_trade = f"{balance_after_trade:.2f}".rstrip('0').rstrip('.') if isinstance(balance_after_trade, (int, float)) else str(balance_after_trade)
    # -------------------------------------------------------------------

    # Abre el archivo en modo 'a' (append) para añadir la nueva fila de datos
    with open(session_log_filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            timestamp_log_entry,
            symbol,
            action,
            side,
            formatted_quantity,
            formatted_price,
            formatted_pnl,
            formatted_balance_after_trade,
            order_id,
            status
        ])

    # Se elimina este print para evitar exceso de mensajes en el backtest
    # print(f"Operación registrada en {session_log_filename}")
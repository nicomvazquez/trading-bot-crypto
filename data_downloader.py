# services/data_downloader.py
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from pybit.unified_trading import HTTP # Importa el cliente HTTP para interactuar con la API de Bybit
from dotenv import load_dotenv # Cargar las variables de entorno para el cliente REAL

# Carga las variables de entorno del archivo .env al inicio de la ejecución
load_dotenv() # Esto es crucial para que BybitClient (real) pueda leer las claves

def download_historical_klines(symbol, interval, start_date_str, end_date_str, category="linear", output_folder="data/historical_data"):
    """
    Descarga datos históricos de velas (kline) de Bybit para un símbolo y periodo dados.

    Args:
        symbol (str): Símbolo de trading (ej. "BTCUSDT").
        interval (str): Intervalo de las velas (ej. "1" para 1 minuto, "60" para 1 hora, "D" para 1 día).
        start_date_str (str): Fecha de inicio en formato "YYYY-MM-DD".
        end_date_str (str): Fecha de fin en formato "YYYY-MM-DD".
        category (str): Categoría del producto (ej. "linear" para futuros perpetuos).
        output_folder (str): Carpeta donde se guardarán los datos.
    """
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        print("ERROR: Las variables de entorno BYBIT_API_KEY y BYBIT_API_SECRET no están configuradas.")
        print("Por favor, configúralas antes de ejecutar el descargador de datos.")
        return

    session = HTTP(
        testnet=True, # Usa la configuración de testnet de config.py
        api_key=api_key,
        api_secret=api_secret
    )

    # Convertir fechas string a objetos datetime
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # Crear la carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Nombre del archivo de salida
    output_filename = os.path.join(output_folder, f"{symbol}_{interval}m_{start_date_str}_to_{end_date_str}.csv")
    
    all_klines = []
    current_end_timestamp_ms = int(end_date.timestamp() * 1000) # Convertir a milisegundos

    print(f"Iniciando descarga para {symbol} - {interval} desde {start_date_str} hasta {end_date_str}...")

    # Bybit API devuelve hasta 1000 klines por solicitud y va desde el más reciente al más antiguo.
    # Necesitamos iterar hacia atrás en el tiempo.
    limit = 1000 # Número máximo de velas por solicitud

    while True:
        # Asegúrate de que el timestamp no sea menor que el de la fecha de inicio
        if current_end_timestamp_ms < int(start_date.timestamp() * 1000):
            print("Fecha de inicio alcanzada o superada. Deteniendo descarga.")
            break

        print(f"Descargando hasta {datetime.fromtimestamp(current_end_timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')}...")
        try:
            response = session.get_kline(
                category=category,
                symbol=symbol,
                interval=interval,
                limit=limit,
                end=current_end_timestamp_ms # 'end' es el timestamp de la vela más reciente a obtener
            )

            if response['retCode'] == 0:
                klines = response['result']['list']
                if not klines:
                    print("No más datos disponibles en este rango.")
                    break

                # Los klines vienen en orden descendente de tiempo (más reciente primero)
                # Los agregamos al principio de nuestra lista para mantener el orden ascendente
                all_klines = klines + all_klines

                # El timestamp de la vela más antigua descargada será el nuevo 'end' para la siguiente solicitud
                # Es el primer elemento de la última vela en la lista
                current_end_timestamp_ms = int(klines[-1][0])
                
                # Resta 1 milisegundo para asegurar que la próxima solicitud no incluya la vela ya descargada
                current_end_timestamp_ms -= 1 
                
                time.sleep(0.5) # Pausa para evitar exceder límites de tasa de la API

            else:
                print(f"Error al obtener klines: {response['retMsg']}")
                break

        except Exception as e:
            print(f"Ocurrió un error inesperado durante la descarga: {e}")
            break

    # Filtrar los klines para asegurar que estén dentro del rango de fecha deseado
    final_klines = []
    start_ts_ms = int(start_date.timestamp() * 1000)
    end_ts_ms = int(end_date.timestamp() * 1000)
    
    # Se añade un pequeño margen al final del rango para asegurar que la última vela del día final se incluya
    # Esto es porque 'end_date' es el inicio del día final. Queremos incluir todo ese día.
    # Un día tiene 86,400,000 milisegundos (24 * 60 * 60 * 1000)
    # Sin embargo, dado que current_end_timestamp_ms se ajusta para ser el timestamp del inicio de la vela,
    # el filtrado debería ser inclusivo hasta el final del día de end_date.
    # Para simplicidad y precisión, filtramos con el timestamp original de la vela.

    for kline in all_klines:
        kline_ts_ms = int(kline[0])
        # Incluir velas cuyo inicio sea mayor o igual al inicio de start_date
        # e incluir velas cuyo inicio sea menor o igual al inicio de end_date
        if start_ts_ms <= kline_ts_ms <= end_ts_ms: 
            final_klines.append(kline)
    
    if not final_klines:
        print("No se encontraron datos dentro del rango de fechas especificado después de la descarga y filtrado.")
        return

    # Crear DataFrame
    df = pd.DataFrame(final_klines, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover'])
    
    # --- LA CORRECCIÓN CLAVE ESTÁ AQUÍ ---
    # Primero, asegúrate de que la columna 'Timestamp' sea numérica (entero)
    df['Timestamp'] = pd.to_numeric(df['Timestamp'])
    # Luego, convierte a datetime especificando la unidad (ahora no dará FutureWarning)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    # --- FIN DE LA CORRECCIÓN ---
    
    # Asegurarse de que la columna 'close' sea numérica y renombrar 'Close' a 'close' si es necesario
    df.rename(columns={'Close': 'close'}, inplace=True)
    df['close'] = pd.to_numeric(df['close']) # Aseguramos tipo numérico

    # Guardar en CSV
    df.to_csv(output_filename, index=False)
    print(f"\nDescarga completa. Datos guardados en: {output_filename}")
    print(f"Total de velas descargadas: {len(df)}")
    print(f"Rango de datos en archivo: {df['Timestamp'].min()} a {df['Timestamp'].max()}")

# --- Cómo ejecutar el descargador ---
if __name__ == "__main__":
    # Asegúrate de que tus variables de entorno BYBIT_API_KEY y BYBIT_API_SECRET estén configuradas.
    # También, asegúrate de que config.py tenga la variable TESTNET correctamente configurada.

    # Parámetros para la descarga: CONFIGURAR
    SYMBOL_TO_DOWNLOAD = "ETHUSDT" # Se cambió a BTCUSDT para que coincida con tu config.py
    INTERVAL_TO_DOWNLOAD = "60" # "1" para 1 minuto. Puedes probar "5", "15", "60", etc.
    START_DATE = "2023-06-01" # Formato YYYY-MM-DD (Se ajustó al ejemplo de tu config.py)
    END_DATE = "2023-12-31"   # Formato YYYY-MM-DD (Se ajustó al ejemplo de tu config.py)
    
    # Llama a la función para iniciar la descarga
    download_historical_klines(
        symbol=SYMBOL_TO_DOWNLOAD,
        interval=INTERVAL_TO_DOWNLOAD,
        start_date_str=START_DATE,
        end_date_str=END_DATE
    )
    # Puedes llamar a la función varias veces para diferentes periodos o símbolos
    # download_historical_klines(symbol="ETHUSDT", interval="5", start_date_str="2024-01-01", end_date_str="2024-03-31")
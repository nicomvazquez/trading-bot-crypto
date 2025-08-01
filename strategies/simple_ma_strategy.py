# strategies/simple_ma_strategy.py
import pandas as pd

# Configuracion inicial: definir los parametros de las medias moviles
SMA_LONG_PERIOD = 7
SMA_SHORT_PERIOD = 3

def generate_signal(df_klines: pd.DataFrame) -> str:
    """
    Genera una señal de trading (BUY, SELL, HOLD, WAIT) basada en el cruce de Medias Móviles Simples (SMA).
    
    Args:
        df_klines (pd.DataFrame): DataFrame de Pandas con los datos de velas,
                                  debe contener una columna 'close' con los precios de cierre.
                                  Se espera que las velas estén ordenadas cronológicamente (la más antigua primero).

    Returns:
        str: "BUY" para señal de compra, "SELL" para señal de venta, 
             "HOLD" si no hay cruce o "WAIT" si no hay suficientes datos.
    """
    # 1. Validación inicial de datos
    # Necesitamos al menos suficientes velas para calcular la SMA más larga.
    if df_klines.empty or len(df_klines) < SMA_LONG_PERIOD:
        print(f"DEBUG: No hay suficientes datos para la estrategia. Necesita {SMA_LONG_PERIOD} velas, tiene {len(df_klines)}.")
        return "WAIT" # No hay suficientes datos para tomar una decisión

    # 2. Asegurarse de que la columna 'close' sea numérica
    # Esto es importante por si los datos vienen como strings desde la API.
    df_klines['close'] = pd.to_numeric(df_klines['close'], errors='coerce')
    
    # Eliminar cualquier fila que haya quedado con NaN en 'close' después de la conversión
    df_klines.dropna(subset=['close'], inplace=True)

    # Volver a verificar la cantidad de datos después de limpiar
    if len(df_klines) < SMA_LONG_PERIOD:
        print(f"DEBUG: No hay suficientes datos válidos después de la limpieza. Necesita {SMA_LONG_PERIOD} velas, tiene {len(df_klines)}.")
        return "WAIT"

    # 3. Calcular las Medias Móviles Simples (SMA)
    df_klines['SMA_Short'] = df_klines['close'].rolling(window=SMA_SHORT_PERIOD).mean()
    df_klines['SMA_Long'] = df_klines['close'].rolling(window=SMA_LONG_PERIOD).mean()

    # 4. Eliminar las filas iniciales que contienen valores NaN después del cálculo de las SMA
    # Esto ocurre porque las medias móviles necesitan un número de períodos para calcularse.
    df_klines.dropna(inplace=True)

    # 5. Volver a verificar que tengamos al menos dos filas después de dropna para detectar un cruce
    if df_klines.empty or len(df_klines) < 2:
        print("DEBUG: No hay suficientes datos después de calcular SMAs y limpiar NaNs para detectar un cruce.")
        return "WAIT"

    # 6. Obtener las dos últimas filas para detectar el cruce
    # 'iloc[-1]' es la vela más reciente
    # 'iloc[-2]' es la vela anterior a la más reciente
    last_row = df_klines.iloc[-1]
    prev_row = df_klines.iloc[-2]

    # 7. Lógica del Cruce de Medias Móviles
    # Cruce alcista (Golden Cross): SMA Corta cruza por encima de SMA Larga
    if last_row['SMA_Short'] > last_row['SMA_Long'] and \
       prev_row['SMA_Short'] <= prev_row['SMA_Long']: # El cruce ocurrió en la última vela
        return "BUY" 
    
    # Cruce bajista (Death Cross): SMA Corta cruza por debajo de SMA Larga
    elif last_row['SMA_Short'] < last_row['SMA_Long'] and \
         prev_row['SMA_Short'] >= prev_row['SMA_Long']: # El cruce ocurrió en la última vela
        return "SELL"
    
    # Si no hay cruce, no se toma ninguna acción
    else:
        return "HOLD"
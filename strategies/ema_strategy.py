import pandas as pd
import pandas_ta as ta # Asegúrate de tener pandas_ta instalado (pip install pandas_ta)

# Configuracion inicial: definir los parametros de las medias moviles exponenciales
EMA_FAST_PERIOD = 9  # Periodo para la EMA rápida
EMA_SLOW_PERIOD = 26 # Periodo para la EMA lenta

def generate_signal(df_klines: pd.DataFrame, 
                    fast_period: int = EMA_FAST_PERIOD, 
                    slow_period: int = EMA_SLOW_PERIOD) -> str:
    """
    Genera una señal de trading (BUY, SELL, HOLD, WAIT) basada en el cruce de Medias Móviles Exponenciales (EMA).
    
    Args:
        df_klines (pd.DataFrame): DataFrame de Pandas con los datos de velas,
                                  debe contener una columna 'close' con los precios de cierre.
                                  Se espera que las velas estén ordenadas cronológicamente (la más antigua primero).
        fast_period (int): El número de períodos para la Media Móvil Exponencial rápida.
        slow_period (int): El número de períodos para la Media Móvil Exponencial lenta.

    Returns:
        str: "BUY" para señal de compra, "SELL" para señal de venta, 
             "HOLD" si no hay cruce, o "WAIT" si no hay suficientes datos.
    """
    # Validaciones iniciales de los periodos
    if not isinstance(fast_period, int) or not isinstance(slow_period, int):
        # print("ERROR: Los periodos de las EMA deben ser números enteros.") # Descomentar para debug
        return "WAIT"
    if fast_period <= 0 or slow_period <= 0:
        # print("ERROR: Los periodos de las EMA deben ser mayores que cero.") # Descomentar para debug
        return "WAIT"
    if fast_period >= slow_period:
        # print("ERROR: El periodo de la EMA rápida debe ser estrictamente menor que el de la EMA lenta.") # Descomentar para debug
        return "WAIT"

    # 1. Validación inicial de datos
    # Necesitamos al menos suficientes velas para calcular la EMA más larga.
    required_candles = slow_period 
    if df_klines.empty or len(df_klines) < required_candles:
        # print(f"DEBUG: No hay suficientes datos para la estrategia. Necesita {required_candles} velas, tiene {len(df_klines)}.") # Descomentar para debug
        return "WAIT"

    # 2. Asegurarse de que la columna 'close' sea numérica
    df_klines['close'] = pd.to_numeric(df_klines['close'], errors='coerce')
    
    # Eliminar cualquier fila que haya quedado con NaN en 'close' después de la conversión
    df_klines.dropna(subset=['close'], inplace=True)

    # Volver a verificar la cantidad de datos después de limpiar
    if len(df_klines) < required_candles:
        # print(f"DEBUG: No hay suficientes datos válidos después de la limpieza. Necesita {required_candles} velas, tiene {len(df_klines)}.") # Descomentar para debug
        return "WAIT"

    # 3. Calcular las Medias Móviles Exponenciales (EMA)
    df_klines['EMA_Fast'] = ta.ema(df_klines['close'], length=fast_period)
    df_klines['EMA_Slow'] = ta.ema(df_klines['close'], length=slow_period)

    # 4. Eliminar las filas iniciales que contienen valores NaN después del cálculo de las EMAs
    df_klines.dropna(inplace=True)

    # 5. Volver a verificar que tengamos al menos dos filas después de dropna para detectar un cruce
    if df_klines.empty or len(df_klines) < 2:
        # print("DEBUG: No hay suficientes datos después de calcular EMAs y limpiar NaNs para detectar un cruce.") # Descomentar para debug
        return "WAIT"

    # 6. Obtener las dos últimas filas para detectar el cruce
    last_row = df_klines.iloc[-1]
    prev_row = df_klines.iloc[-2]

    # 7. Lógica del Cruce de Medias Móviles Exponenciales
    if prev_row['EMA_Fast'] <= prev_row['EMA_Slow'] and \
       last_row['EMA_Fast'] > last_row['EMA_Slow']:
        # print(f"DEBUG: Señal detectada: BUY en {df_klines.index[-1]} (EMA Rápida {last_row['EMA_Fast']:.2f} > EMA Larga {last_row['EMA_Slow']:.2f}, antes era <=)") # Descomentar para debug
        return "BUY" 
    
    elif prev_row['EMA_Fast'] >= prev_row['EMA_Slow'] and \
         last_row['EMA_Fast'] < last_row['EMA_Slow']:
        # print(f"DEBUG: Señal detectada: SELL en {df_klines.index[-1]} (EMA Rápida {last_row['EMA_Fast']:.2f} < EMA Larga {last_row['EMA_Slow']:.2f}, antes era >=)") # Descomentar para debug
        return "SELL"
    
    else:
        # print(f"DEBUG: Señal detectada: HOLD en {df_klines.index[-1]} (No hay cruce claro. EMA Rápida: {last_row['EMA_Fast']:.2f}, EMA Larga: {last_row['EMA_Slow']:.2f})") # Descomentar para debug
        return "HOLD"
# strategies/single_ema_strategy.py
import pandas as pd

# Configuracion inicial: definir el parametro de la Media Movil Exponencial
EMA_PERIOD = 20 # Puedes ajustar este período según tus preferencias

def generate_signal(df_klines: pd.DataFrame) -> str:
    """
    Genera una señal de trading (BUY, SELL, HOLD, WAIT) basada en el cruce del precio de cierre
    con una Media Móvil Exponencial (EMA).
    
    Args:
        df_klines (pd.DataFrame): DataFrame de Pandas con los datos de velas,
                                  debe contener una columna 'close' con los precios de cierre.
                                  Se espera que las velas estén ordenadas cronológicamente (la más antigua primero).

    Returns:
        str: "BUY" para señal de compra, "SELL" para señal de venta, 
             "HOLD" si no hay cruce o "WAIT" si no hay suficientes datos.
    """
    # 1. Validación inicial de datos
    # Necesitamos al menos suficientes velas para calcular la EMA.
    if df_klines.empty or len(df_klines) < EMA_PERIOD:
        print(f"DEBUG: No hay suficientes datos para la estrategia EMA. Necesita {EMA_PERIOD} velas, tiene {len(df_klines)}.")
        return "WAIT" # No hay suficientes datos para tomar una decisión

    # 2. Asegurarse de que la columna 'close' sea numérica
    df_klines['close'] = pd.to_numeric(df_klines['close'], errors='coerce')
    
    # Eliminar cualquier fila que haya quedado con NaN en 'close' después de la conversión
    df_klines.dropna(subset=['close'], inplace=True)

    # Volver a verificar la cantidad de datos después de limpiar
    if len(df_klines) < EMA_PERIOD:
        print(f"DEBUG: No hay suficientes datos válidos después de la limpieza. Necesita {EMA_PERIOD} velas, tiene {len(df_klines)}.")
        return "WAIT"

    # 3. Calcular la Media Móvil Exponencial (EMA)
    # Usamos .ewm() para EMA (Exponential Weighted Moving Average)
    df_klines['EMA'] = df_klines['close'].ewm(span=EMA_PERIOD, adjust=False).mean()

    # 4. Eliminar las filas iniciales que contienen valores NaN después del cálculo de la EMA
    df_klines.dropna(inplace=True)

    # 5. Volver a verificar que tengamos al menos dos filas después de dropna para detectar un cruce
    if df_klines.empty or len(df_klines) < 2:
        print("DEBUG: No hay suficientes datos después de calcular EMA y limpiar NaNs para detectar un cruce.")
        return "WAIT"

    # 6. Obtener las dos últimas filas para detectar el cruce
    last_row = df_klines.iloc[-1]
    prev_row = df_klines.iloc[-2]

    # 7. Lógica del Cruce del Precio con la EMA
    # Señal de COMPRA: El precio de cierre actual cruza por encima de la EMA
    if last_row['close'] > last_row['EMA'] and \
       prev_row['close'] <= prev_row['EMA']: # El cruce ocurrió en la última vela
        return "BUY" 
    
    # Señal de VENTA: El precio de cierre actual cruza por debajo de la EMA
    elif last_row['close'] < last_row['EMA'] and \
         prev_row['close'] >= prev_row['EMA']: # El cruce ocurrió en la última vela
        return "SELL"
    
    # Si no hay cruce claro, se mantiene la posición
    else:
        return "HOLD"
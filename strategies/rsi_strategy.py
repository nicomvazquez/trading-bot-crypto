# strategies/rsi_strategy.py

import pandas as pd
import pandas_ta as ta # Asegúrate de tener pandas_ta instalado (pip install pandas_ta)

# Configuración inicial: definir los parámetros del RSI
RSI_PERIOD = 14  # Período para el cálculo del RSI (comúnmente 14)
RSI_OVERBOUGHT = 70 # Nivel de sobrecompra (cuando el RSI está por encima de este valor)
RSI_OVERSOLD = 30   # Nivel de sobreventa (cuando el RSI está por debajo de este valor)

def generate_signal(df_klines: pd.DataFrame) -> str:
    """
    Genera una señal de trading (BUY, SELL, HOLD, WAIT) basada en el indicador RSI.
    
    Args:
        df_klines (pd.DataFrame): DataFrame de Pandas con los datos de velas,
                                  debe contener una columna 'close' con los precios de cierre.
                                  Se espera que las velas estén ordenadas cronológicamente (la más antigua primero).

    Returns:
        str: "BUY" para señal de compra, "SELL" para señal de venta, 
             "HOLD" si no hay cruce o "WAIT" si no hay suficientes datos.
    """
    # 1. Validación inicial de datos
    # Necesitamos al menos suficientes velas para calcular el RSI.
    if df_klines.empty or len(df_klines) < RSI_PERIOD + 1: # RSI necesita al menos un período + 1 vela para el cambio
        print(f"DEBUG: No hay suficientes datos para la estrategia RSI. Necesita {RSI_PERIOD + 1} velas, tiene {len(df_klines)}.")
        return "WAIT"

    # 2. Asegurarse de que la columna 'close' sea numérica
    df_klines['close'] = pd.to_numeric(df_klines['close'], errors='coerce')
    df_klines.dropna(subset=['close'], inplace=True) # Eliminar filas con NaN en 'close'

    # Volver a verificar la cantidad de datos después de limpiar
    if len(df_klines) < RSI_PERIOD + 1:
        print(f"DEBUG: No hay suficientes datos válidos después de la limpieza para RSI. Necesita {RSI_PERIOD + 1} velas, tiene {len(df_klines)}.")
        return "WAIT"

    # 3. Calcular el RSI utilizando pandas_ta
    # pandas_ta añade la columna RSI directamente al DataFrame
    df_klines.ta.rsi(close='close', length=RSI_PERIOD, append=True)

    # 4. Eliminar las filas iniciales que contienen valores NaN después del cálculo del RSI
    df_klines.dropna(subset=[f'RSI_{RSI_PERIOD}'], inplace=True)

    # 5. Volver a verificar que tengamos al menos dos filas después de dropna para detectar un cruce
    if df_klines.empty or len(df_klines) < 2:
        print("DEBUG: No hay suficientes datos después de calcular RSI y limpiar NaNs para detectar un cruce.")
        return "WAIT"

    # 6. Obtener el valor de RSI de la vela actual y la anterior
    last_rsi = df_klines[f'RSI_{RSI_PERIOD}'].iloc[-1]
    prev_rsi = df_klines[f'RSI_{RSI_PERIOD}'].iloc[-2]

    # 7. Lógica de la estrategia RSI
    # Señal de COMPRA: RSI cruza por encima del nivel de sobreventa (ej. 30)
    if last_rsi > RSI_OVERSOLD and prev_rsi <= RSI_OVERSOLD:
        print(f"DEBUG: Señal detectada: BUY (RSI {last_rsi:.2f} cruza por encima de sobreventa {RSI_OVERSOLD}).")
        return "BUY" 
    
    # Señal de VENTA: RSI cruza por debajo del nivel de sobrecompra (ej. 70)
    elif last_rsi < RSI_OVERBOUGHT and prev_rsi >= RSI_OVERBOUGHT:
        print(f"DEBUG: Señal detectada: SELL (RSI {last_rsi:.2f} cruza por debajo de sobrecompra {RSI_OVERBOUGHT}).")
        return "SELL"
    
    # Si no hay cruce claro de los niveles, no se toma ninguna acción
    else:
        print(f"DEBUG: Señal detectada: HOLD (RSI: {last_rsi:.2f}). No hay cruce de niveles clave.")
        return "HOLD"
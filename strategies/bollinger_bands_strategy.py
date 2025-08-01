# strategies/bollinger_bands_strategy.py
import pandas as pd

# Configuracion inicial: definir los parametros de las Bandas de Bollinger
# Periodo para la Media Móvil (SMA) de Bollinger Bands
BB_PERIOD = 20 
# Número de desviaciones estándar para las bandas superior e inferior
BB_STD_DEV = 2 

def generate_signal(df_klines: pd.DataFrame) -> str:
    """
    Genera una señal de trading (BUY, SELL, HOLD, WAIT) basada en las Bandas de Bollinger.
    
    Args:
        df_klines (pd.DataFrame): DataFrame de Pandas con los datos de velas,
                                  debe contener una columna 'close' con los precios de cierre.
                                  Se espera que las velas estén ordenadas cronológicamente (la más antigua primero).

    Returns:
        str: "BUY" para señal de compra, "SELL" para señal de venta, 
             "HOLD" si no hay señal clara o "WAIT" si no hay suficientes datos.
    """
    # 1. Validación inicial de datos
    # Necesitamos al menos suficientes velas para calcular las Bandas de Bollinger.
    if df_klines.empty or len(df_klines) < BB_PERIOD:
        print(f"DEBUG: No hay suficientes datos para la estrategia de Bandas de Bollinger. Necesita {BB_PERIOD} velas, tiene {len(df_klines)}.")
        return "WAIT" # No hay suficientes datos para tomar una decisión

    # 2. Asegurarse de que la columna 'close' sea numérica
    df_klines['close'] = pd.to_numeric(df_klines['close'], errors='coerce')
    
    # Eliminar cualquier fila que haya quedado con NaN en 'close' después de la conversión
    df_klines.dropna(subset=['close'], inplace=True)

    # Volver a verificar la cantidad de datos después de limpiar
    if len(df_klines) < BB_PERIOD:
        print(f"DEBUG: No hay suficientes datos válidos después de la limpieza. Necesita {BB_PERIOD} velas, tiene {len(df_klines)}.")
        return "WAIT"

    # 3. Calcular las Bandas de Bollinger
    # Media Móvil Central (Middle Band)
    df_klines['BB_Middle'] = df_klines['close'].rolling(window=BB_PERIOD).mean()
    
    # Desviación estándar
    df_klines['BB_StdDev'] = df_klines['close'].rolling(window=BB_PERIOD).std()
    
    # Banda Superior (Upper Band)
    df_klines['BB_Upper'] = df_klines['BB_Middle'] + (df_klines['BB_StdDev'] * BB_STD_DEV)
    
    # Banda Inferior (Lower Band)
    df_klines['BB_Lower'] = df_klines['BB_Middle'] - (df_klines['BB_StdDev'] * BB_STD_DEV)

    # 4. Eliminar las filas iniciales que contienen valores NaN después del cálculo
    df_klines.dropna(inplace=True)

    # 5. Volver a verificar que tengamos al menos una fila después de dropna para tomar una decisión
    if df_klines.empty:
        print("DEBUG: No hay suficientes datos después de calcular Bandas de Bollinger y limpiar NaNs.")
        return "WAIT"

    # 6. Obtener la última fila para la lógica de la señal
    last_row = df_klines.iloc[-1]
    current_price = last_row['close']
    bb_upper = last_row['BB_Upper']
    bb_lower = last_row['BB_Lower']
    bb_middle = last_row['BB_Middle']

    # 7. Lógica de la Estrategia de Bandas de Bollinger
    # Señal de COMPRA: El precio cierra por debajo de la banda inferior
    if current_price < bb_lower:
        print(f"DEBUG: Señal detectada: BUY (Precio {current_price:.2f} < Banda Inferior {bb_lower:.2f})")
        return "BUY" 
    
    # Señal de VENTA: El precio cierra por encima de la banda superior
    elif current_price > bb_upper:
        print(f"DEBUG: Señal detectada: SELL (Precio {current_price:.2f} > Banda Superior {bb_upper:.2f})")
        return "SELL"
    
    # Si el precio está entre las bandas o toca la media, mantener posición o esperar
    else:
        print(f"DEBUG: Señal detectada: HOLD (Precio {current_price:.2f} entre bandas. Central: {bb_middle:.2f}, Superior: {bb_upper:.2f}, Inferior: {bb_lower:.2f})")
        return "HOLD"
# main.py
import time
import pandas as pd
from datetime import datetime

# Importa los módulos de tu proyecto
import config # Para acceder a los parámetros de configuración
from services.bybit_client import BybitClient # Tu clase para interactuar con Bybit
from strategies.simple_ma_strategy import generate_signal # Tu función de estrategia
from services.trade_logger import log_trade # Tu función para registrar operaciones

def main_bot_loop():
    print("Iniciando Bot de Trading de Bybit...")
    print("---------------------------------------")

    # 1. Inicializa el cliente de la API de Bybit
    api_client = BybitClient(testnet=config.TESTNET)
    print(f"Bybit API Client inicializado. Modo Testnet: {config.TESTNET}\n")

    # Bucle principal del bot: se ejecuta continuamente
    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n--- INICIO DE CICLO: {current_time} ---")
            print(f"Obteniendo datos de mercado para {config.SYMBOL} con intervalo {config.INTERVAL}...")

            # 2. Obtener datos de mercado (Klines)
            klines_data = api_client.get_klines(config.SYMBOL, config.INTERVAL, limit=200) 
            
            if not klines_data:
                print("Advertencia: No se pudieron obtener Klines. Reintentando en 1 minuto...")
                time.sleep(60)
                continue

            # Convertir los datos de klines a un DataFrame de Pandas
            df_klines = pd.DataFrame(klines_data, columns=[
                'start_time', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            df_klines[['open', 'high', 'low', 'close', 'volume']] = \
                df_klines[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df_klines['start_time'] = pd.to_datetime(df_klines['start_time'].astype(int), unit='ms')
            df_klines = df_klines.set_index('start_time').sort_index()

            # Asegurarse de que el DataFrame no esté vacío después del procesamiento
            if df_klines.empty:
                print("Advertencia: El DataFrame de Klines está vacío o contiene datos inválidos después del procesamiento. Reintentando...")
                time.sleep(60)
                continue

            # 3. Generar la señal de trading usando la estrategia
            signal = generate_signal(df_klines.copy()) 
            current_price = df_klines['close'].iloc[-1]
            print(f"Precio actual de {config.SYMBOL}: {current_price:.2f}")
            print(f"Señal de la estrategia: {signal}")

            # 4. Obtener información de la posición actual en Bybit
            current_position_size, current_position_side, current_avg_entry_price = api_client.get_current_position(config.SYMBOL)
            
            # 5. Obtener el balance actual de la cuenta (en USDT, o la moneda base)
            current_balance = api_client.get_wallet_balance("USDT")
            
            print(f"Balance actual (USDT): {current_balance:.2f} | Tamaño de posición actual: {current_position_size} | Lado: {current_position_side or 'Ninguno'}")
            if current_position_size > 0 and current_avg_entry_price is not None:
                print(f"  (Precio de entrada promedio: {current_avg_entry_price:.2f})")

            # 6. Ejecutar operaciones según la señal y la posición actual
            if signal == "BUY":
                if current_position_size == 0:
                    print(f"Señal de COMPRA: Abriendo posición LONG de {config.TRADE_QUANTITY} {config.SYMBOL}...")
                    order_response = api_client.place_order(config.SYMBOL, "Buy", config.TRADE_QUANTITY)
                    if order_response:
                        print(f"  Orden de compra enviada. ID: {order_response.get('orderId')}")
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Buy", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                elif current_position_side == "Sell": 
                    print(f"Señal de COMPRA: Hay posición SHORT. Cerrando SHORT y abriendo LONG...")
                    close_qty = current_position_size
                    
                    pnl_on_close = 0.0 # Inicializar por defecto
                    if current_avg_entry_price is not None:
                        pnl_on_close = (current_avg_entry_price - current_price) * close_qty
                    
                    api_client.close_position(config.SYMBOL, current_position_side, close_qty)
                    print(f"  Posición SHORT de {close_qty} {config.SYMBOL} cerrada. PnL estimado: {pnl_on_close:.2f}")
                    log_trade(config.SYMBOL, "CLOSE_POSITION", "Buy", close_qty, current_price, 
                              pnl=pnl_on_close, balance_after_trade=current_balance, status="CLOSED SHORT")
                    
                    time.sleep(5) # Esperar un momento para asegurar que la orden de cierre se procese

                    order_response = api_client.place_order(config.SYMBOL, "Buy", config.TRADE_QUANTITY)
                    if order_response:
                        print(f"  Orden de compra para LONG enviada. ID: {order_response.get('orderId')}")
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Buy", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                else: # Ya en posición Long (current_position_side == "Buy")
                    print("Señal de COMPRA: Ya en posición LONG. Manteniendo.")
            
            elif signal == "SELL":
                if current_position_size == 0:
                    print(f"Señal de VENTA: Abriendo posición SHORT de {config.TRADE_QUANTITY} {config.SYMBOL}...")
                    order_response = api_client.place_order(config.SYMBOL, "Sell", config.TRADE_QUANTITY)
                    if order_response:
                        print(f"  Orden de venta enviada. ID: {order_response.get('orderId')}")
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Sell", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                elif current_position_side == "Buy": 
                    print(f"Señal de VENTA: Hay posición LONG. Cerrando LONG y abriendo SHORT...")
                    close_qty = current_position_size
                    
                    pnl_on_close = 0.0 # Inicializar por defecto
                    if current_avg_entry_price is not None:
                        pnl_on_close = (current_price - current_avg_entry_price) * close_qty
                    
                    api_client.close_position(config.SYMBOL, current_position_side, close_qty)
                    print(f"  Posición LONG de {close_qty} {config.SYMBOL} cerrada. PnL estimado: {pnl_on_close:.2f}")
                    log_trade(config.SYMBOL, "CLOSE_POSITION", "Sell", close_qty, current_price, 
                              pnl=pnl_on_close, balance_after_trade=current_balance, status="CLOSED LONG")
                    
                    time.sleep(5) # Esperar un momento para asegurar que la orden de cierre se procese
                    
                    order_response = api_client.place_order(config.SYMBOL, "Sell", config.TRADE_QUANTITY)
                    if order_response:
                        print(f"  Orden de venta para SHORT enviada. ID: {order_response.get('orderId')}")
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Sell", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                else: # Ya en posición Short (current_position_side == "Sell")
                    print("Señal de VENTA: Ya en posición SHORT. Manteniendo.")
            
            elif signal == "HOLD" or signal == "WAIT":
                print("Señal de HOLD/WAIT: No se toma ninguna acción.")

            print(f"Esperando {config.CHECK_INTERVAL_SECONDS} segundos hasta la próxima verificación...")
            print("--- FIN DE CICLO ---")
            time.sleep(config.CHECK_INTERVAL_SECONDS) 

        except Exception as e:
            print(f"\n--- ERROR EN CICLO ---")
            print(f"¡Un error inesperado ocurrió en el bucle principal! Detalles: {e}")
            print("Reintentando en 5 minutos para evitar saturar la API o la CPU...")
            print("---------------------------------------")
            time.sleep(300) # Tiempo de espera más largo en caso de error

if __name__ == "__main__":
    main_bot_loop()
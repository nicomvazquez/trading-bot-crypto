# services/bybit_client.py

import os
import pandas as pd
import uuid # Para generar IDs de órdenes simuladas
from datetime import datetime # Importar datetime para los timestamps de depuración
from dotenv import load_dotenv # Cargar las variables de entorno para el cliente REAL

# Carga las variables de entorno del archivo .env al inicio de la ejecución
load_dotenv() # Esto es crucial para que BybitClient (real) pueda leer las claves

class BybitClient:
    def __init__(self, testnet=False):
        # Obtiene las claves API de las variables de entorno
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError("BYBIT_API_KEY o BYBIT_API_SECRET no se encontraron en el archivo .env. Asegúrate de configurarlos.")

        # Importar HTTP aquí para el cliente real, ya que no se usa en el simulado
        from pybit.unified_trading import HTTP
        
        # Inicializa la sesión HTTP con la API unificada de Bybit
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        print(f"Bybit API Client (Real) inicializado (Testnet: {testnet})")

    def get_klines(self, symbol, interval, limit=200):
        """
        Obtiene datos de velas (candlesticks) de Bybit.
        symbol: El par de trading (ej. "BTCUSDT")
        interval: La temporalidad de las velas (ej. "1", "5", "60", "D")
        limit: Número de velas a obtener (máximo 1000 por solicitud).
        """
        try:
            response = self.session.get_kline(
                category="linear", # Para futuros perpetuos (USD-M)
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            if response and 'result' in response and 'list' in response['result']:
                # Las klines se devuelven en orden descendente (las más nuevas primero).
                # Las invertimos para que las más antiguas estén al principio, que es útil para análisis.
                return response['result']['list'][::-1]
            else:
                print(f"Error al obtener klines para {symbol} ({interval}): {response}")
                return []
        except Exception as e:
            print(f"Excepción en get_klines para {symbol} ({interval}): {e}")
            return []

    def place_order(self, symbol, side, qty, order_type="Market"):
        """
        Coloca una orden de trading en Bybit.
        symbol: El par de trading (ej. "BTCUSDT")
        side: "Buy" (compra) o "Sell" (venta)
        qty: Cantidad de la orden (como string para la API)
        order_type: "Market" (mercado) o "Limit" (límite). Por defecto "Market".
        """
        try:
            order_params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "qty": str(qty), # La cantidad debe ser un string para la API
                "isLeverage": 1, # Generalmente 1 para futuros perpetuos (apalancamiento habilitado)
                "timeInForce": "GTC" # Good Till Cancel (la orden permanece hasta que se ejecuta o se cancela)
            }
            
            response = self.session.place_order(**order_params)
            print(f"Respuesta de orden enviada: {response}")
            if response and 'result' in response and 'orderId' in response['result']:
                return response['result'] # Retorna el ID de la orden y otros detalles
            return None
        except Exception as e:
            print(f"Excepción al enviar orden para {symbol} ({side} {qty}): {e}")
            return None

    def get_wallet_balance(self, coin="USDT"):
        """
        Obtiene el balance de la billetera para una moneda específica.
        coin: La moneda a consultar (ej. "USDT", "BTC")
        """
        try:
            response = self.session.get_wallet_balance(
                accountType="UNIFIED", # Tipo de cuenta (Unified Trading Account, SPOT, CONTRACT)
                coin=coin
            )
            if response and 'result' in response and 'list' in response['result'] and len(response['result']['list']) > 0:
                # La respuesta puede contener balances de varias cuentas. Buscamos la de 'UNIFIED' y el 'coin' específico.
                for account in response['result']['list']:
                    for c in account['coin']:
                        if c['coin'] == coin:
                            return float(c['walletBalance'])
            return 0.0 # Retorna 0.0 si no se encuentra el balance o hay un error
        except Exception as e:
            print(f"Excepción al obtener balance para {coin}: {e}")
            return 0.0

    def get_current_position(self, symbol):
        """
        Obtiene el tamaño, el lado y el precio de entrada promedio de la posición actual para un símbolo dado.
        Retorna (tamaño, lado_de_la_posicion, avg_entry_price)
        lado_de_la_posicion puede ser "Buy", "Sell" o "None".
        avg_entry_price será float o None si no hay posición.
        """
        try:
            response = self.session.get_positions(category="linear", symbol=symbol)
            
            if response and response['retCode'] == 0 and 'list' in response['result']:
                positions = response['result']['list']
                
                if positions:
                    position = positions[0] 
                    # Asegurarse de manejar cadenas vacías o None antes de convertir a float
                    size = float(position['size']) if position['size'] not in [None, ''] else 0.0
                    side = position['side'].capitalize() if position['side'] not in [None, ''] else "None"
                    avg_entry_price = float(position['avgPrice']) if position['avgPrice'] not in [None, ''] else 0.0
                    
                    if size > 0:
                        return size, side, avg_entry_price 
                    else:
                        return 0.0, "None", None 
                else:
                    return 0.0, "None", None 
            else:
                print(f"Error al obtener posiciones (Bybit API): {response}")
                return 0.0, "None", None 
        except Exception as e:
            print(f"Excepción al obtener información de la posición para {symbol}: {e}")
            return 0.0, "None", None 

    def close_position(self, symbol, current_position_side, qty):
        """
        Cierra una posición abierta.
        symbol: El par de trading
        current_position_side: El lado de la posición actualmente ABIERTA ("Buy" o "Sell").
        qty: El tamaño de la posición a cerrar.
        """
        close_order_side = None
        if current_position_side == "Buy": 
            close_order_side = "Sell" 
        elif current_position_side == "Sell": 
            close_order_side = "Buy" 
        else:
            print(f"Error: Lado de posición desconocido o no válido para cerrar: {current_position_side}")
            return None

        if close_order_side:
            print(f"Cerrando posición: Símbolo={symbol}, Lado de cierre={close_order_side}, Cantidad={qty}")
            return self.place_order(symbol, close_order_side, qty, order_type="Market")
        return None

# --- CLASE DE CLIENTE SIMULADO PARA BACKTESTING ---
class SimulatedBybitClient:
    def __init__(self, historical_data_df: pd.DataFrame, initial_capital: float = 10000.0, commission_rate: float = 0.00075):
        self.current_balance = initial_capital
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate 
        
        self.current_position = {
            "symbol": None,
            "size": 0.0,
            "side": "None", # "Long", "Short", "None"
            "entry_price": 0.0
        }
        
        print(f"Simulated Bybit Client inicializado con capital: {initial_capital:.2f} USDT (Comisión simulada: {commission_rate*100:.3f}%)")

    def get_klines(self, symbol: str, interval: str, limit: int):
        """Placeholder para compatibilidad con la interfaz del cliente real."""
        return []

    def get_current_position(self, symbol: str):
        """
        Retorna el estado actual de la posición simulada.
        Retorna (tamaño, lado_de_la_posicion, avg_entry_price)
        """
        pos = self.current_position
        return pos["size"], pos["side"], pos["entry_price"] 

    def get_wallet_balance(self, coin: str = "USDT") -> float:
        """
        Simula la obtención del balance de la billetera.
        """
        return self.current_balance
    
    def execute_order(self, symbol: str, order_side: str, quantity: float, price: float, timestamp: datetime):
        """
        Simula la ejecución de una orden de compra/venta y gestiona la posición y el balance.
        Esta versión asume que el backtester maneja la lógica de cierre/apertura secuencialmente.
        Las comisiones NO se calculan ni se restan en esta versión simplificada.

        Args:
            symbol (str): Símbolo de trading (ej. "BTCUSDT").
            order_side (str): Lado de la orden a ejecutar ("Buy" o "Sell").
            quantity (float): Cantidad del activo a operar.
            price (float): Precio de ejecución de la orden.
            timestamp (datetime): Timestamp de la vela actual para el log.
        
        Returns:
            dict: Diccionario con el resultado de la operación simulada.
        """
        pnl_on_this_trade = 0.0 # PnL materializado por esta operación (si es un cierre)
        order_id = str(uuid.uuid4())
        
        # Estado actual de la posición ANTES de esta orden
        current_size = self.current_position["size"]
        current_side = self.current_position["side"]
        current_entry_price = self.current_position["entry_price"]

        print(f"\n--- SIMULACIÓN DE ORDEN ({timestamp}) ---")
        print(f"  Orden solicitada: {order_side} {quantity:.5f} {symbol} @ {price:.5f}")
        print(f"  Posición ANTES: size={current_size:.5f}, side={current_side}, entry_price={current_entry_price:.5f}")
        print(f"  Balance ANTES: {self.current_balance:.2f} USDT")

        # Determinar el tipo de operación
        is_closing = False
        is_opening = False
        is_extending = False

        if current_size > 1e-9 and (
            (current_side == "Long" and order_side == "Sell") or
            (current_side == "Short" and order_side == "Buy")
        ):
            is_closing = True
        elif current_size < 1e-9: # Si no hay posición
            is_opening = True
        elif current_size > 1e-9 and current_side == order_side:
            is_extending = True
        else:
            # Este else cubre el caso de intentar abrir una posición opuesta sin cerrar la anterior,
            # lo cual el backtester debería manejar con dos llamadas separadas.
            print(f"  ADVERTENCIA: Orden '{order_side}' {quantity} NO encaja en una operación significativa (cierre, apertura, extensión). Posición actual: {current_side} {current_size}.")
            return {
                "success": False,
                "order_id": order_id,
                "pnl": 0.0,
                "balance_after_trade": self.current_balance
            }
            
        if is_closing:
            close_amount = min(quantity, current_size) # Cantidad que realmente se cierra
            
            if current_side == "Long":
                pnl_on_this_trade = (price - current_entry_price) * close_amount
            else: # current_side == "Short"
                pnl_on_this_trade = (current_entry_price - price) * close_amount
            
            self.current_balance += pnl_on_this_trade # Actualiza el balance con el PnL materializado
            
            self.current_position["size"] -= close_amount
            
            if self.current_position["size"] <= 1e-9: # Si la posición se cierra completamente
                self.current_position["size"] = 0.0
                self.current_position["side"] = "None"
                self.current_position["entry_price"] = 0.0
                print(f"  Cierre COMPLETO de posición {current_side}. PnL Materializado: {pnl_on_this_trade:.2f} USDT.")
            else:
                print(f"  Cierre PARCIAL de posición {current_side}. PnL Materializado: {pnl_on_this_trade:.2f} USDT. Restante: {self.current_position['size']:.5f}")
            
        elif is_opening:
            self.current_position["symbol"] = symbol
            self.current_position["size"] = quantity
            self.current_position["side"] = "Long" if order_side == "Buy" else "Short"
            self.current_position["entry_price"] = price 
            print(f"  Apertura de nueva posición: {self.current_position['side']} (Cantidad: {quantity:.5f} @ {price:.5f})")
            pnl_on_this_trade = 0.0 # No hay PnL materializado en una apertura

        elif is_extending:
            old_total_value = current_size * current_entry_price
            new_trade_value = quantity * price
            new_total_size = current_size + quantity
            
            new_avg_entry_price = (old_total_value + new_trade_value) / new_total_size if new_total_size > 0 else 0.0

            self.current_position["size"] = new_total_size
            self.current_position["entry_price"] = new_avg_entry_price
            print(f"  Extensión de posición {self.current_position['side']}: Nueva Cantidad: {self.current_position['size']:.5f}, Nuevo Precio Entrada: {self.current_position['entry_price']:.5f}")
            pnl_on_this_trade = 0.0 # No hay PnL materializado en una extensión
        
        print(f"  Posición FINAL: size={self.current_position['size']:.5f}, side={self.current_position['side']}, entry_price={self.current_position['entry_price']:.5f}")
        print(f"  Balance FINAL: {self.current_balance:.2f} USDT")
        print("-----------------------------------")

        return {
            "success": True,
            "order_id": order_id,
            "pnl": pnl_on_this_trade, 
            "balance_after_trade": self.current_balance
        }
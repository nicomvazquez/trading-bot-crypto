# 🤖 Bot de Trading con Medias Móviles para Bybit (Python)

Este es un bot de trading automatizado desarrollado en Python que opera en la plataforma Bybit capaz de usar distintos tipos de estrategias.

## 🚀 Características Principales

* **Integración con Bybit:** Se conecta a la API unificada de Bybit para obtener datos de mercado (velas), gestionar posiciones y ejecutar órdenes de compra/venta/cierre.
* **Registro Detallado (Logging):** Registra cada operación (apertura, cierre) en un archivo CSV fácil de leer. Se genera un nuevo archivo de log por cada sesión del bot, organizado en una carpeta `data/`.
* **Gestión de Posiciones:** Monitorea tu posición actual en Bybit y ajusta las operaciones (abrir Long/Short, cerrar y revertir) según la señal de la estrategia.
* **Configuración Flexible:** Todos los parámetros clave (símbolo, temporalidad, cantidad de trading, periodos SMA, modo Testnet) son fácilmente configurables en un archivo `config.py`.
* **Manejo de Errores:** Incluye un manejo básico de excepciones para reintentar operaciones y evitar fallos críticos.

## ⚙️ Requisitos

Antes de ejecutar el bot, asegúrate de tener lo siguiente:

* **Python 3.x** instalado.
* **Cuenta en Bybit:** Puedes usar una cuenta de Testnet para pruebas (recomendado inicialmente) o una cuenta real.
* **API Keys de Bybit:** Genera tus API keys en la configuración de tu cuenta de Bybit con los permisos necesarios (Lectura de mercado, Órdenes, Posiciones, Balance). **¡Guárdalas de forma segura y NO las compartas!**


3.  **Estructura de Archivos:** La organización del proyecto es modular para mantener el código limpio y escalable:

    ```
    tu_bot_trading/
    ├── backtester.py                 # Motor principal para ejecutar el backtest
    ├── config.py                     # Archivo de configuración global
    ├── data/
    │   ├── logs/                     # Carpeta donde se guardan los logs CSV de cada backtest
    │   └── historical_data.csv       # Archivo con los datos históricos para el backtest
    ├── services/
    │   ├── __init__.py
    │   ├── simulated_bybit_client.py  # Clase que simula la interacción con la API de Bybit
    │   └── trade_logger.py          # Servicio para registrar las operaciones en un CSV
    └── strategies/
        ├── __init__.py
        ├── simple_ma_strategy.py     # Lógica de la estrategia de Medias Móviles
        ├── rsi_strategy.py           # Lógica de la estrategia de RSI
        └── bollinger_bands_strategy.py # Lógica de la estrategia de Bandas de Bollinger
    ```

## 🛠️ Guía de Uso del Backtester

### 1. Pre-requisitos

Asegúrate de tener **Python 3.x** instalado en tu sistema.

### 2. Instalación Paso a Paso

1.  **Clonar el repositorio:**
    Abre tu terminal y clona el proyecto con el siguiente comando:
    ```bash
    git clone [https://github.com/tu-usuario/tu-repositorio-del-bot.git](https://github.com/tu-usuario/tu-repositorio-del-bot.git)
    cd tu-repositorio-del-bot
    ```

2.  **Configurar un entorno virtual (recomendado):**
    Crea un entorno virtual para aislar las dependencias del proyecto y actívalo.
    ```bash
    python -m venv venv
    # En Windows:
    .\venv\Scripts\activate
    # En macOS/Linux:
    source venv/bin/activate
    ```

3.  **Instalar las dependencias:**
    Con el entorno virtual activado, instala todas las librerías necesarias con el siguiente comando:
    ```bash
    pip install pandas pandas_ta matplotlib
    ```
    (Si tienes un archivo `requirements.txt`, puedes usar `pip install -r requirements.txt`).

### 3. Configuración del Proyecto

* **`config.py`**: Edita este archivo para definir los parámetros del backtest, como el capital inicial (`BACKTEST_INITIAL_CAPITAL`), el símbolo (`BACKTEST_SYMBOL`) y el nombre del archivo de datos (`BACKTEST_DATA_FILE`).
* **`data/`**: Coloca tus datos históricos en formato CSV en esta carpeta. El archivo debe contener las columnas `Timestamp`, `Open`, `High`, `Low`, `Close`, `Volume`. El nombre del archivo debe coincidir con `BACKTEST_DATA_FILE` en `config.py`.
* **Seleccionar Estrategia**: En el archivo `backtester.py`, asegúrate de que la línea de importación apunte a la estrategia que deseas probar. Por ejemplo, `from strategies.rsi_strategy import generate_signal`.

### 4. Ejecutar el Backtest

Una vez configurado, ejecuta el script `backtester.py` desde tu terminal:

```bash
python backtester.py

``` 


## 🛠️ Configuración

Para configurar el bot, necesitarás establecer variables de entorno y ajustar el archivo `config.py`.

### 1. Configurar Variables de Entorno (¡CRÍTICO para la seguridad!)

Por motivos de seguridad, tus API Keys de Bybit **NO deben estar directamente en el código**. Debes configurarlas como variables de entorno en tu sistema operativo.

* **`BYBIT_API_KEY`**: Tu clave API de Bybit.
* **`BYBIT_API_SECRET`**: Tu clave secreta API de Bybit.

**Cómo configurarlas (ejemplos):**

* **En Linux/macOS (para la sesión actual de terminal):**
    ```bash
    export BYBIT_API_KEY="tu_clave_api_aqui"
    export BYBIT_API_SECRET="tu_secreto_api_aqui"
    ```
    (Para hacerlas persistentes después de cerrar la terminal, añádelas a tu archivo de configuración de shell como `.bashrc`, `.zshrc` o `.profile`.)

* **En Windows (CMD - para la sesión actual):**
    ```cmd
    set BYBIT_API_KEY="tu_clave_api_aqui"
    set BYBIT_API_SECRET="tu_secreto_api_aqui"
    ```

* **En Windows (PowerShell - para la sesión actual):**
    ```powershell
    $env:BYBIT_API_KEY="tu_clave_api_aqui"
    $env:BYBIT_API_SECRET="tu_secreto_api_aqui"
    ```
    (Para hacerlas persistentes, puedes buscarlas en las "Propiedades del Sistema" -> "Variables de entorno" y agregarlas de forma permanente, o usar métodos de PowerShell para setearlas en tu perfil de usuario).

**¡IMPORTANTE!** Después de configurar las variables de entorno, es posible que necesites **reiniciar tu terminal** o el IDE desde donde ejecutas el bot para que los cambios surtan efecto.

### 2. Ajustar `config.py`

Abre el archivo `config.py` y ajusta los siguientes parámetros. **Las API Keys serán cargadas automáticamente desde las variables de entorno, por lo que NO las pondrás directamente aquí.**

* **`TESTNET`**: Establece `True` para operar en la red de prueba (¡ALTAMENTE RECOMENDADO para probar!) o `False` para operar con dinero real.
* **`SYMBOL`**: El par de trading que deseas operar (ej. `"BTCUSDT"`, `"ETHUSDT"`).
* **`INTERVAL`**: La temporalidad de las velas que usará la estrategia (ej. `"1"` para 1 minuto, `"5"` para 5 minutos, `"60"` para 1 hora). Ten en cuenta que la API de Bybit generalmente no soporta intervalos menores a 1 minuto.
* **`TRADE_QUANTITY`**: La cantidad de la moneda base a operar en cada transacción (ej. `0.001` para BTC).
* **`CHECK_INTERVAL_SECONDS`**: El tiempo en segundos que el bot esperará entre cada ciclo de verificación y ejecución. Esto es independiente del `INTERVAL` de las velas.

**Ejemplo de `config.py` (ahora sin las claves API directamente):**

```python
# config.py

# --- Configuración del Bot ---
TESTNET = True
SYMBOL = "BTCUSDT"
INTERVAL = "1"
TRADE_QUANTITY = 0.001
CHECK_INTERVAL_SECONDS = 60

### 5. Analizar los Resultados

El archivo de log (`CSV`) te permitirá analizar la evolución del balance y el PnL.  
Podés usar herramientas como:

- **Google Sheets**
- **Excel**
- O un script en Python con `matplotlib`:

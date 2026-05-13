# Crypto Trading Bot

Bot de trading automatizado de criptomonedas. Pega tu análisis de ChatGPT (u otra fuente) y el bot interpreta las señales y ejecuta operaciones en Bybit.

## Características

- **Parsing inteligente**: Interpreta texto libre en español o inglés — detecta señales de compra/venta, precios de entrada, stop-loss y take-profit
- **Paper Trading**: Motor de simulación completo para probar estrategias sin riesgo
- **Datos de mercado**: Obtiene precios en tiempo real desde Bybit
- **Ejecución automática**: Ejecuta operaciones basadas en tu análisis
- **Dashboard CLI**: Interfaz de línea de comandos con tablas formateadas y colores
- **Gestión de riesgo**: Límites de posición y confianza mínima configurables
- **Estado persistente**: El portafolio de paper trading se guarda en disco

## Requisitos

- Python >= 3.11
- Credenciales API de Bybit (para datos de mercado y trading)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Guillerm25/crypto-trading-bot.git
cd crypto-trading-bot

# Instalar dependencias con uv
uv sync

# Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves de Bybit
```

## Configuración

Edita el archivo `.env` con tus credenciales:

```env
# Bybit API (para datos de mercado)
BYBIT_API_KEY=your-api-key
BYBIT_API_SECRET=your-api-secret

# Bybit Testnet (para demo wallet)
BYBIT_TESTNET_API_KEY=your-testnet-api-key
BYBIT_TESTNET_API_SECRET=your-testnet-api-secret

# Modo de trading: paper (simulación), sandbox (testnet) o live
TRADING_MODE=paper
PAPER_TRADING_BALANCE=10000
```

## Uso

### 1. Pegar análisis y ejecutar trades

```bash
# Interactivo: pega tu análisis, luego Ctrl+D
uv run trading-bot execute

# Desde un archivo
uv run trading-bot execute -f mi_analisis.txt

# Con ejecución automática
uv run trading-bot execute --auto-execute

# Desde un archivo con ejecución automática
uv run trading-bot execute -f mi_analisis.txt --auto-execute
```

**Ejemplo de texto que el bot interpreta:**

```
Recomiendo comprar BTC con entrada en $80,000, stop-loss en $78,000 y 
take-profit en $85,000. Confianza: 75%.

ETH: mantener posición actual (hold).

Vender SOL con precio objetivo $90.
```

El bot detecta automáticamente:
- Símbolos: BTC, ETH, SOL (y 20+ criptomonedas más)
- Señales: comprar/buy, vender/sell, mantener/hold
- Precios: entrada, stop-loss, take-profit
- Confianza: porcentajes

### 2. Ver datos de mercado

```bash
uv run trading-bot market
uv run trading-bot market -s BTC/USDT,ETH/USDT
```

### 3. Ver estado del portafolio

```bash
uv run trading-bot status
```

### 4. Resetear paper trading

```bash
uv run trading-bot reset
```

## Arquitectura

```
src/trading_bot/
├── main.py          # CLI principal (Click)
├── config.py        # Configuración (Pydantic Settings)
├── models.py        # Modelos de datos (Pydantic)
├── text_parser.py   # Parser de texto libre → señales de trading
├── market_data.py   # Datos de mercado (Bybit via ccxt)
├── paper_trader.py  # Motor de paper trading
├── sandbox_trader.py # Trading en Bybit Testnet
├── executor.py      # Ejecución de órdenes
└── dashboard.py     # Dashboard CLI (Rich)
```

## Flujo de operación

1. **Obtener análisis**: Genera tu análisis en ChatGPT u otra IA
2. **Pegar en el bot**: Ejecuta `trading-bot execute` y pega el texto
3. **Parsing automático**: El bot detecta símbolos, señales y precios
4. **Ejecutar**: Con `--auto-execute`, las operaciones se ejecutan en paper trading
5. **Reportar**: Se muestra el portafolio actualizado

## Tests

```bash
uv run pytest
```

## Disclaimer

Este software es solo para fines educativos y de investigación. El trading de criptomonedas conlleva un riesgo significativo. No use este bot con dinero real sin entender completamente los riesgos involucrados. Los autores no se hacen responsables de pérdidas financieras.

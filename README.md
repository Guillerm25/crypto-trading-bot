# Crypto Trading Bot

Bot de trading automatizado de criptomonedas con análisis impulsado por IA (ChatGPT de OpenAI) e integración con Coinbase.

## Características

- **Análisis con IA**: Utiliza ChatGPT (OpenAI) para analizar datos de mercado y generar recomendaciones de trading
- **Paper Trading**: Motor de simulación completo para probar estrategias sin riesgo
- **Datos de mercado**: Obtiene precios en tiempo real, velas OHLCV y volúmenes desde Coinbase
- **Ejecución automática**: Ejecuta operaciones basadas en las recomendaciones de la IA
- **Dashboard CLI**: Interfaz de línea de comandos con tablas formateadas y colores
- **Gestión de riesgo**: Stop-loss, take-profit, límites de posición y confianza mínima configurables
- **Estado persistente**: El portafolio de paper trading se guarda en disco

## Requisitos

- Python >= 3.11
- Clave API de OpenAI (para análisis con IA)
- Credenciales API de Coinbase (para trading en vivo, opcional para paper trading)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Guillerm25/crypto-trading-bot.git
cd crypto-trading-bot

# Instalar dependencias con uv
uv sync

# Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves API
```

## Configuración

Edita el archivo `.env` con tus credenciales:

```env
# Requerido para análisis con IA
OPENAI_API_KEY=sk-xxxxx

# Requerido solo para trading en vivo
COINBASE_API_KEY=your-api-key
COINBASE_API_SECRET=your-api-secret

# Modo de trading: paper (simulación) o live
TRADING_MODE=paper
PAPER_TRADING_BALANCE=10000
```

## Uso

### Ver datos de mercado

```bash
uv run trading-bot market
uv run trading-bot market -s BTC/USDT,ETH/USDT
```

### Ejecutar análisis con IA

```bash
uv run trading-bot analyze
uv run trading-bot analyze -s BTC/USDT,ETH/USDT
```

### Ejecutar un ciclo de trading

```bash
# Sin ejecución automática (solo muestra recomendaciones)
uv run trading-bot trade

# Con ejecución automática de paper trading
uv run trading-bot trade --auto-execute
```

### Bot en modo continuo

```bash
# Ejecutar cada hora (3600 segundos)
uv run trading-bot run

# Ejecutar cada 30 minutos
uv run trading-bot run -i 1800
```

### Ver estado del portafolio

```bash
uv run trading-bot status
```

### Resetear paper trading

```bash
uv run trading-bot reset
```

## Arquitectura

```
src/trading_bot/
├── main.py          # CLI principal (Click)
├── config.py        # Configuración (Pydantic Settings)
├── models.py        # Modelos de datos (Pydantic)
├── market_data.py   # Datos de mercado (Coinbase via ccxt)
├── ai_analyst.py    # Análisis con IA (ChatGPT/OpenAI)
├── paper_trader.py  # Motor de paper trading
├── executor.py      # Ejecución de órdenes
└── dashboard.py     # Dashboard CLI (Rich)
```

## Flujo de operación

1. **Obtener datos**: Se consultan precios, velas y volúmenes de Coinbase
2. **Analizar con IA**: ChatGPT analiza los datos y genera recomendaciones con niveles de confianza
3. **Filtrar señales**: Se filtran por confianza mínima y reglas de gestión de riesgo
4. **Ejecutar**: Las operaciones se ejecutan en paper trading (simulación) o en vivo
5. **Reportar**: Se muestra el informe, órdenes ejecutadas y estado del portafolio

## Tests

```bash
uv run pytest
```

## Disclaimer

Este software es solo para fines educativos y de investigación. El trading de criptomonedas conlleva un riesgo significativo. No use este bot con dinero real sin entender completamente los riesgos involucrados. Los autores no se hacen responsables de pérdidas financieras.

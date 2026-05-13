@echo off
title Crypto Trading Bot - Instalacion
echo ============================================
echo   Crypto Trading Bot - Instalacion
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado.
    echo Descargalo en: https://www.python.org/downloads/
    echo IMPORTANTE: Marca "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

echo [OK] Python encontrado:
python --version
echo.

:: Install uv
echo Instalando uv (gestor de paquetes)...
pip install uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se pudo instalar uv.
    pause
    exit /b 1
)
echo [OK] uv instalado.
echo.

:: Install dependencies
echo Instalando dependencias del bot...
uv sync
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias.
    pause
    exit /b 1
)
echo.
echo [OK] Dependencias instaladas.
echo.

:: Create .env if not exists
if not exist .env (
    copy .env.example .env >nul
    echo [INFO] Archivo .env creado. Editalo con tus credenciales de Bybit.
    echo        Abre .env con el Bloc de notas y configura:
    echo        - BYBIT_TESTNET_API_KEY
    echo        - BYBIT_TESTNET_API_SECRET
    echo        - TRADING_MODE=sandbox
    echo.
    echo        Crea tus credenciales en: https://testnet.bybit.com
) else (
    echo [OK] Archivo .env ya existe.
)

echo.
echo ============================================
echo   Instalacion completada!
echo   Ejecuta trading-bot.bat para usar el bot.
echo ============================================
pause

@echo off
title Crypto Trading Bot
cd /d "%~dp0"
chcp 65001 >nul 2>&1

:menu
cls
echo ============================================
echo   Crypto Trading Bot - Bybit
echo ============================================
echo.
echo   1. Ejecutar analisis (pegar texto)
echo   2. Ejecutar analisis con auto-execute
echo   3. Ejecutar desde archivo
echo   4. Ver precios de mercado
echo   5. Ver estado del portafolio
echo   6. Resetear portafolio (paper trading)
echo   7. Salir
echo.
echo ============================================
set /p opcion="Elige una opcion (1-7): "

if "%opcion%"=="1" goto ejecutar
if "%opcion%"=="2" goto autoexecutar
if "%opcion%"=="3" goto desde_archivo
if "%opcion%"=="4" goto mercado
if "%opcion%"=="5" goto estado
if "%opcion%"=="6" goto resetear
if "%opcion%"=="7" goto salir

echo Opcion no valida.
timeout /t 2 >nul
goto menu

:ejecutar
cls
echo ============================================
echo   Pega tu analisis y pulsa Ctrl+Z + Enter
echo ============================================
echo.
uv run trading-bot execute
echo.
pause
goto menu

:autoexecutar
cls
echo ============================================
echo   Pega tu analisis y pulsa Ctrl+Z + Enter
echo   (Las operaciones se ejecutaran automaticamente)
echo ============================================
echo.
uv run trading-bot execute --auto-execute
echo.
pause
goto menu

:desde_archivo
cls
set /p archivo="Ruta del archivo de analisis: "
if not exist "%archivo%" (
    echo [ERROR] Archivo no encontrado: %archivo%
    pause
    goto menu
)
uv run trading-bot execute -f "%archivo%" --auto-execute
echo.
pause
goto menu

:mercado
cls
echo ============================================
echo   Precios de Mercado
echo ============================================
echo.
uv run trading-bot market
echo.
pause
goto menu

:estado
cls
echo ============================================
echo   Estado del Portafolio
echo ============================================
echo.
uv run trading-bot status
echo.
pause
goto menu

:resetear
cls
echo.
uv run trading-bot reset
echo.
pause
goto menu

:salir
exit /b 0

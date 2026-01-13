@echo off
chcp 65001 >nul
title 🚀 Servidor Gerador de Etiquetas - Rede Local
color 0A

echo ================================================
echo   GERADOR DE ETIQUETAS - SERVIDOR DE REDE
echo ================================================
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado!
    echo Instale Python 3.8 ou superior: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Verificar se as dependências estão instaladas
echo 🔍 Verificando dependências...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 📦 Instalando Flask...
    pip install flask
)

pip show reportlab >nul 2>&1
if errorlevel 1 (
    echo 📦 Instalando ReportLab...
    pip install reportlab
)

:: Obter informações da rede
echo.
echo 🌐 Detectando configuração de rede...
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    set "IP=%%i"
    set "IP=!IP:~1!"
    echo 📍 IP Encontrado: !IP!
)

:: Iniciar servidor
echo.
echo 🚀 Iniciando servidor...
echo ================================================
echo.

python app.py

if errorlevel 1 (
    echo.
    echo ❌ ERRO: Não foi possível iniciar o servidor
    echo Verifique se a porta 5000 está disponível
    echo.
    pause
)
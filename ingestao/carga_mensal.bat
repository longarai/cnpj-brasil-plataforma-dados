@echo off
chcp 65001 >nul
title Carga mensal Receita Federal - Snowflake
echo ================================================
echo   CARGA MENSAL RECEITA FEDERAL - SNOWFLAKE
echo ================================================
echo.
python "%~dp0carga_mensal.py"
echo.
if errorlevel 1 (
  echo *** A CARGA FALHOU - leia as mensagens acima ***
) else (
  echo *** CARGA FINALIZADA - confira o resumo acima ***
)
echo.
pause

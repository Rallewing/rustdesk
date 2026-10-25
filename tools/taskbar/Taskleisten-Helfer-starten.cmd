@echo off
where pyw >nul 2>nul
if errorlevel 1 (
  echo Der vorhandene Python-Launcher pyw wurde nicht gefunden.
  echo Bitte Python 3.13 mit Python-Launcher verwenden.
  pause
  exit /b 1
)
start "" pyw -3.13 "%~dp0taskbar_helper.py"

@echo off
setlocal
set SCRIPT_DIR=%~dp0
set PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%
"%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%app\cli.py" %*

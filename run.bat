@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment...
  py -3 -m venv .venv
  if errorlevel 1 (echo Python 3 was not found. Install Python 3.12 or newer.& pause & exit /b 1)
)
call ".venv\Scripts\activate.bat"
python -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (echo Dependency installation failed. Check your network connection.& pause & exit /b 1)
rem Do not open the browser to another app if this local port is already occupied.
python tools\start_app.py
if errorlevel 1 (echo Could not open Beta Project Intelligence.& pause & exit /b 1)

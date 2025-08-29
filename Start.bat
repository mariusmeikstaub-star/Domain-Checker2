
@echo off
setlocal

REM -------- Domain Checker Quick Start (Windows) --------
REM Creates/uses a local venv with the default Python 3, installs deps, and launches Streamlit.

cd /d %~dp0

REM --- Check for Python ---
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [FEHLER] Python 3 nicht gefunden. Bitte installieren:
  echo https://www.python.org/downloads/
  pause
  exit /b 1
)

echo.
echo [1/4] Virtuelle Umgebung pruefen/anlegen (.venv)...
if not exist .venv (
  python -m venv .venv
)

echo.
echo [2/4] VENV aktivieren...
call .venv\Scripts\activate.bat

echo.
echo [3/4] Requirements installieren...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/4] Starte Streamlit App...
streamlit run app.py

endlocal
pause

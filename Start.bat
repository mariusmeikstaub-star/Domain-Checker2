
@echo off
setlocal

REM -------- Domain Checker Quick Start (Windows) --------
REM Creates/uses a local venv with Python 3.12, installs deps, and launches Streamlit.

where py >nul 2>nul
if errorlevel 1 (
  echo.
  echo [FEHLER] Python Launcher 'py' nicht gefunden. Bitte Python 3.12 installieren:
  echo https://www.python.org/downloads/
  pause
  exit /b 1
)

echo.
echo [1/5] Virtuelle Umgebung pruefen/anlegen (.venv, Python 3.12)...
py -3.12 -m venv .venv
if errorlevel 1 (
  echo.
  echo [HINWEIS] Konnte ggf. kein Python 3.12 finden. Stelle sicher, dass Python 3.12 installiert ist.
  pause
)

echo.
echo [2/5] VENV aktivieren...
call .venv\Scripts\activate.bat

echo.
echo [3/5] Pip aktualisieren...
python -m pip install --upgrade pip

echo.
echo [4/5] Requirements installieren...
pip install -r requirements.txt

echo.
echo [5/5] Starte Streamlit App...
streamlit run app.py

endlocal

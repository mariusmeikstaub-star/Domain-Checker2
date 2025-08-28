
@echo off
setlocal
REM Optional: silence pip version check that errors on some systems
set PIP_DISABLE_PIP_VERSION_CHECK=1
IF NOT EXIST .venv (
  py -3.12 -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt --disable-pip-version-check
streamlit run app.py

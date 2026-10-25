@echo off
title Crowd Threat Monitor
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"
python -m streamlit run app.py --theme.base light --theme.primaryColor "#0EA5A0" --theme.backgroundColor "#F4F6FB" --theme.secondaryBackgroundColor "#0B1E33" --theme.textColor "#0F172A" --theme.font "sans serif"
pause
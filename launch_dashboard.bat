@echo off
title ESADE Sustainable Finance Dashboard
echo.
echo  Starting ESADE Sustainable Finance Dashboard...
echo  Open your browser at: http://localhost:8501
echo.
venv\Scripts\streamlit.exe run app.py --server.headless=true
pause

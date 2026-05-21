@echo off
call "%~dp0venv\Scripts\activate.bat"
jupyter notebook --notebook-dir="%~dp0notebooks"

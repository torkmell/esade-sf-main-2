@echo off
echo ============================================
echo  Sustainable Finance Project - Setup
echo ============================================
echo.

echo [1/3] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python first (see instructions below).
    pause
    exit /b 1
)

echo [2/3] Activating environment and installing packages...
call venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt

echo [3/3] Registering Jupyter kernel...
python -m ipykernel install --user --name=sustainable-finance --display-name "Sustainable Finance"

echo.
echo ============================================
echo  Setup complete!
echo  To start Jupyter: run  launch_jupyter.bat
echo ============================================
pause

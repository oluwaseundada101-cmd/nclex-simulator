@echo off
title NGN NCLEX Simulator — Local Launcher
color 0A

echo ==========================================
echo   NGN NCLEX Simulator — Local Launcher
echo ==========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.11 from:
    echo https://www.python.org/downloads/release/python-3119/
    echo.
    echo IMPORTANT: During install, check the box that says
    echo "Add Python to PATH" before clicking Install.
    echo.
    pause
    exit
)

echo Python found. Checking for Streamlit...
echo.

:: Install/upgrade streamlit if not present
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Streamlit for the first time...
    echo This will take about 1-2 minutes on the first run.
    echo.
    pip install streamlit==1.40.2
)

echo.
echo ==========================================
echo  Starting your NCLEX Simulator...
echo  Your browser will open automatically.
echo  To stop: close this window or press Ctrl+C
echo ==========================================
echo.

:: Run the app — looks for app.py in the same folder as this .bat file
cd /d "%~dp0"
python -m streamlit run app.py --server.headless false --browser.gatherUsageStats false

pause

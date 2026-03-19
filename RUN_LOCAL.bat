@echo off
echo ==========================================
echo   NGN NCLEX Simulator v4 - Quick Launch
echo ==========================================
echo.

REM Check if venv exists
IF NOT EXIST "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo ERROR: Python not found or virtual environment failed.
        echo Make sure Python 3.11 is installed from https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade requirements
echo Installing requirements...
pip install -r requirements.txt --quiet

REM Launch app
echo.
echo Starting NGN NCLEX Simulator...
echo Open your browser to: http://localhost:8501
echo Press Ctrl+C to stop.
echo.
streamlit run app.py

pause

@echo off
echo ====================================
echo AZ Gov Job Scraper - Setup Script
echo ====================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/4] Installing Playwright browsers...
playwright install
if errorlevel 1 (
    echo ERROR: Failed to install Playwright browsers
    pause
    exit /b 1
)

echo.
echo ====================================
echo Setup complete!
echo ====================================
echo.
echo Next steps:
echo 1. Copy .env.example to .env
echo 2. Add your GEMINI_API_KEY to .env
echo 3. Run: streamlit run streamlit_app.py
echo.
pause

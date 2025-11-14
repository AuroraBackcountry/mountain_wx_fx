@echo off
REM Setup script for Mountain Weather Forecast System (Windows)

echo Setting up Mountain Weather Forecast System...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo To activate the environment in the future, run:
echo   venv\Scripts\activate
echo.
echo To run the weather forecast system:
echo   python main.py
echo.
echo To deactivate the environment when done:
echo   deactivate

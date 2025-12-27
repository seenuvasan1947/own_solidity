@echo off
REM Quick installation script for SolScan on Windows

echo ========================================
echo SolScan Installation Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Python found
python --version

echo.
echo [2/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/4] Installing SolScan package...
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install SolScan package
    pause
    exit /b 1
)

echo.
echo [4/4] Verifying installation...
solscan --version
if errorlevel 1 (
    echo ERROR: SolScan command not found
    echo Try closing and reopening your terminal
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo You can now use SolScan with:
echo   solscan -i your_contract.sol
echo   solscan --help
echo.
echo For more information, see INSTALLATION_GUIDE.md
echo.
pause

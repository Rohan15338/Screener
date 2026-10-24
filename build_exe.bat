@echo off
echo ==============================================
echo  Building Standalone Screener.exe with PyInstaller
echo ==============================================

pyinstaller --noconsole --onefile --icon=screener.ico --name "Screener" --add-data "screener.ico;." run.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Screener.exe built successfully in dist\Screener.exe!
) else (
    echo.
    echo [ERROR] Build failed.
)
pause

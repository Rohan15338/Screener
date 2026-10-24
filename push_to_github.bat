@echo off
echo Pushing Screener to GitHub (https://github.com/Rohan15338/Screener.git)...
git push -u origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Successfully pushed to GitHub!
) else (
    echo.
    echo [NOTE] If this is the first time, ensure you have created the empty 'Screener' repository at https://github.com/new
)
pause

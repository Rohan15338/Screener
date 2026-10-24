@echo off
echo Stopping Screener background processes...
taskkill /F /FI "WINDOWTITLE eq Screener*" /T >nul 2>&1
wmic process where "CommandLine like '%%run.py%%'" call terminate >nul 2>&1
echo Done! Screener stopped.
timeout /t 2 >nul

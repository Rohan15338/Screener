@echo off
echo Creating Desktop and Start Menu shortcuts for Screener...

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$exePath = (Join-Path (Get-Location) 'dist\Screener.exe'); " ^
  "$iconPath = (Join-Path (Get-Location) 'screener.ico'); " ^
  "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$startMenu = [Environment]::GetFolderPath('Programs'); " ^
  "$scDesktop = $ws.CreateShortcut((Join-Path $desktop 'Screener.lnk')); " ^
  "$scDesktop.TargetPath = $exePath; " ^
  "$scDesktop.IconLocation = $iconPath; " ^
  "$scDesktop.Description = 'Screener - Active Screen Time Tracker & Break Reminder'; " ^
  "$scDesktop.Save(); " ^
  "$scStart = $ws.CreateShortcut((Join-Path $startMenu 'Screener.lnk')); " ^
  "$scStart.TargetPath = $exePath; " ^
  "$scStart.IconLocation = $iconPath; " ^
  "$scStart.Description = 'Screener - Active Screen Time Tracker & Break Reminder'; " ^
  "$scStart.Save(); " ^
  "Write-Host '[OK] Shortcuts created successfully on Desktop and Start Menu!'"

timeout /t 3 >nul

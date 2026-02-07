@echo off
echo ===============================================================================
echo   LAUNCHING EDGE FOR TEST GEN AI
echo ===============================================================================
echo.
echo 1. Closing any existing Edge processes...
taskkill /IM msedge.exe /F >nul 2>&1
echo.
echo 2. Launching Edge with Remote Debugging (Port 9222)...
echo.
echo   NOTE: Please log in to Copilot (Microsoft account) and bypass any Captchas manually.
echo   Once the chat is ready, return to the GUI and click "Generate".
echo.

start msedge.exe --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Microsoft\Edge\User Data" "https://copilot.microsoft.com"

echo Done. Edge is running in debug mode.
pause

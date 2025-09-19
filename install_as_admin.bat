@echo off
echo Installing Permanent Delete Context Menu...
echo This requires administrator privileges.
echo.

cd /d "%~dp0"
powershell -Command "Start-Process python -ArgumentList 'install_context_menu.py' -Verb RunAs -Wait"

echo.
echo Installation complete. Press any key to exit.
pause

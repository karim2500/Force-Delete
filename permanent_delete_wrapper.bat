@echo off
setlocal
cd /d "%~dp0"

rem Write a quick log to help debug context menu execution
set LOGDIR=%LOCALAPPDATA%\PermanentDeleter
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1
echo [%date% %time%] Args: %* >> "%LOGDIR%\wrapper.log"

rem Use system python explicitly if available, otherwise fallback to file association
set PY=%LocalAppData%\Microsoft\WindowsApps\python.exe
if exist "%PY%" (
    "%PY%" "Test deleted.py" %*
    exit /b %errorlevel%
) else (
    python "Test deleted.py" %*
    exit /b %errorlevel%
)

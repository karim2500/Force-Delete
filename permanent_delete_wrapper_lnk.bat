@echo off
setlocal
cd /d "%~dp0"

set LOGDIR=%LOCALAPPDATA%\PermanentDeleter
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1

echo [%date% %time%] LNK Args: %* >> "%LOGDIR%\wrapper.log"

set LNK=%~1

rem Resolve target of .lnk via powershell COM
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); Write-Output $s.TargetPath"`) do set TARGET=%%T

if not defined TARGET set TARGET=%LNK%

echo [%date% %time%] Resolved: %TARGET% >> "%LOGDIR%\wrapper.log"

set PY=%LocalAppData%\Microsoft\WindowsApps\python.exe
if exist "%PY%" (
    "%PY%" "Test deleted.py" "%TARGET%"
    exit /b %errorlevel%
) else (
    python "Test deleted.py" "%TARGET%"
    exit /b %errorlevel%
)

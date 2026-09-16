@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "start_server.py" %*
    goto :finished
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "start_server.py" %*
    goto :finished
)

where python >nul 2>nul
if not errorlevel 1 (
    python "start_server.py" %*
    goto :finished
)

echo Python 3 nao encontrado. Instale em https://www.python.org/downloads/
pause
exit /b 1

:finished
set "SITE_EXIT_CODE=%errorlevel%"
if not "%SITE_EXIT_CODE%"=="0" (
    echo.
    echo O servidor encerrou com erro. Confira a mensagem acima.
    pause
)
exit /b %SITE_EXIT_CODE%

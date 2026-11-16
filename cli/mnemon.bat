@echo off
setlocal
if defined PYTHON (
    "%PYTHON%" "%~dp0mnemon" %*
    exit /b %ERRORLEVEL%
)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3 "%~dp0mnemon" %*
    exit /b %ERRORLEVEL%
)
python "%~dp0mnemon" %*
exit /b %ERRORLEVEL%

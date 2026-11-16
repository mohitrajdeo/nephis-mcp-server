@echo off
setlocal
if defined PYTHON (
    "%PYTHON%" "%~dp0thanaton" %*
    exit /b %ERRORLEVEL%
)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3 "%~dp0thanaton" %*
    exit /b %ERRORLEVEL%
)
python "%~dp0thanaton" %*
exit /b %ERRORLEVEL%

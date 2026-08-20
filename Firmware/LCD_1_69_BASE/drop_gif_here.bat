@echo off
title Rollopod GIF to Arduino Code Generator
cls
echo ========================================================
echo    ROLLOPOD 1.69" LCD GIF-to-Arduino Code Generator
echo ========================================================
echo.
if "%~1"=="" (
    echo [INFO] Looking for GIF files in this folder...
    python "%~dp0generate_gif_code.py"
) else (
    echo [INFO] Converting dropped file: "%~1"
    python "%~dp0generate_gif_code.py" "%~1"
)
echo.
echo ========================================================
echo Press any key to exit...
pause >nul

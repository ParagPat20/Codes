@echo off
title ESP32-C6 ESP-NOW Tracer UI (100Hz)
echo Starting ESP32-C6 Packet Loss & RSSI Real-Time UI...
.venv\Scripts\python.exe tracer_ui.py
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause > nul
)

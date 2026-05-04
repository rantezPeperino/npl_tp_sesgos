@echo off
REM kill_ports.bat - Kill processes on specified ports (Windows)
REM Usage: kill_ports.bat [port1 port2 ...]
REM Default ports: 5173-5177 (frontend), 8000-8001 (backend)

setlocal enabledelayedexpansion

REM Parse arguments or use defaults
set "ports=5173 5174 5175 5176 5177 8000 8001"
if not "%~1"=="" (
  set "ports=%*"
)

echo [kill_ports] Terminando procesos en puertos: %ports%

for %%P in (%ports%) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P "') do (
    echo [kill_ports] Matando proceso %%A en puerto %%P
    taskkill /PID %%A /F >nul 2>&1
  )
)

echo [kill_ports] Listo.

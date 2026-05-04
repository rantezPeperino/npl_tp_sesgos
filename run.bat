@echo off
REM run.bat - unified entrypoint for tiltDetector on Windows
REM Allows running backend only, frontend only, or both in parallel

setlocal enabledelayedexpansion

REM ---- Configuration ----
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR:~0,-1%"
set "BACKEND_DIR=%ROOT_DIR%\app"
set "FRONTEND_DIR=%ROOT_DIR%\frontend"
set "REQUIREMENTS_FILE=%BACKEND_DIR%\requirements.txt"
set "VENV_DIR=%ROOT_DIR%\.venv"
set "BACKEND_HOST=0.0.0.0"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"

if not "%BACKEND_HOST%"=="" goto skip_env_backend_host
set "BACKEND_HOST=0.0.0.0"
:skip_env_backend_host

if not "%BACKEND_PORT%"=="" goto skip_env_backend_port
set "BACKEND_PORT=8000"
:skip_env_backend_port

if not "%FRONTEND_PORT%"=="" goto skip_env_frontend_port
set "FRONTEND_PORT=5173"
:skip_env_frontend_port

REM ---- Helpers ----
:log
echo [run] %*
exit /b

:ok
echo [ok] %*
exit /b

:warn
echo [WARN] %*
exit /b

:err
echo [ERR] %* 1>&2
exit /b

REM ---- Setup ----
:ensure_backend_ready
if exist "%VENV_DIR%" goto skip_venv_create
echo [run] Creando virtualenv en .venv ...
python -m venv "%VENV_DIR%"
if errorlevel 1 (
  echo [ERR] No se pudo crear virtualenv. Verifica que Python esté instalado y en PATH.
  exit /b 1
)

:skip_venv_create
if exist "%VENV_DIR%\Scripts\pip.exe" goto skip_pip_install
echo [run] Instalando dependencias del backend (requirements.txt) ...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >nul
"%VENV_DIR%\Scripts\pip.exe" install -r "%REQUIREMENTS_FILE%"
if errorlevel 1 (
  echo [ERR] No se pudieron instalar dependencias.
  exit /b 1
)
goto after_pip_install

:skip_pip_install
"%VENV_DIR%\Scripts\python.exe" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
  echo [run] Sincronizando dependencias del backend ...
  "%VENV_DIR%\Scripts\pip.exe" install -r "%REQUIREMENTS_FILE%"
)

:after_pip_install
exit /b 0

:ensure_frontend_ready
if not exist "%FRONTEND_DIR%" (
  echo [ERR] No existe %FRONTEND_DIR%
  exit /b 1
)
if exist "%FRONTEND_DIR%\node_modules" goto skip_npm_install
echo [run] Instalando dependencias del frontend (npm install) ...
cd /d "%FRONTEND_DIR%"
call npm install
if errorlevel 1 (
  echo [ERR] npm install fallo.
  exit /b 1
)
:skip_npm_install
exit /b 0

REM ---- Runners ----
:run_backend_foreground
call :ensure_backend_ready
if errorlevel 1 exit /b 1
echo [ok] Backend en http://%BACKEND_HOST%:%BACKEND_PORT% (Presiona Ctrl+C para detener)
cd /d "%ROOT_DIR%"
"%VENV_DIR%\Scripts\uvicorn.exe" app.main:app --reload --host %BACKEND_HOST% --port %BACKEND_PORT%
exit /b

:run_frontend_foreground
call :ensure_frontend_ready
if errorlevel 1 exit /b 1
echo [ok] Frontend en http://localhost:%FRONTEND_PORT% (Presiona Ctrl+C para detener)
cd /d "%FRONTEND_DIR%"
call npm run dev -- --port %FRONTEND_PORT%
exit /b

:run_both
call :ensure_backend_ready
if errorlevel 1 exit /b 1
call :ensure_frontend_ready
if errorlevel 1 exit /b 1

echo [run] Levantando backend en :%BACKEND_PORT% + frontend en :%FRONTEND_PORT%
echo.
echo ---- logs combinados ----

REM Lanzar backend en background
start "tiltDetector-backend" "%VENV_DIR%\Scripts\uvicorn.exe" app.main:app --reload --host %BACKEND_HOST% --port %BACKEND_PORT%

REM Lanzar frontend en background
start "tiltDetector-frontend" cmd /k "cd /d %FRONTEND_DIR% && npm run dev -- --port %FRONTEND_PORT%"

REM Esperar a que el frontend esté listo y abrir navegador
timeout /t 5 /nobreak
start http://localhost:%FRONTEND_PORT%
echo [ok] Browser abierto en http://localhost:%FRONTEND_PORT%

echo.
echo Presiona cualquier tecla para detener los servidores...
pause >nul

REM Detener procesos
taskkill /FI "WINDOWTITLE eq tiltDetector-backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq tiltDetector-frontend*" /T /F >nul 2>&1
taskkill /PORT:%BACKEND_PORT% /T /F >nul 2>&1
taskkill /PORT:%FRONTEND_PORT% /T /F >nul 2>&1

echo [ok] Servidores detenidos.
exit /b 0

REM ---- Menu ----
:print_header
echo.
echo ========================================
echo.
echo tiltDetector - runner
echo backend:  %BACKEND_DIR% (puerto %BACKEND_PORT%)
echo frontend: %FRONTEND_DIR% (puerto %FRONTEND_PORT%)
echo.
echo ========================================
echo.
exit /b 0

:choose_action
echo.
echo Que queres correr?
echo   1^) Solo backend
echo   2^) Solo frontend
echo   3^) Ambos (backend + frontend en paralelo)
echo   q^) Salir
echo.
set /p choice="Elegí [1/2/3/q]: "
echo.

if /i "%choice%"=="1" goto choice_backend
if /i "%choice%"=="b" goto choice_backend
if /i "%choice%"=="backend" goto choice_backend
if /i "%choice%"=="be" goto choice_backend
if /i "%choice%"=="2" goto choice_frontend
if /i "%choice%"=="f" goto choice_frontend
if /i "%choice%"=="frontend" goto choice_frontend
if /i "%choice%"=="fe" goto choice_frontend
if /i "%choice%"=="3" goto choice_both
if /i "%choice%"=="a" goto choice_both
if /i "%choice%"=="both" goto choice_both
if /i "%choice%"=="ambos" goto choice_both
if /i "%choice%"=="q" (
  echo [run] Cancelado.
  exit /b 0
)
if "%choice%"=="" (
  echo [run] Cancelado.
  exit /b 0
)

echo [ERR] Opcion invalida: '%choice%'
exit /b 1

:choice_backend
call :run_backend_foreground
exit /b

:choice_frontend
call :run_frontend_foreground
exit /b

:choice_both
call :run_both
exit /b

REM ---- Main ----
call :print_header

if "%~1"=="" (
  call :choose_action
  exit /b %errorlevel%
)

if /i "%~1"=="backend" call :run_backend_foreground && exit /b %errorlevel%
if /i "%~1"=="back" call :run_backend_foreground && exit /b %errorlevel%
if /i "%~1"=="be" call :run_backend_foreground && exit /b %errorlevel%
if /i "%~1"=="1" call :run_backend_foreground && exit /b %errorlevel%

if /i "%~1"=="frontend" call :run_frontend_foreground && exit /b %errorlevel%
if /i "%~1"=="front" call :run_frontend_foreground && exit /b %errorlevel%
if /i "%~1"=="fe" call :run_frontend_foreground && exit /b %errorlevel%
if /i "%~1"=="2" call :run_frontend_foreground && exit /b %errorlevel%

if /i "%~1"=="both" call :run_both && exit /b %errorlevel%
if /i "%~1"=="all" call :run_both && exit /b %errorlevel%
if /i "%~1"=="ambos" call :run_both && exit /b %errorlevel%
if /i "%~1"=="3" call :run_both && exit /b %errorlevel%

if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
if /i "%~1"=="help" goto show_help

echo [ERR] Argumento desconocido: '%~1'. Usa: run.bat --help
exit /b 1

:show_help
echo.
echo Uso: run.bat [backend^|frontend^|both]
echo.
echo Sin argumentos abre un menu interactivo.
echo.
echo Variables de entorno opcionales:
echo   BACKEND_HOST   (default: 0.0.0.0)
echo   BACKEND_PORT   (default: 8000)
echo   FRONTEND_PORT  (default: 5173)
echo.
exit /b 0

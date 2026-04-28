#!/usr/bin/env bash
# run.sh — entrypoint unificado para tiltDetector.
# Permite levantar solo backend, solo frontend, o ambos en paralelo.

set -euo pipefail

# ---- Configuración ----
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/app"
FRONTEND_DIR="$ROOT_DIR/frontend"
REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"
VENV_DIR="$ROOT_DIR/.venv"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# ---- Colores (auto-disable si no es TTY) ----
if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_BLUE=$'\033[34m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_RED=$'\033[31m'
  C_DIM=$'\033[2m'
else
  C_RESET=""; C_BOLD=""; C_BLUE=""; C_GREEN=""; C_YELLOW=""; C_RED=""; C_DIM=""
fi

log()   { echo "${C_BLUE}[run]${C_RESET} $*"; }
ok()    { echo "${C_GREEN}[ok]${C_RESET}  $*"; }
warn()  { echo "${C_YELLOW}[warn]${C_RESET} $*"; }
err()   { echo "${C_RED}[err]${C_RESET} $*" >&2; }

# ---- Helpers de setup ----
ensure_backend_ready() {
  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creando virtualenv en .venv …"
    python3 -m venv "$VENV_DIR"
  fi
  if [[ ! -f "$VENV_DIR/bin/uvicorn" ]] || [[ ! -f "$VENV_DIR/bin/python" ]]; then
    log "Instalando dependencias del backend (requirements.txt) …"
    "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
    "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
  else
    if ! "$VENV_DIR/bin/python" -c "import fastapi" 2>/dev/null; then
      log "Sincronizando dependencias del backend …"
      "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
    fi
  fi
}

ensure_frontend_ready() {
  if [[ ! -d "$FRONTEND_DIR" ]]; then
    err "No existe $FRONTEND_DIR"
    exit 1
  fi
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    log "Instalando dependencias del frontend (npm install) …"
    (cd "$FRONTEND_DIR" && npm install)
  fi
}

# ---- Runners ----
run_backend_foreground() {
  ensure_backend_ready
  ok "Backend en http://${BACKEND_HOST}:${BACKEND_PORT}  (Ctrl+C para detener)"
  cd "$ROOT_DIR"
  exec "$VENV_DIR/bin/uvicorn" app.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT"
}

run_frontend_foreground() {
  ensure_frontend_ready
  ok "Frontend en http://localhost:${FRONTEND_PORT}  (Ctrl+C para detener)"
  cd "$FRONTEND_DIR"
  exec npm run dev -- --port "$FRONTEND_PORT"
}

run_both() {
  ensure_backend_ready
  ensure_frontend_ready

  log "Levantando backend en :$BACKEND_PORT  +  frontend en :$FRONTEND_PORT"
  echo "${C_DIM}─ logs combinados ─────────────────────────────────────────${C_RESET}"

  # Lanzar backend en background
  (
    cd "$ROOT_DIR"
    "$VENV_DIR/bin/uvicorn" app.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT" 2>&1 \
      | sed -u "s/^/${C_BLUE}[backend]${C_RESET} /"
  ) &
  BACK_PID=$!

  # Lanzar frontend en background
  (
    cd "$FRONTEND_DIR"
    npm run dev -- --port "$FRONTEND_PORT" 2>&1 \
      | sed -u "s/^/${C_GREEN}[frontend]${C_RESET} /"
  ) &
  FRONT_PID=$!

  cleanup() {
    log "Deteniendo procesos…"
    kill "$BACK_PID" 2>/dev/null || true
    kill "$FRONT_PID" 2>/dev/null || true
    wait "$BACK_PID" 2>/dev/null || true
    wait "$FRONT_PID" 2>/dev/null || true
    ok "Listo."
  }
  trap cleanup INT TERM EXIT

  wait -n "$BACK_PID" "$FRONT_PID" || true
  cleanup
}

# ---- Menú ----
print_header() {
  cat <<EOF
${C_BOLD}tiltDetector — runner${C_RESET}
${C_DIM}backend:  $BACKEND_DIR  (puerto $BACKEND_PORT)
frontend: $FRONTEND_DIR  (puerto $FRONTEND_PORT)${C_RESET}
EOF
}

choose_action() {
  echo ""
  echo "${C_BOLD}¿Qué querés correr?${C_RESET}"
  echo "  1) Solo backend"
  echo "  2) Solo frontend"
  echo "  3) Ambos (backend + frontend en paralelo)"
  echo "  q) Salir"
  echo ""
  read -r -p "Elegí [1/2/3/q]: " choice
  echo ""
  case "${choice:-}" in
    1|b|backend) run_backend_foreground ;;
    2|f|frontend) run_frontend_foreground ;;
    3|a|both|ambos) run_both ;;
    q|Q|"") log "Cancelado."; exit 0 ;;
    *) err "Opción inválida: '$choice'"; exit 1 ;;
  esac
}

# ---- Modo no interactivo (argumento explícito) ----
if [[ $# -gt 0 ]]; then
  print_header
  case "$1" in
    backend|back|be|1) run_backend_foreground ;;
    frontend|front|fe|2) run_frontend_foreground ;;
    both|all|ambos|3) run_both ;;
    -h|--help|help)
      cat <<EOF
Uso: ./run.sh [backend|frontend|both]

Sin argumentos abre un menú interactivo.

Variables de entorno opcionales:
  BACKEND_HOST   (default: 0.0.0.0)
  BACKEND_PORT   (default: 8000)
  FRONTEND_PORT  (default: 5173)
EOF
      ;;
    *) err "Argumento desconocido: '$1'. Usá: ./run.sh --help"; exit 1 ;;
  esac
else
  print_header
  choose_action
fi

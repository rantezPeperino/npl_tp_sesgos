#!/usr/bin/env bash
# kill_ports.sh — mata todos los procesos que usen puertos específicos

set -euo pipefail

# Puertos por defecto a limpiar
PORTS="${1:-5173 5174 5175 5176 5177 8000 8001}"

echo "Matando procesos en puertos: $PORTS"

for PORT in $PORTS; do
  PIDS=$(lsof -ti:$PORT 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    echo "Puerto $PORT: matando PIDs $PIDS"
    echo "$PIDS" | xargs kill -9 2>/dev/null || true
  else
    echo "Puerto $PORT: libre"
  fi
done

sleep 1
echo "Hecho. Puertos liberados."

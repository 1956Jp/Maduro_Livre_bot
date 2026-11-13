#!/usr/bin/env bash
# Repara Lex cuando se cuelga (runner de Ollama atascado).
# Uso: ./reparar_ollama.sh
set -u
MODELO="gemma4:e2b"
URL="http://localhost:11434/v1/chat/completions"

echo "[1/3] Descargando el modelo atascado..."
ollama stop "$MODELO" 2>/dev/null && sleep 2

echo "[2/3] Probando generacion (puede tardar ~50 s en la 1a peticion)..."
if curl -sS --max-time 150 -o /dev/null -w "%{http_code}" "$URL" \
     -H "Content-Type: application/json" \
     -d "{\"model\":\"$MODELO\",\"messages\":[{\"role\":\"user\",\"content\":\"Di OK\"}]}" \
     | grep -q 200; then
  echo "[3/3] Ollama responde: REPARADO. Arranca de nuevo el bot."
else
  echo "[3/3] Sigue colgado. Ejecuta: sudo systemctl restart ollama"
  echo "      y vuelve a correr este script."
fi

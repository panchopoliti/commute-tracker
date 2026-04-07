#!/bin/bash
#
# setup_cron.sh - Configura/elimina el cron job para commute_tracker.py
#
# Uso:
#   ./setup_cron.sh start   - Instala el cron (cada 10 min)
#   ./setup_cron.sh stop    - Elimina el cron
#   ./setup_cron.sh status  - Muestra si está activo
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TRACKER_SCRIPT="$SCRIPT_DIR/commute_tracker.py"
LOG_FILE="$SCRIPT_DIR/commute_tracker.log"
CRON_MARKER="# commute-tracker"

# Usar Python del venv si existe, sino el del sistema
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
if [ -x "$VENV_PYTHON" ]; then
    PYTHON_BIN="$VENV_PYTHON"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="$(command -v python3)"
else
    echo "ERROR: python3 no encontrado. Creá el venv primero:"
    echo "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Verificar que la API key esté configurada
if [ -z "${GOOGLE_MAPS_API_KEY:-}" ]; then
    echo "WARNING: GOOGLE_MAPS_API_KEY no está configurada en el entorno actual."
    echo "El cron necesita la API key. Agregala a tu ~/.zshrc o ~/.bash_profile:"
    echo ""
    echo "  export GOOGLE_MAPS_API_KEY='tu-api-key-aquí'"
    echo ""
    read -p "¿Querés continuar igual? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

install_cron() {
    # Remover entrada anterior si existe
    remove_cron 2>/dev/null || true

    # La línea de cron: cada 10 minutos, con la API key
    CRON_LINE="*/10 * * * * GOOGLE_MAPS_API_KEY='${GOOGLE_MAPS_API_KEY:-TU_API_KEY_AQUI}' $PYTHON_BIN $TRACKER_SCRIPT ambas >> $LOG_FILE 2>&1 $CRON_MARKER"

    # Agregar al crontab
    (crontab -l 2>/dev/null || true; echo "$CRON_LINE") | crontab -

    echo "✅ Cron instalado: cada 10 minutos"
    echo "   Python:  $PYTHON_BIN"
    echo "   Script:  $TRACKER_SCRIPT"
    echo "   Log:     $LOG_FILE"
    echo ""
    echo "Para ver los logs en tiempo real:"
    echo "   tail -f $LOG_FILE"
}

remove_cron() {
    crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | crontab -
    echo "🛑 Cron eliminado"
}

show_status() {
    if crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
        echo "✅ Cron ACTIVO:"
        crontab -l | grep "$CRON_MARKER"
    else
        echo "❌ Cron NO activo"
    fi
}

case "${1:-}" in
    start)
        install_cron
        ;;
    stop)
        remove_cron
        ;;
    status)
        show_status
        ;;
    *)
        echo "Uso: $0 {start|stop|status}"
        exit 1
        ;;
esac

#!/bin/bash
set -e

echo "Esperando a que la base de datos esté lista..."
# Espera simple para dar tiempo a Postgres a arrancar
sleep 10

echo "Iniciando proceso de poblado para nivel: $NIVEL_POBLADO"

case "$NIVEL_POBLADO" in
    "leve")
        python scripts/poblar_leve.py
        ;;
    "moderado")
        python scripts/poblar_moderado.py
        ;;
    "masivo")
        python scripts/poblar_masivo.py
        ;;
    *)
        echo "Nivel '$NIVEL_POBLADO' no reconocido. Ejecutando nivel LEVE por defecto."
        python scripts/poblar_leve.py
        ;;
esac

echo "Proceso finalizado."
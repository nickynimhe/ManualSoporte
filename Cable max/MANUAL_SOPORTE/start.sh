#!/bin/bash

# Ejecuta el script de inicialización de la base de datos
echo "Inicializando la base de datos..."
python database.py

# Inicia la aplicación con Gunicorn
echo "Iniciando Gunicorn..."
gunicorn --bind 0.0.0.0:5000 app:app
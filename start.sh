#!/bin/bash

# Ejecuta el script de inicialización de la base de datos
#!/bin/bash
echo "🚀 Iniciando la aplicación Flask..."
python app.py

# Inicia la aplicación con Gunicorn
echo "Iniciando Gunicorn..."
gunicorn --bind 0.0.0.0:5000 app:app

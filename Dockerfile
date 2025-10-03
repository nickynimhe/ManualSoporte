FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hacer el script de inicio ejecutable
RUN chmod +x start.sh

EXPOSE 5000

# Usar el script de inicio para inicializar la DB y luego correr la app
CMD ["./start.sh"]
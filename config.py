import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-muy-segura-aqui-123'
    
    # Configuración para PostgreSQL (Render)
    DB_HOST = os.environ.get('DB_HOST') or 'dpg-d3g1q2nqaa0ldt0j7vug-a.oregon-postgres.render.com'
    DB_NAME = os.environ.get('DB_NAME') or 'soporte_tecnico_9sad'
    DB_USER = os.environ.get('DB_USER') or 'soporte_tecnico_9sad_user'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'T56GYS30j5w4k6zrdlvAh1GfExjT0t7a'
    DB_PORT = os.environ.get('DB_PORT') or '5432'
    
    # URL completa de conexión para PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://soporte_tecnico_9sad_user:T56GYS3Oj5w4kGzrdlvAhlGfExjT0t7a@dpg-d3g1q2nfte5s73cjpiu0-a/soporte_tecnico_9sad'

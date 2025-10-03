import os

class Config:
    # Es recomendable definir un valor por defecto solo para desarrollo local
    SECRET_KEY = os.environ.get('SECRET_KEY', 'reemplaza-esto-por-un-valor-seguro-en-produccion')
    
    # Configuración para PostgreSQL (Render)
    DB_HOST = os.environ.get('DB_HOST', 'dpg-d3g1q2nqaa0ldt0j7vug-a.oregon-postgres.render.com')
    DB_NAME = os.environ.get('DB_NAME', 'soporte_tecnico_9sad')
    DB_USER = os.environ.get('DB_USER', 'soporte_tecnico_9sad_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'pon-una-contraseña-segura-o-usar-env')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    
    # URL completa de conexión para PostgreSQL
    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )

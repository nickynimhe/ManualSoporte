import os

class Config:
    # Clave secreta para sesiones Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-super-secreta-para-desarrollo'
    
    # Configuración adicional
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
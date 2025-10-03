import os

class Config:
    # Clave secreta para sesiones Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-super-secreta-para-desarrollo'
    
    # Configuración de MySQL
    MYSQL_HOST = os.environ.get('dpg-d3g1q2nfte5s73cjpiu0-a') or 'dpg-d3g1q2nfte5s73cjpiu0-a'
    MYSQL_USER = os.environ.get('soporte_tecnico_9sad_user') or 'soporte_tecnico_9sad_user'
    MYSQL_PASSWORD = os.environ.get('T56GYS3Oj5w4kGzrdlvAhlGfExjT0t7a') or 'T56GYS3Oj5w4kGzrdlvAhlGfExjT0t7a'
    MYSQL_DB = os.environ.get('soporte_tecnico_9sad') or 'soporte_tecnico_9sad'
    
    # Configuración adicional
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

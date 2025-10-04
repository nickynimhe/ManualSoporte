import os
import psycopg2
from werkzeug.security import generate_password_hash
import json
import time

def crear_conexion():
    """Usa EXACTAMENTE la misma lógica que get_db() de Flask"""
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            print(f"🔗 Intento {intento + 1} de conexión a PostgreSQL...")
            
            # CÓDIGO CORREGIDO - usar nombres de variables de entorno, no valores
            database_url = os.getenv('DATABASE_URL')
            sslmode_require = os.getenv('SSL_MODE', '') == 'require'

            if not database_url:
                # Configuración local - usar nombres CORRECTOS de variables de entorno
                user = os.getenv('DB_USER', 'soporte_tecnico_9sad_user')
                password = os.getenv('DB_PASSWORD', 'T56GYS30j5w4k6zrdlvAh1GfExjT0t7a')
                host = os.getenv('DB_HOST', 'dpg-d3g1q2nqaa0ldt0j7vug-a.oregon-postgres.render.com')
                port = os.getenv('DB_PORT', '5432')
                dbname = os.getenv('DB_NAME', 'soporte_tecnico_9sad')
                
                print(f"🔧 Configuración local - Host: {host}, DB: {dbname}, User: {user}")
                
                # Codifica la contraseña por si tiene caracteres especiales
                password_encoded = quote_plus(password)
                database_url = f"postgresql://{user}:{password_encoded}@{host}:{port}/{dbname}"
            else:
                print("🔧 Usando DATABASE_URL de variable de entorno")
                if database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql://", 1)
            
            # Agrega sslmode=require al URI si es necesario
            if sslmode_require and 'sslmode=' not in database_url:
                separator = '?' if '?' not in database_url else '&'
                database_url += f"{separator}sslmode=require"

            print(f"🔗 URL de conexión: {database_url.split('@')[0]}@***")  # Oculta credenciales en logs

            # Conexión SOLO con el URI (igual que en Flask)
            conexion = psycopg2.connect(database_url)
            
            print("✅ ¡CONEXIÓN EXITOSA a PostgreSQL!")
            return conexion
            
        except Exception as err:
            print(f"❌ Intento {intento + 1} falló: {err}")
            if intento < max_intentos - 1:
                print("🔄 Reintentando en 3 segundos...")
                time.sleep(3)
            else:
                print("💥 Todos los intentos de conexión fallaron")
                return None

# El resto del código se mantiene igual...
def crear_tablas():
    print("🔧 Iniciando creación de tablas...")
    conexion = crear_conexion()
    if not conexion:
        print("💥 No se pudo conectar para crear tablas")
        return False

    cursor = conexion.cursor()
    try:
        # Tabla usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                rol VARCHAR(50) NOT NULL DEFAULT 'asesor',
                permisos JSONB,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla 'usuarios' lista")

        # Tabla fichas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fichas (
                id SERIAL PRIMARY KEY,
                categoria VARCHAR(50) NOT NULL DEFAULT 'Equipo',
                problema VARCHAR(255) NOT NULL,
                descripcion TEXT,
                causas TEXT,
                solucion TEXT,
                palabras_clave TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla 'fichas' lista")

        # Insertar usuarios si no existen
        usuarios_data = [
            ('admin', generate_password_hash('admin123'), 'admin'),
            ('asesor', generate_password_hash('asesor123'), 'asesor')
        ]
        
        for usuario, password, rol in usuarios_data:
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = %s", (usuario,))
            if cursor.fetchone()[0] == 0:
                permisos = json.dumps({
                    'ver_fichas': True, 
                    'agregar_fichas': rol == 'admin',
                    'editar_fichas': rol == 'admin', 
                    'eliminar_fichas': rol == 'admin',
                    'cambiar_password': True
                })
                cursor.execute(
                    "INSERT INTO usuarios (usuario, password, rol, permisos) VALUES (%s, %s, %s, %s)",
                    (usuario, password, rol, permisos)
                )
                print(f"✅ Usuario '{usuario}' creado")

        conexion.commit()
        print("🎉 Base de datos inicializada CORRECTAMENTE")
        return True

    except Exception as err:
        print(f"💥 Error en creación de tablas: {err}")
        conexion.rollback()
        return False
    finally:
        cursor.close()
        conexion.close()

if __name__ == "__main__":
    print("🔧 Ejecutando inicialización de base de datos...")
    crear_tablas()

import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from config import Config
import os
import json

def crear_conexion():
    """
    Crea y retorna una conexión a la base de datos PostgreSQL usando la URL de Render.
    """
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            raise RuntimeError("La variable de entorno DATABASE_URL no está configurada.")
        
        # Render usa URLs de DB que pueden empezar con 'postgres://' en lugar de 'postgresql://'
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        conexion = psycopg2.connect(db_url)
        return conexion
    except psycopg2.Error as e:
        print(f"❌ Error al conectar a PostgreSQL: {e}")
        return None

def crear_tablas():
    """
    Crea las tablas necesarias en la base de datos PostgreSQL si no existen.
    """
    conexion = crear_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()

            # Crear tabla usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    usuario VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    rol VARCHAR(50) NOT NULL,
                    permisos TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ Tabla 'usuarios' creada o ya existente.")

            # Crear tabla fichas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fichas (
                    id SERIAL PRIMARY KEY,
                    categoria VARCHAR(50) NOT NULL,
                    problema VARCHAR(255) NOT NULL,
                    descripcion TEXT,
                    causas TEXT,
                    solucion TEXT,
                    palabras_clave TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ Tabla 'fichas' creada o ya existente.")

            # Insertar usuarios por defecto si no existen
            admin_pass = generate_password_hash('admin123')
            asesor_pass = generate_password_hash('asesor123')
            default_perms = json.dumps({
                'ver_fichas': True, 'agregar_fichas': False, 'editar_fichas': False,
                'eliminar_fichas': False, 'cambiar_password': True
            })

            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO usuarios (usuario, password, rol, permisos) VALUES (%s, %s, %s, %s)",
                    ('admin', admin_pass, 'admin', default_perms)
                )
                print("✅ Usuario 'admin' creado.")

            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'asesor'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO usuarios (usuario, password, rol, permisos) VALUES (%s, %s, %s, %s)",
                    ('asesor', asesor_pass, 'asesor', default_perms)
                )
                print("✅ Usuario 'asesor' creado.")

            conexion.commit()
            print("🎉 Base de datos inicializada correctamente.")

        except psycopg2.Error as e:
            print(f"❌ Error al crear tablas: {e}")
            conexion.rollback()
        finally:
            cursor.close()
            conexion.close()

if __name__ == "__main__":
    print("🔧 Inicializando base de datos...")
    crear_tablas()
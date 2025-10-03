import psycopg2
from werkzeug.security import generate_password_hash
import os
import json
import urllib.parse

def crear_conexion():
    try:
        # Opción 1: Usar DATABASE_URL de Render (RECOMENDADO)
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            print("🔗 Intentando conexión via DATABASE_URL...")
            # Parsear la URL de la base de datos
            url = urllib.parse.urlparse(database_url)
            
            conexion = psycopg2.connect(
                database=url.path[1:],  # Remover el '/' inicial
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port,
                sslmode='require'  # Requerido para Render PostgreSQL
            )
            print("✅ Conexión a PostgreSQL exitosa via DATABASE_URL")
            return conexion
        
        # Opción 2: Usar variables individuales
        print("🔗 Intentando conexión via parámetros individuales...")
        user = 'soporte_tecnico_9sad_user'
        password = 'T56GYS30j5w4k6zrdlvAh1GfExjT0t7a'
        host = 'dpg-d3g1q2nqaa0ldt0j7vug-a.oregon-postgres.render.com'
        database = 'soporte_tecnico_9sad'
        port = '5432'

        conexion = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            sslmode='require'
        )
        print("✅ Conexión a PostgreSQL exitosa via parámetros individuales")
        return conexion
        
    except Exception as err:
        print(f"❌ Error al conectar a PostgreSQL: {err}")
        return None

def crear_tablas():
    conexion = crear_conexion()
    if not conexion:
        print("❌ No se pudo conectar a la base de datos para crear las tablas.")
        return False

    cursor = conexion.cursor()

    try:
        # Crear tabla usuarios (sintaxis PostgreSQL)
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
        print("✅ Tabla 'usuarios' creada o ya existente.")

        # Crear tabla fichas (sintaxis PostgreSQL)
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
        print("✅ Tabla 'fichas' creada o ya existente.")

        # Insertar usuarios por defecto si no existen
        admin_pass = generate_password_hash('admin123')
        asesor_pass = generate_password_hash('asesor123')
        default_perms = json.dumps({
            'ver_fichas': True, 
            'agregar_fichas': False, 
            'editar_fichas': False,
            'eliminar_fichas': False, 
            'cambiar_password': True
        })

        # Verificar si el usuario admin existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO usuarios (usuario, password, rol, permisos) VALUES (%s, %s, %s, %s)",
                ('admin', admin_pass, 'admin', default_perms)
            )
            print("✅ Usuario 'admin' creado.")

        # Verificar si el usuario asesor existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'asesor'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO usuarios (usuario, password, rol, permisos) VALUES (%s, %s, %s, %s)",
                ('asesor', asesor_pass, 'asesor', default_perms)
            )
            print("✅ Usuario 'asesor' creado.")

        conexion.commit()
        print("🎉 Base de datos PostgreSQL inicializada correctamente.")
        return True

    except Exception as err:
        print(f"❌ Error al crear tablas: {err}")
        conexion.rollback()
        return False
    finally:
        cursor.close()
        conexion.close()

if __name__ == "__main__":
    print("🔧 Inicializando base de datos PostgreSQL...")
    crear_tablas()

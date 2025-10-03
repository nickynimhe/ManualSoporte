import psycopg2
from werkzeug.security import generate_password_hash
import json
import time

def crear_conexion():
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            print(f"🔗 Intento {intento + 1} de conexión a PostgreSQL...")
            
            # Conexión DIRECTA - valores fijos
            conexion = psycopg2.connect(
                host='dpg-d3g1q2nqaa0ldt0j7vug-a.oregon-postgres.render.com',
                database='soporte_tecnico_9sad',
                user='soporte_tecnico_9sad_user',
                password='T56GYS30j5w4k6zrdlvAh1GfExjT0t7a',
                port=5432,
                sslmode='require',
                connect_timeout=10
            )
            
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

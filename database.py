import os
import psycopg2
from urllib.parse import quote_plus
from werkzeug.security import generate_password_hash
import json
import time

def crear_conexion():
    """Conexión mejorada con mejor manejo de errores"""
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            print(f"🔗 Intento {intento + 1} de conexión a PostgreSQL...")
            
            # Usar DATABASE_URL si existe
            database_url = os.getenv('DATABASE_URL')
            
            if database_url:
                print("🔧 Usando DATABASE_URL de variable de entorno")
                if database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql://", 1)
                
                # Agregar sslmode si es necesario para Render
                if 'render.com' in database_url and 'sslmode=' not in database_url:
                    database_url += '?sslmode=require'
                    
                print(f"🔗 URL: {database_url.split('@')[0]}@***")
                conexion = psycopg2.connect(database_url)
                
            else:
                # Usar variables individuales
                user = os.getenv('DB_USER', 'soporte_tecnico_9sad_user')
                password = os.getenv('DB_PASSWORD', 'T56GYS30j5w4k6zrdlvAh1GfExjT0t7a')
                host = os.getenv('DB_HOST', 'dpg-d3g1q2nqaa0ldt0j7vug-a.oregon-postgres.render.com')
                port = os.getenv('DB_PORT', '5432')
                dbname = os.getenv('DB_NAME', 'soporte_tecnico_9sad')
                
                print(f"🔧 Configuración: host={host}, db={dbname}, user={user}")
                
                # Para Render, usar sslmode=require
                if 'render.com' in host:
                    conexion = psycopg2.connect(
                        host=host,
                        database=dbname,
                        user=user,
                        password=password,
                        port=port,
                        sslmode='require'
                    )
                else:
                    conexion = psycopg2.connect(
                        host=host,
                        database=dbname,
                        user=user,
                        password=password,
                        port=port
                    )
            
            # Verificar que la conexión funciona
            cursor = conexion.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            
            print("✅ ¡CONEXIÓN EXITOSA a PostgreSQL!")
            return conexion
            
        except Exception as err:
            print(f"❌ Intento {intento + 1} falló: {str(err)}")
            if intento < max_intentos - 1:
                print("🔄 Reintentando en 3 segundos...")
                time.sleep(3)
            else:
                print("💥 Todos los intentos de conexión fallaron")
                return None

def resetear_secuencias():
    """Función CRÍTICA: Resetea las secuencias de las tablas"""
    conexion = None
    cursor = None
    
    try:
        conexion = crear_conexion()
        if not conexion:
            print("💥 No se pudo conectar para resetear secuencias")
            return False

        cursor = conexion.cursor()
        
        print("🔄 Reseteando secuencias...")
        
        # Resetear secuencia de usuarios
        cursor.execute("""
            SELECT setval('usuarios_id_seq', COALESCE((SELECT MAX(id) FROM usuarios), 1), false)
        """)
        print("✅ Secuencia 'usuarios_id_seq' reseteada")
        
        # Resetear secuencia de fichas
        cursor.execute("""
            SELECT setval('fichas_id_seq', COALESCE((SELECT MAX(id) FROM fichas), 1), false)
        """)
        print("✅ Secuencia 'fichas_id_seq' reseteada")
        
        conexion.commit()
        print("🎉 Secuencias reseteadas correctamente")
        return True

    except Exception as err:
        print(f"💥 Error reseteando secuencias: {str(err)}")
        if conexion:
            conexion.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def crear_tablas():
    """Función mejorada para crear tablas"""
    print("🔧 Iniciando creación de tablas...")
    
    conexion = None
    cursor = None
    
    try:
        conexion = crear_conexion()
        if not conexion:
            print("💥 No se pudo conectar para crear tablas")
            return False

        cursor = conexion.cursor()

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
                categoria VARCHAR(50) NOT NULL,
                problema VARCHAR(255) NOT NULL,
                descripcion TEXT,
                causas TEXT,
                solucion TEXT NOT NULL,
                palabras_clave TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla 'fichas' lista")

        # Insertar usuario admin por defecto
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            password_hash = generate_password_hash('admin123')
            permisos_admin = json.dumps({
                'ver_fichas': True, 
                'agregar_fichas': True,
                'editar_fichas': True, 
                'eliminar_fichas': True,
                'cambiar_password': True
            })
            cursor.execute(
                "INSERT INTO usuarios (usuario, password, rol, permisos) VALUES (%s, %s, %s, %s)",
                ('admin', password_hash, 'admin', permisos_admin)
            )
            print("✅ Usuario 'admin' creado (password: admin123)")

        # RESETEAR SECUENCIAS DESPUÉS DE CREAR TABLAS
        cursor.execute("""
            SELECT setval('usuarios_id_seq', COALESCE((SELECT MAX(id) FROM usuarios), 1), true)
        """)
        cursor.execute("""
            SELECT setval('fichas_id_seq', COALESCE((SELECT MAX(id) FROM fichas), 1), true)
        """)

        conexion.commit()
        print("🎉 Base de datos inicializada CORRECTAMENTE")
        return True

    except Exception as err:
        print(f"💥 Error en creación de tablas: {str(err)}")
        if conexion:
            conexion.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def verificar_tablas():
    """Verificar que las tablas existen"""
    conexion = None
    cursor = None
    
    try:
        conexion = crear_conexion()
        if not conexion:
            return False

        cursor = conexion.cursor()
        
        # Verificar tabla usuarios
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'usuarios')")
        usuarios_existe = cursor.fetchone()[0]
        
        # Verificar tabla fichas
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'fichas')")
        fichas_existe = cursor.fetchone()[0]
        
        print(f"📊 Tabla 'usuarios' existe: {usuarios_existe}")
        print(f"📊 Tabla 'fichas' existe: {fichas_existe}")
        
        return usuarios_existe and fichas_existe
        
    except Exception as err:
        print(f"💥 Error verificando tablas: {err}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

if __name__ == "__main__":
    print("🚀 Inicializando base de datos...")
    
    # Primero resetear secuencias
    print("🔄 Reseteando secuencias...")
    if resetear_secuencias():
        print("✅ Secuencias reseteadas")
    else:
        print("⚠️ No se pudieron resetear secuencias")
    
    # Luego crear tablas si es necesario
    if crear_tablas():
        print("🎉 ¡Base de datos lista!")
    else:
        print("💥 Error inicializando base de datos")}

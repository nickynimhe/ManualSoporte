import os
import psycopg2
from urllib.parse import quote_plus
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

def crear_tablas():
    """Función para crear tablas con manejo seguro de errores"""
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

        # Tabla fichas (existente)
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

        # CORREGIDO: Tabla para soluciones visuales con la columna IMAGEN
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS soluciones_visuales (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                categoria VARCHAR(50) NOT NULL,
                descripcion TEXT,
                pasos JSONB NOT NULL DEFAULT '[]',
                imagen JSONB NOT NULL DEFAULT '[]',
                estado VARCHAR(20) DEFAULT 'activo',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla 'soluciones_visuales' lista (con columna imagen)")

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
                    'cambiar_password': True,
                    'gestion_soluciones_visuales': rol == 'admin'
                })
                cursor.execute(
                    "INSERT INTO usuarios (usuario, password, rol, permisos) VALUES (%s, %s, %s, %s)",
                    (usuario, password, rol, permisos)
                )
                print(f"✅ Usuario '{usuario}' creado")

        # Insertar algunas soluciones visuales de ejemplo
        cursor.execute("SELECT COUNT(*) FROM soluciones_visuales")
        if cursor.fetchone()[0] == 0:
            soluciones_ejemplo = [
                {
                    'titulo': 'Consultar cliente en Softv',
                    'categoria': 'Softv',
                    'descripcion': 'Guía paso a paso para consultar información de clientes en la plataforma Softv',
                    'pasos': json.dumps([
                        {
                            'titulo': 'Paso 1: Ingresar a Softv y acceder al menú lateral',
                            'descripcion': 'Dentro de la plataforma Softv, ubique el menú desplegable lateral y seleccione la opción **Facturación** para continuar con el proceso.',
                            'imagen': 'softv/softv1.png'
                        }
                    ]),
                    'imagen': 'softv/softv_principal.png'
                },
                {
                    'titulo': '¿Como validar puertos en uso y la MAC del equipo?',
                    'categoria': 'Vortex',
                    'descripcion': 'Procedimiento para validar puertos LAN y dirección MAC en dispositivos Vortex',
                    'pasos': json.dumps([
                        {
                            'titulo': 'Paso 1: Obtener el estado del dispositivo',
                            'descripcion': 'Haga clic en el botón **Get Status** para que el sistema consulte la información actual del dispositivo.',
                            'imagen': 'vortex/vortex4.png'
                        }
                    ]),
                    'imagen': 'vortex/vortex_principal.png'
                }
            ]
            
            for solucion in soluciones_ejemplo:
                cursor.execute(
                    "INSERT INTO soluciones_visuales (titulo, categoria, descripcion, pasos, imagen) VALUES (%s, %s, %s, %s, %s)",
                    (solucion['titulo'], solucion['categoria'], solucion['descripcion'], solucion['pasos'], solucion['imagen'])
                )
            print("✅ Soluciones visuales de ejemplo creadas")

        conexion.commit()
        print("🎉 Base de datos inicializada CORRECTAMENTE")
        return True

    except Exception as err:
        print(f"💥 Error en creación de tablas: {err}")
        if conexion:
            conexion.rollback()
        return False
        
    finally:
        # ✅ MANEJO SEGURO - verificar antes de cerrar
        if cursor is not None:
            cursor.close()
            print("🔒 Cursor cerrado")
        if conexion is not None:
            conexion.close()
            print("🔒 Conexión cerrada")

def verificar_tablas():
    """Función para verificar que las tablas existen"""
    conexion = None
    cursor = None
    
    try:
        conexion = crear_conexion()
        if not conexion:
            print("💥 No se pudo conectar para verificar tablas")
            return False

        cursor = conexion.cursor()
        
        # Verificar tabla usuarios
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'usuarios'
            )
        """)
        usuarios_existe = cursor.fetchone()[0]
        
        # Verificar tabla fichas
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'fichas'
            )
        """)
        fichas_existe = cursor.fetchone()[0]
        
        # Verificar tabla soluciones_visuales
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'soluciones_visuales'
            )
        """)
        soluciones_existe = cursor.fetchone()[0]
        
        # Verificar también las columnas de soluciones_visuales
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'soluciones_visuales'
        """)
        columnas = [row[0] for row in cursor.fetchall()]
        print(f"📋 Columnas de soluciones_visuales: {columnas}")
        
        print(f"📊 Tabla 'usuarios' existe: {usuarios_existe}")
        print(f"📊 Tabla 'fichas' existe: {fichas_existe}")
        print(f"📊 Tabla 'soluciones_visuales' existe: {soluciones_existe}")
        
        return usuarios_existe and fichas_existe and soluciones_existe
        
    except Exception as err:
        print(f"💥 Error verificando tablas: {err}")
        return False
        
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

def reparar_tabla_soluciones_visuales():
    """Función específica para reparar la tabla soluciones_visuales si falta la columna imagen"""
    conexion = None
    cursor = None
    
    try:
        conexion = crear_conexion()
        if not conexion:
            print("💥 No se pudo conectar para reparar tabla")
            return False

        cursor = conexion.cursor()
        
        # Verificar si la columna imagen existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'soluciones_visuales' 
                AND column_name = 'imagen'
            )
        """)
        columna_imagen_existe = cursor.fetchone()[0]
        
        if not columna_imagen_existe:
            print("🔧 Agregando columna 'imagen' a la tabla soluciones_visuales...")
            cursor.execute("""
                ALTER TABLE soluciones_visuales 
                ADD COLUMN imagen VARCHAR(255)
            """)
            conexion.commit()
            print("✅ Columna 'imagen' agregada correctamente")
        else:
            print("✅ La columna 'imagen' ya existe en soluciones_visuales")
        
        return True
        
    except Exception as err:
        print(f"💥 Error reparando tabla: {err}")
        if conexion:
            conexion.rollback()
        return False
        
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

if __name__ == "__main__":
    print("🚀 Ejecutando inicialización de base de datos...")
    
    # Primero reparar la tabla soluciones_visuales si es necesario
    print("🛠️ Verificando estructura de soluciones_visuales...")
    reparar_tabla_soluciones_visuales()
    
    # Luego verificar si las tablas ya existen
    if verificar_tablas():
        print("✅ Las tablas ya existen. No es necesario crearlas.")
    else:
        print("🔧 Creando tablas...")
        if crear_tablas():
            print("🎉 Inicialización completada exitosamente!")
        else:
            print("💥 Falló la inicialización de la base de datos")

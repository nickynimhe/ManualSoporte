import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash
import os
import json
import urllib.parse

def crear_conexion():
    try:
        # Opción 1: Usar DATABASE_URL de Render (recomendado)
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
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
        
        # Opción 2: Usar variables individuales (alternativa)
        user = os.environ.get('DB_USER', 'soporte_tecnico_9sad_user')
        password = os.environ.get('DB_PASSWORD', 'T56GYS30j5w4k6zrdlvAh1GfExjT0t7a')
        host = os.environ.get('DB_HOST', 'dpg-d3g1q2nqaa0ldt0j7vug-a.oregon-postgres.render.com')
        database = os.environ.get('DB_NAME', 'soporte_tecnico_9sad')
        port = os.environ.get('DB_PORT', '5432')

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
        print("No se pudo conectar a la base de datos para crear las tablas.")
        return

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

        # Insertar algunas fichas de ejemplo si no existen
        cursor.execute("SELECT COUNT(*) FROM fichas")
        if cursor.fetchone()[0] == 0:
            fichas_ejemplo = [
                ('TV', 'No hay señal en el televisor', 'Usuario indica que el televisor no muestra ningún canal, aparece en pantalla negra o con el mensaje sin señal.', 'Micronodo/CATV alarmado, apagado|Problemas con el decodificador', 'Encender el CATV.|Validar que el Micronodo no esté alarmado.|Confirmar que CATV y Micronodo estén conectados correctamente.|Verificar que el decodificador esté programado adecuadamente.', 'Sin señal, CATV, Micronodo, Decodificador'),
                ('Internet', 'Internet lento o intermitente', 'Usuario indica que la conexión se cae constantemente o que la velocidad es muy baja.', 'Congestión de la red|Potencias mayores a -27', 'Validar potencias del módem.|Realizar Reboot en Vortex y esperar 1 minuto.|Ejecutar Resync Config en Vortex y esperar 1 minuto.|Indicar al usuario desconectar el módem por 3 minutos.', 'Lento, Intermitente'),
                ('Equipo', 'Equipo no enciende', 'Usuario indica que el dispositivo no prende ni muestra luces aunque esté conectado a la corriente.', 'Cargador del modem desconectado|Boton OFF/ON Sin presionar', 'Indicar al usuario validar el cableado del cargador del módem.|Sugerir conectarlo en otra toma de corriente.|Realizar Resync Config en Vortex y esperar que el equipo cambie de estado.|Recomendar revisar el botón trasero del módem.|Si persiste la falla, generar orden en Softv para enviar personal técnico.', 'Apagado, No enciende, Modem')
            ]
            
            for ficha in fichas_ejemplo:
                cursor.execute(
                    "INSERT INTO fichas (categoria, problema, descripcion, causas, solucion, palabras_clave) VALUES (%s, %s, %s, %s, %s, %s)",
                    ficha
                )
            print("✅ Fichas de ejemplo creadas.")

        conexion.commit()
        print("🎉 Base de datos PostgreSQL inicializada correctamente.")

    except Exception as err:
        print(f"❌ Error al crear tablas: {err}")
        conexion.rollback()
    finally:
        cursor.close()
        conexion.close()

if __name__ == "__main__":
    print("🔧 Inicializando base de datos PostgreSQL...")
    crear_tablas()

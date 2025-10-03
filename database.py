import mysql.connector
from mysql.connector import errorcode
from werkzeug.security import generate_password_hash
import os
import json

def crear_conexion():
    try:
        # Extraer la configuración de las variables de entorno
        user = os.environ.get('MYSQL_USER')
        password = os.environ.get('MYSQL_PASSWORD')
        host = os.environ.get('MYSQL_HOST')
        database = os.environ.get('MYSQL_DATABASE')

        # Validar que las variables de entorno existan
        if not all([user, password, host, database]):
            print("❌ Error: Faltan variables de entorno para la conexión a MySQL.")
            return None

        conexion = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        return conexion
    except mysql.connector.Error as err:
        print(f"❌ Error al conectar a MySQL: {err}")
        return None

def crear_tablas():
    conexion = crear_conexion()
    if not conexion:
        print("No se pudo conectar a la base de datos para crear las tablas.")
        return

    cursor = conexion.cursor()

    try:
        # Crear tabla usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `usuarios` (
              `id` int(11) NOT NULL AUTO_INCREMENT,
              `usuario` varchar(50) NOT NULL,
              `password` varchar(255) NOT NULL,
              `rol` varchar(50) NOT NULL,
              `permisos` TEXT,
              `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
              `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
              PRIMARY KEY (`id`),
              UNIQUE KEY `usuario` (`usuario`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("✅ Tabla 'usuarios' creada o ya existente.")

        # Crear tabla fichas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `fichas` (
              `id` int(11) NOT NULL AUTO_INCREMENT,
              `categoria` varchar(50) NOT NULL,
              `problema` varchar(255) NOT NULL,
              `descripcion` text,
              `causas` text,
              `solucion` text,
              `palabras_clave` text,
              `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
              `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
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

    except mysql.connector.Error as err:
        print(f"❌ Error al crear tablas: {err}")
        conexion.rollback()
    finally:
        cursor.close()
        conexion.close()

if __name__ == "__main__":
    print("🔧 Inicializando base de datos MySQL...")
    crear_tablas()

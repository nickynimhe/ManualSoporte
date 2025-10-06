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
                pasos JSONB,
                imagen JSONB,
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
               1: {
        titulo: 'Consultar cliente en Softv',
        servicio: 'Softv',
        pasos: [
            {
                imagen: 'softv/softv1.png',
                titulo: 'Paso 1: Ingresar a Softv y acceder al menú lateral',
                descripcion: 'Dentro de la plataforma Softv, ubique el menú desplegable lateral y seleccione la opción **Facturación** para continuar con el proceso.'
            },
            {
                imagen: 'softv/softv2.png',
                titulo: 'Paso 2: Ingresar al apartado de Cajas',
                descripcion: 'Haga clic en la opción **Cajas**. Se abrirá una ventana con las herramientas disponibles para realizar la búsqueda del cliente.'
            },
            {
                imagen: 'softv/softv3.png',
                titulo: 'Paso 3: Buscar al cliente',
                descripcion: 'Digite el número de documento del titular en el campo correspondiente. Una vez aparezca el registro del usuario, haga clic en el botón **Seleccionar**.'
            },
            {
                imagen: 'softv/softv4.png',
                titulo: 'Paso 4: Visualizar la información del cliente',
                descripcion: 'Después de seleccionar al usuario, se mostrarán sus datos generales junto con los servicios activos y otra información relevante.'
            }
        ]
    },
    2: {
        titulo: '¿Como consultamos las facturas de los usuarios?',
        servicio: 'Softv',
        pasos: [
            {
                imagen: 'softv/softv5.png',
                titulo: 'Paso 1: Acceder al botón Historial',
                descripcion: 'En la parte inferior de la pantalla de información del usuario, ubique el botón **Historial** y haga clic en él.'
            },
            {
                imagen: 'softv/softv6.png',
                titulo: 'Paso 2: Ingresar al apartado de Pagos',
                descripcion: 'Al abrir el historial, se mostrarán tres opciones. Seleccione la primera opción: **Pagos**.'
            },
            {
                imagen: 'softv/softv7.png',
                titulo: 'Paso 3: Visualizar los pagos del usuario',
                descripcion: 'Dentro del apartado de pagos se presenta la información general de los abonos realizados. También se habilita la opción de consultar el comprobante del pago mediante el botón **Ver**.'
            },
            {
                imagen: 'softv/softv8.png',
                titulo: 'Paso 4: Consultar el ticket del pago',
                descripcion: 'Al hacer clic en **Ver**, se desplegará el ticket con el detalle completo del pago seleccionado.'
            }
        ]
    },
    3: {
        titulo: '¿Como consultamos las ordenes de servicio de los usuarios?',
        servicio: 'Softv',
        pasos: [
            {
                imagen: 'softv/softv9.png',
                titulo: 'Paso 1: Acceder al apartado de Órdenes de Servicio',
                descripcion: 'Desde la información del usuario, ubique y haga clic en la pestaña **Órdenes de Servicio** para visualizar los registros asociados.'
            },
            {
                imagen: 'softv/softv10.png',
                titulo: 'Paso 2: Consultar las órdenes disponibles',
                descripcion: 'En esta sección se muestran todas las órdenes creadas para el cliente, incluyendo el número de orden, estado y descripción del servicio solicitado.'
            },
            {
                imagen: 'softv/softv12.png',
                titulo: 'Paso 3: Revisar el detalle de una orden',
                descripcion: 'Seleccione una orden específica y haga clic en el botón **Ver** para consultar información detallada como fechas, técnico asignado y observaciones.'
            },
            {
                imagen: 'softv/softv11.png',
                titulo: 'Paso 4: Visualizar el estado de la orden',
                descripcion: 'En el detalle de la orden podrá confirmar el estado actual (pendientes, ejecutadas o en visita), así como el historial de seguimiento asociado.'
            }
        ]
    },
    4: {
        titulo: '¿Como consultamos reportes de fallas de los usuarios?',
        servicio: 'Softv',
        pasos: [
            {
                imagen: 'softv/softv13.png',
                titulo: 'Paso 1: Acceder al apartado de Reportes de Fallas',
                descripcion: 'Desde la información del usuario, diríjase a la pestaña **Reportes de Fallas** para consultar los incidentes registrados.'
            },
            {
                imagen: 'softv/softv10.png',
                titulo: 'Paso 2: Visualizar los reportes existentes',
                descripcion: 'En esta sección se listan los reportes generados para el cliente, incluyendo número de reporte, fecha, estado y descripción de la falla reportada.'
            },
            {
                imagen: 'softv/softv12.png',
                titulo: 'Paso 3: Revisar el detalle de un reporte',
                descripcion: 'Seleccione un reporte y haga clic en el botón **Ver** para acceder a información detallada como tipo de falla, observaciones y técnico asignado.'
            },
            {
                imagen: 'softv/softv14.png',
                titulo: 'Paso 4: Consultar el estado del reporte',
                descripcion: 'Dentro del detalle podrá verificar el estado del reporte (pendientes, ejecutadas o en visita), así como el historial de atención relacionado.'
            }
        ]
    },
    5: {
        titulo: '¿Como creamos un reporte de falla?',
        servicio: 'Softv',
        pasos: [
            {
                imagen: 'softv/softv15.png',
                titulo: 'Paso 1: Acceder al menú lateral',
                descripcion: 'Dentro de la plataforma Softv, ubique el menú desplegable lateral y seleccione la opción **Procesos** para continuar con el procedimiento.'
            },
            {
                imagen: 'softv/softv16.png',
                titulo: 'Paso 2: Ingresar al apartado de Atención Telefónica',
                descripcion: 'Haga clic en la opción **Atención Telefónica**. Se abrirá una ventana con la información correspondiente a esta sección.'
            },
            {
                imagen: 'softv/softv17.png',
                titulo: 'Paso 3: Crear una nueva atención',
                descripcion: 'Dentro de la sección, haga clic en el botón **Nueva Atención**, ubicado en la parte superior derecha de la pantalla.'
            },
            {
                imagen: 'softv/softv19.png',
                titulo: 'Paso 4: Seleccionar el servicio afectado e ingresar el contrato',
                descripcion: 'Al crear el reporte de falla, seleccione la categoría correspondiente (**TV** o **Internet**) según lo informado por el usuario. Luego ingrese el número de contrato y presione **Enter** para cargar automáticamente los datos del cliente.'
            },
            {
                imagen: 'softv/softv21.png',
                titulo: 'Paso 5: Completar los campos obligatorios',
                descripcion: 'En los recuadros amarillos, diligencie los campos solicitados. En el apartado **Reporte cliente** es obligatorio registrar al menos dos números telefónicos del usuario. Posteriormente, haga clic en el botón rojo **Generar reporte de falla** y luego en el botón verde **Guardar**.'
            },
            {
                imagen: 'softv/softv22.png',
                titulo: 'Paso 6: Registrar los datos de agendamiento',
                descripcion: 'Si el proceso fue realizado correctamente, aparecerá un recuadro de agendamiento. Complete los campos con la fecha en que se generó el reporte, seleccione el horario (**Mañana** o **Tarde**) y escriba un comentario, donde usualmente se repiten los números telefónicos del usuario. Finalmente, haga clic en **Aceptar** para que la orden se genere automáticamente.'
            }
        ]
    },
    6: {
        titulo: '¿Como creamos una orden de servicio? ',
        servicio: 'Softv',
        pasos: [
            {
                imagen: 'softv/softv23.png',
                titulo: 'Paso 1: Ingresar al apartado de Órdenes de Servicio',
                descripcion: 'Desde el menú lateral de Softv, diríjase a la sección **Procesos** y seleccione la opción **Órdenes de Servicio**. Allí podrá visualizar el listado de órdenes pendientes, junto con los datos del cliente, contrato y acciones disponibles.'
            },
            {
                imagen: 'softv/softv24.png',
                titulo: 'Paso 2: Crear una nueva orden de servicio',
                descripcion: 'En la parte superior derecha de la pantalla, haga clic en el botón **Crear Nueva Orden**. Se abrirá un formulario donde podrá diligenciar la información correspondiente al cliente y al servicio solicitado.'
            },
            {
                imagen: 'softv/softv26.png',
                titulo: 'Paso 3: Seleccionar el servicio del cliente',
                descripcion: 'Dentro del formulario, haga clic en **Agregar Servicio**. Se abrirá una ventana emergente donde deberá elegir el **Tipo de servicio** (TV por Cable o Internet), el trabajo a realizar y las observaciones necesarias.'
            },
            {
                imagen: 'softv/softv27.png',
                titulo: 'Paso 4: Definir el trabajo específico',
                descripcion: 'Según el tipo de servicio seleccionado, despliegue la lista de trabajos disponibles (por ejemplo: Instalación, Traslado de domicilio, Cambio de aparato, Desconexión temporal, entre otros). Seleccione la opción correspondiente y confirme con **Aceptar**.'
            },
            {
                imagen: 'softv/softv28.png',
                titulo: 'Paso 5: Guardar y finalizar la orden',
                descripcion: 'Una vez completada toda la información, haga clic en el botón **Guardar**. La orden quedará registrada en el sistema y podrá ser consultada o ejecutada posteriormente desde el listado de órdenes.'
            }
        ]
    },
    7: {
        titulo: '¿Como borramos un reporte de falla en caso necesario?',
        servicio: 'Softv',
        pasos: [
            {
                imagen: 'softv/softv29.png',
                titulo: 'Paso 1: Acceder a la sección de Reportes de Fallas',
                descripcion: 'En el menú lateral de Softv, seleccione la opción **Procesos** y luego haga clic en **Reportes de Fallas**. Se mostrará un listado con todos los reportes pendientes de gestión.'
            },
            {
                imagen: 'softv/softv29.png',
                titulo: 'Paso 2: Consultar un reporte de falla',
                descripcion: 'Ubique el reporte correspondiente al usuario y haga clic en el botón **Consultar** (color azul). Se abrirá una ventana con la información detallada del reporte registrado.'
            },
            {
                imagen: 'softv/softv29.png',
                titulo: 'Paso 3: Eliminar un reporte de falla',
                descripcion: 'Si desea borrar un reporte, haga clic en el botón **Eliminar** (color rojo). El sistema solicitará confirmación antes de proceder con la eliminación definitiva del registro.'
            }
        ]
    },
    8: {
        titulo: '¿Como ingresamos un nuevo cliente?',
        servicio: 'Softv',
        pasos: [
            {
                imagen: 'softv/softv30.png',
                titulo: 'Paso 1: Acceder al módulo de clientes',
                descripcion: 'En el menú lateral, ubique la sección **Catálogos > Generales** y seleccione la opción **Clientes**. Esto lo llevará al listado de clientes registrados en el sistema.'
            },
            {
                imagen: 'softv/softv31.png',
                titulo: 'Paso 2: Ingresar a la opción "Nuevo Cliente"',
                descripcion: 'En la parte superior derecha de la pantalla, haga clic en el botón **+ NUEVO CLIENTE** para iniciar el registro de un cliente en la plataforma.'
            },
            {
                imagen: 'softv/softv33.png',
                titulo: 'Paso 3: Diligenciar los datos personales',
                descripcion: 'Complete el formulario con la información personal del cliente: nombre, apellidos, tipo y número de identificación, fecha de nacimiento, teléfonos y correo electrónico. Estos campos son indispensables para la creación del cliente.'
            },
            {
                imagen: 'softv/softv33.png',
                titulo: 'Paso 4: Registrar la información de ubicación',
                descripcion: 'Seleccione la región, departamento, ciudad, localidad y barrio correspondientes. Además, diligencie la dirección completa (calle, número exterior, número interior, entre calles, código postal y estrato).'
            },
            {
                imagen: 'softv/softv33.png',
                titulo: 'Paso 5: Guardar el registro',
                descripcion: 'Una vez completados todos los campos obligatorios, haga clic en el botón **Guardar**. El sistema confirmará que el nuevo cliente ha sido creado correctamente y quedará registrado en el catálogo.'
            }
        ]
    },
    9: {
        titulo: '¿Como buscar un usuario?',
        servicio: 'Vortex',
        pasos: [
            {
                imagen: 'vortex/vortex1.png',
                titulo: 'Paso 1: Acceder al menú Configure',
                descripcion: 'En la parte superior del sistema, ubique la barra de menús y haga clic en la opción **Configured**.'
            },
            {
                imagen: 'vortex/vortex2.png',
                titulo: 'Paso 2: Ingresar el contrato en el área de búsqueda',
                descripcion: 'Dentro de la sección **Configured**, en la parte superior encontrará el campo **Search**. Ingrese el número de contrato del usuario en este espacio.'
            },
            {
                imagen: 'vortex/vortex3.png',
                titulo: 'Paso 3: Consultar las ONU asociadas al contrato',
                descripcion: 'Después de ingresar el contrato **View**, el sistema mostrará automáticamente las ONU vinculadas al cliente. Desde aquí podrá visualizarlas y gestionarlas según sea necesario.'
            }
        ]
    },
    10: {
        titulo: '¿Como validar puertos en uso y la MAC del equipo?',
        servicio: 'Vortex',
        pasos: [
            {
                imagen: 'vortex/vortex4.png',
                titulo: 'Paso 1: Obtener el estado del dispositivo',
                descripcion: 'Haga clic en el botón **Get Status** para que el sistema consulte la información actual del dispositivo.'
            },
            {
                imagen: 'vortex/vortex5.png',
                titulo: 'Paso 2: Validar puertos LAN y MAC',
                descripcion: 'En la información desplegada podrá ver los puertos LAN en uso y, validar que el dispositivo este mostrando **MAC** asociadas a la VLAN.'
            }
        ]
    },
    11: {
        titulo: '¿Como validar si el usuario esta teniendo consumo del servicio?',
        servicio: 'Vortex',
        pasos: [
            {
                imagen: 'vortex/vortex7.png',
                titulo: 'Paso 1: Validar navegación en Internet',
                descripcion: 'Para verificar si el usuario cuenta con navegación activa, haga clic en el botón verde **LIVE**. El sistema mostrará en tiempo real el estado de la conexión a Internet.'
            }
        ]
    },
    12: {
        titulo: '¿Como cambiar la VLAN?',
        servicio: 'Vortex',
        pasos: [
            {
                imagen: 'vortex/vortex8.png',
                titulo: 'Paso 1: Acceder a la configuración de VLAN',
                descripcion: 'Desplácese hacia el apartado **Speed Profiles**, ubique la casilla **Action** y haga clic en la opción **Configure**. Esto abrirá un formulario de configuración donde aparece el campo **User VLAN-ID**.'
            },
            {
                imagen: 'vortex/vortex9.png',
                titulo: 'Paso 2: Seleccionar y guardar la VLAN correspondiente',
                descripcion: 'En el campo **User VLAN-ID**, despliegue la lista y seleccione la VLAN según la zona del módem. Luego haga clic en **Save** para guardar los cambios. Finalmente, realice un **Reboot** y un **Resync Config** para aplicar la nueva configuración.'
            }
        ]
    },
    13: {
        titulo: '¿Como realizar un resync config?',
        servicio: 'Vortex',
        pasos: [
            {
                imagen: 'vortex/vortex10.png',
                titulo: 'Paso 1: Ubicar el botón Resync Config',
                descripcion: 'Desplácese hasta el final de la página y ubique el botón **Resync Config**. Al hacer clic en él, se abrirá una ventana de confirmación.'
            },
            {
                imagen: 'vortex/vortex11.png',
                titulo: 'Paso 2: Confirmar y aplicar el Resync',
                descripcion: 'En la ventana emergente, vuelva a presionar el botón **Resync Config** para confirmar la acción. Espere aproximadamente un minuto a que el módem recupere sus potencias y quede nuevamente operativo.'
            }
        ]
    },
    14: {
        titulo: '¿Como realizar un reboot?',
        servicio: 'Vortex',
        pasos: [
            {
                imagen: 'vortex/vortex12.png',
                titulo: 'Paso 1: Ubicar el botón Reboot',
                descripcion: 'Desplácese hasta el final de la página y localice el botón **Reboot**. Al hacer clic en él, se abrirá una ventana de confirmación.'
            },
            {
                imagen: 'vortex/vortex13.png',
                titulo: 'Paso 2: Confirmar y aplicar el Reboot',
                descripcion: 'En la ventana emergente, vuelva a presionar el botón **Reboot** para confirmar la acción. Espere aproximadamente un minuto a que el módem reinicie y recupere sus potencias.'
            }
        ]
    },
    15: {
        titulo: '¿Como identificar si el servicio de internet y TV estan activados?',
        servicio: 'Vortex',
        pasos: [
            {
                imagen: 'vortex/vortex14.png',
                titulo: 'Paso 1: Verificar estado de CATV y disponibilidad para deshabilitar ONU',
                descripcion: 'En la sección correspondiente observe que la casilla **CATV** debe aparecer marcada (chulito). Los botones inferiores muestran la opción **Disable ONU**, lo que indica que es posible deshabilitar la ONU desde aquí. Sin embargo, la práctica recomendada es mantener la ONU **habilitada** y conservar la casilla **CATV** activada salvo que exista una instrucción explícita para desactivarla. Si por algún motivo es necesario deshabilitarla, confirme previamente con el equipo responsable y registre la acción en la orden de servicio.'
            }
        ]
    }
};
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

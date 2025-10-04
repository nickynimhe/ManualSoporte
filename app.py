from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from database import crear_conexion, crear_tablas
from config import Config
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2
import json
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

# Función para inicializar datos en la base de datos
def inicializar_datos():
    conexion = crear_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            
            # Verificar si ya existen datos
            cursor.execute("SELECT COUNT(*) as count FROM usuarios")
            usuarios_count = cursor.fetchone()[0]  # PostgreSQL devuelve tupla
            
            cursor.execute("SELECT COUNT(*) as count FROM fichas")
            fichas_count = cursor.fetchone()[0]  # PostgreSQL devuelve tupla
            
            # Si no hay datos, insertar los datos iniciales
            if usuarios_count == 0:
                print("Inicializando datos de usuarios...")
                
                # Insertar usuarios
                usuarios_data = [
                    ('admin', 'scrypt:32768:8:1$GYLitI11BqRpnnNx$3adb3a1bf184477ed191740551bacc0554b711f78d020526a6a63fbb97562da618e5ce5ef2b2af88eae7015aa202672e22f452568aee17b2f289d34aaad96646', 'admin'),
                    ('asesor', 'scrypt:32768:8:1$y4mBv6yET3dE1AOG$a0f2ae79026b6d3accb5bd80c610f8c6c0bc1fbc70d11b8b5825188947a64abe24114f439b89f935f704416d7bc6868e37920714c8177a7eb2276c3f61095b6e', 'asesor')
                ]
                
                permisos_base = json.dumps({
                    "ver_fichas": True,
                    "agregar_fichas": False,
                    "editar_fichas": False,
                    "eliminar_fichas": False,
                    "cambiar_password": True
                })
                
                for usuario, password, rol in usuarios_data:
                    cursor.execute(
                        "INSERT INTO usuarios (usuario, password, rol, permisos) VALUES (%s, %s, %s, %s)",
                        (usuario, password, rol, permisos_base)
                    )
                
                print("Usuarios iniciales creados")
            
            if fichas_count == 0:
                print("Inicializando datos de fichas...")
                
                # Insertar fichas de ejemplo
                fichas_data = [
                    ('TV', 'No hay señal en el televisor', 'Usuario indica que el televisor no muestra ningún canal, aparece en pantalla negra o con el mensaje sin señal.', 'Micronodo/CATV alarmado, apagado|Problemas con el decodificador', 'Encender el CATV.|Validar que el Micronodo no esté alarmado.|Confirmar que CATV y Micronodo estén conectados correctamente.|Verificar que el decodificador esté programado adecuadamente.', 'Sin señal, CATV, Micronodo, Decodificador'),
                    ('TV', 'Imagen pixelada o con interferencias', 'Usuario indica que la imagen se ve con cuadritos, borrosa, congelada o con rayas', 'Cable de señal dañado|Problemas con la antena/servicio|Reprogramacion mal ejecutada', 'Validar si el inconveniente no corresponde al proveedor.|Indicar al usuario que reprograme en modo Aire/Antena.|Brindar el paso a paso para la reprogramación.|Si persiste la falla, generar orden de servicio en Softv para enviar personal técnico.', 'Pixeleado, lluvioso, intermitencia'),
                    ('Internet', 'Internet lento o intermitente', 'Usuario indica que la conexión se cae constantemente o que la velocidad es muy baja.', 'Congestión de la red|Potencias mayores a -27', 'Validar potencias del módem.|Realizar Reboot en Vortex y esperar 1 minuto.|Ejecutar Resync Config en Vortex y esperar 1 minuto.|Indicar al usuario desconectar el módem por 3 minutos.', 'Lento, Intermitente'),
                    ('Internet', 'Sin conexión a internet', 'Usuario indica que no puede navegar en ningún dispositivo y aparece como sin acceso a la red, tiene un LED rojo encendido.', 'Router/módem apagado|patchcord desconectado/Dañado', 'Habilitar nuevamente el módem en Vortex.|Si presenta LOS, generar orden de falla en Softv para enviar personal técnico.', 'LOS , Modem'),
                    ('Equipo', 'Equipo no enciende', 'Usuario indica que el dispositivo no prende ni muestra luces aunque esté conectado a la corriente.', 'Cargador del modem desconectado|Boton OFF/ON Sin presionar', 'Indicar al usuario validar el cableado del cargador del módem.|Sugerir conectarlo en otra toma de corriente.|Realizar Resync Config en Vortex y esperar que el equipo cambie de estado.|Recomendar revisar el botón trasero del módem.|Si persiste la falla, generar orden en Softv para enviar personal técnico.', 'Apagado, No enciende, Modem')
                ]
                
                for categoria, problema, descripcion, causas, solucion, palabras_clave in fichas_data:
                    cursor.execute(
                        "INSERT INTO fichas (categoria, problema, descripcion, causas, solucion, palabras_clave) VALUES (%s, %s, %s, %s, %s, %s)",
                        (categoria, problema, descripcion, causas, solucion, palabras_clave)
                    )
                
                print("Fichas iniciales creadas")
            
            conexion.commit()
            print("Base de datos inicializada correctamente")
            
        except mysql.connector.Error as e:
            print(f"Error al inicializar datos: {e}")
            conexion.rollback()
        finally:
            cursor.close()
            conexion.close()
    else:
        print("No se pudo conectar a la base de datos para inicializar")

# Agrega estas rutas ANTES de las demás rutas:

@app.route('/debug-db')
def debug_db():
    try:
        from database import crear_conexion
        conexion = crear_conexion()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            usuarios = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM fichas")
            fichas = cursor.fetchone()[0]
            
            cursor.close()
            conexion.close()
            
            return f"""
            <h1>✅ PostgreSQL CONECTADO</h1>
            <p><strong>Versión:</strong> {version}</p>
            <p><strong>Usuarios en DB:</strong> {usuarios}</p>
            <p><strong>Fichas en DB:</strong> {fichas}</p>
            <p><strong>Credenciales de prueba:</strong></p>
            <ul>
                <li>Usuario: <code>admin</code> / Contraseña: <code>admin123</code></li>
                <li>Usuario: <code>asesor</code> / Contraseña: <code>asesor123</code></li>
            </ul>
            """
        else:
            return "<h1>❌ ERROR: No se pudo conectar a PostgreSQL</h1>"
    except Exception as e:
        return f"<h1>❌ EXCEPCIÓN: {str(e)}</h1>"

@app.route('/test-login')
def test_login():
    return '''
    <h1>Prueba de Login</h1>
    <form action="/login" method="post">
        <input type="text" name="usuario" value="admin" placeholder="Usuario">
        <input type="password" name="password" value="admin123" placeholder="Contraseña">
        <button type="submit">Login</button>
    </form>
    '''

@app.context_processor
def inject_now():
    return {'now': datetime.now()}


@app.route('/test-db')
def test_db():
    try:
        from database import crear_conexion
        conexion = crear_conexion()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            usuarios = cursor.fetchone()[0]
            cursor.close()
            conexion.close()
            return f"✅ PostgreSQL OK. Versión: {version[0]}. Usuarios: {usuarios}"
        else:
            return "❌ No se pudo conectar a PostgreSQL"
    except Exception as e:
        return f"❌ Error: {str(e)}"
        

# Inyectar función de permisos a todos los templates
@app.context_processor
def inject_permissions():
    def tiene_permiso(permiso):
        if current_user.is_authenticated:
            if current_user.rol == 'admin':
                return True
            if hasattr(current_user, 'permisos'):
                return current_user.permisos.get(permiso, False)
        return False
    return dict(tiene_permiso=tiene_permiso)

class User(UserMixin):
    def __init__(self, id, usuario, rol, permisos=None):
        self.id = id
        self.usuario = usuario
        self.rol = rol
        self.permisos = permisos or {
            'ver_fichas': True,
            'agregar_fichas': False,
            'editar_fichas': False,
            'eliminar_fichas': False,
            'cambiar_password': True
        }

    def puede(self, permiso):
        if self.rol == 'admin':
            return True
        return self.permisos.get(permiso, False)

@login_manager.user_loader
def load_user(user_id):
    conexion = crear_conexion()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                # Cargar permisos desde JSON
                permisos = {}
                if user_data.get('permisos'):
                    try:
                        permisos = json.loads(user_data['permisos'])
                    except:
                        permisos = {}
                
                return User(
                    user_data['id'], 
                    user_data['usuario'], 
                    user_data['rol'],
                    permisos
                )
        except mysql.connector.Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conexion.close()
    return None

# Decorador personalizado para permisos
def permiso_requerido(permiso):
    def decorator(f):
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.puede(permiso):
                flash('No tienes permisos para acceder a esta página', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('index.html')
    
    # Si es POST, procesar el login
    cursor = None
    try:
        # Verificar si es JSON o form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        usuario = data.get('usuario')
        password = data.get('password')

        if not usuario or not password:
            if request.is_json:
                return jsonify({'error': 'Usuario y contraseña requeridos'}), 400
            else:
                return render_template('login.html', error='Usuario y contraseña requeridos')

        # Obtener conexión
        conexion = get_db()
        cursor = conexion.cursor()

        # Buscar usuario
        cursor.execute("SELECT id, usuario, password, rol, permisos FROM usuarios WHERE usuario = %s", (usuario,))
        user_data = cursor.fetchone()

        if not user_data:
            if request.is_json:
                return jsonify({'error': 'Usuario no encontrado'}), 401
            else:
                return render_template('login.html', error='Usuario no encontrado')

        user_id, username, hashed_password, rol, permisos = user_data

        # Verificar contraseña
        if not check_password_hash(hashed_password, password):
            if request.is_json:
                return jsonify({'error': 'Contraseña incorrecta'}), 401
            else:
                return render_template('login.html', error='Contraseña incorrecta')

        # Login exitoso
        session['user_id'] = user_id
        session['usuario'] = username
        session['rol'] = rol
        session['permisos'] = permisos

        if request.is_json:
            return jsonify({
                'mensaje': 'Login exitoso',
                'usuario': username,
                'rol': rol,
                'permisos': permisos
            }), 200
        else:
            return redirect(url_for('index'))  # Redirigir a la página principal

    except Exception as err:
        print(f"💥 Error en login: {err}")
        if request.is_json:
            return jsonify({'error': 'Error interno del servidor'}), 500
        else:
            return render_template('login.html', error='Error interno del servidor')
        
    finally:
        # ✅ SOLO cerrar recursos, sin return
        if cursor is not None:
            cursor.close()


@app.route('/soluciones_visuales')
@login_required
def soluciones_visuales():
    soluciones = [
        {
            'id': 1,
            'titulo': '¿Como consultamos clientes?',
            'categoria': 'Softv',
            'imagenes': ['softv/softv1.png', 'softv/softv2.png', 'softv/softv3.png', 'softv/softv4.png'],
            'descripcion': 'Busqueda del cliente paso a paso'
        },
        {
            'id': 2,
            'titulo': '¿Como vemos las facturas del usuario?',
            'categoria': 'Softv',
            'imagenes': ['softv/softv5.png', 'softv/softv6.png', 'softv/softv7.png', 'softv/softv8.png'],
            'descripcion': 'Consultar historial de pagos del usuario'
        },
        {
            'id': 3,
            'titulo': '¿Como consultamos las ordenes de servicio de los usuarios?',
            'categoria': 'Softv',
            'imagenes': ['softv/softv9.png', 'softv/softv10.png', 'softv/softv11.png', 'softv/softv12.png'],
            'descripcion': 'Consultar historial de ordenes de servicio del usuario'
        },
        {
            'id': 4,
            'titulo': '¿Como consultamos reportes de fallas de los usuarios?',
            'categoria': 'Softv',
            'imagenes': ['softv/softv13.png', 'softv/softv14.png', 'softv/softv15.png', 'softv/softv16.png'],
            'descripcion': 'Consultar historial de reportes de falla del usuario'
        },
        {
            'id': 5,
            'titulo': '¿Como creamos un reporte de falla?',
            'categoria': 'Softv', 
            'imagenes': ['softv/softv15.png', 'softv/softv16.png', 'softv/softv17.png', 'softv/softv19.png', 'softv/softv21.png', 'softv/softv22.png'],
            'descripcion': 'Crear un reporte de falla'
        },
        {
            'id': 6,
            'titulo': '¿Como creamos una orden de servicio?',
            'categoria': 'Softv',
            'imagenes': ['softv/softv23.png', 'softv/softv24.png', 'softv/softv26.png', 'softv/softv27.png', 'softv/softv28.png'],
            'descripcion': 'Crear una orden de servicio'
        },
        {
            'id': 7,
            'titulo': '¿Como borramos un reporte de falla en caso necesario?',
            'categoria': 'Softv',
            'imagenes': ['softv/softv29.png', 'softv/softv29.png', 'softv/softv29.png'],
            'descripcion': 'Como eliminar un reporte de falla'
        },
        {
            'id': 8,
            'titulo': '¿Como ingresamos un nuevo cliente?',
            'categoria': 'Softv',
            'imagenes': ['softv/softv30.png', 'softv/softv31.png', 'softv/softv32.png', 'softv/softv33.png', 'softv/softv32.png'],
            'descripcion': 'Crear un nuevo cliente'
        },
        {
            'id': 9,
            'titulo': '¿Como buscar un usuario?',
            'categoria': 'Vortex',
            'imagenes': ['vortex/vortex1.png', 'vortex/vortex2.png', 'vortex/vortex3.png'],
            'descripcion': 'Buscar a un usuario'
        },
        {
            'id': 10,
            'titulo': '¿Como validar puertos en uso y la MAC del equipo?',
            'categoria': 'Vortex',
            'imagenes': ['vortex/vortex4.png', 'vortex/vortex5.png'],
            'descripcion': 'Como validar si el usuario esta haciendo uso de los puertos o el dispositivo no da MAC'
        },
        {
            'id': 11,
            'titulo': '¿Como validar si el usuario esta teniendo consumo del servicio?',
            'categoria': 'Vortex',
            'imagenes': ['vortex/vortex7.png'],
            'descripcion': 'Como validar el consumo del usuario'
        },
        {
            'id': 12,
            'titulo': '¿Como cambiar la VLAN?',
            'categoria': 'Vortex',
            'imagenes': ['vortex/vortex8.png', 'vortex/vortex9.png'],
            'descripcion': 'Como cambiar la VLAN acorde a la zona'
        },
        {
            'id': 13,
            'titulo': '¿Como realizar un resync config?',
            'categoria': 'Vortex',
            'imagenes': ['vortex/vortex10.png', 'vortex/vortex11.png'],
            'descripcion': 'Como realizar un resync config'
        },
        {
            'id': 14,
            'titulo': '¿Como realizar un reboot?',
            'categoria': 'Vortex',
            'imagenes': ['vortex/vortex12.png', 'vortex/vortex13.png'],
            'descripcion': 'Como realizar un reebot'
        },
        {
            'id': 15,
            'titulo': '¿Como identificar si el servicio de internet y TV estan activados?',
            'categoria': 'Vortex',
            'imagenes': ['vortex/vortex14.png'],
            'descripcion': 'Validar si el servicio esta activo'
        }
    ]
    return render_template('soluciones_visuales.html', soluciones=soluciones)

@app.route('/atencion_telefonica')
@login_required
def atencion_telefonica():
    return render_template('atencion_telefonica.html')

# Agregar esta ruta en app.py
@app.route('/informacion-general')
@login_required
def informacion_general():
    informacion = {
        'planes': {
            'titulo': '📡 Planes de Servicio',
            'icono': 'fa-tv',
            'contenido': [
                {
                    'subtitulo': 'Planes Básicos',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '💯 **PLANES DE TV E INTERNET** 💯',
                        '400 megas + TV: $85.000',
                        '500 megas + TV: $95.000', 
                        '600 megas + TV: $105.000',
                        '',
                        '💯 **PLANES SOLO TV** 💯',
                        '10Mb + TV: $50.000',
                        '',
                        '🌐 **PLANES SOLO INTERNET** 🌐',
                        '400 megas: $75.000',
                        '500 megas: $85.000',
                        '600 megas: $95.000'
                    ]
                },
                {
                    'subtitulo': 'Planes Corporativos',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '💯 **PLANES CORPORATIVOS** 💯',
                        '1Mb: $12.000',
                        '30Mb (mínimo): $360.000 + 19% IVA = $428.400',
                         '**Planes hogar:** se agrega 19% IVA',
                        '**Equipo:** robusto para configuraciones especiales'
                    ]
                },
                
                 {
                    'subtitulo': 'Planes Guamal y Sanmartin',  # NUEVA SUBSECCIÓN
                    'contenido_items': [
                        '🎯 *PLANES DE TV + INTERNET* 🎯',
                        'TV + 200MB: $65.000',
                        'TV + 300MB: $75.000', 
                        'TV + 400MB: $85.000',
                        '',
                        '📺 *PLAN SOLO TV* 📺',
                        'Solo TV: $50.000'
                    ]
                },
                 
                {
                    'subtitulo': 'Planes Acacías',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '💯 **PLANES DE TV E INTERNET** 💯',
                        'TV + Internet 200MB: $85.000',
                        'TV + Internet 300MB: $95.000',
                        'TV + Internet 400MB: $105.000',
                        '',
                        '💯 **PLANES SOLO TV** 💯',
                        'Solo TV: $50.000',
                        '',
                        '🌐 **PLANES SOLO INTERNET** 🌐',
                        '200MB: $75.000',
                        '300MB: $85.000',
                        '400MB: $95.000'
                    ]
                }
            ]
        },
        'afiliaciones': {
            'titulo': '👥 Afiliaciones',
            'icono': 'fa-user-plus',
            'contenido': [
                {
                    'subtitulo': 'Información General para Afiliar',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**La afiliación no tiene costo**',
                        '**Instalación sin costo** en zona urbana (rural: $150.000)',
                        '',
                        '**Requisitos:**',
                        '• 1 Fotocopia de la cédula',
                        '• 1 Fotocopia del recibo de agua o luz',
                        '• Pago del primer mes por anticipado',
                        '• Servicio de TV para 2 televisores',
                        '',
                        '**Puntos adicionales de TV:**',
                        '• Cada punto: $20.000 (solo instalación)',
                        '• Mensualidad no cambia',
                        '• Solo para el mismo predio',
                        '',
                        '**Señal Digital:**',
                        '• Decodificador: $58.000 (único pago)',
                        '• Para TVs clásicos con señal analógica',
                        '',
                        '**Tiempo de instalación:** 2-4 días hábiles'
                    ]
                },
                {
                    'subtitulo': 'Afiliación San Joaquín',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Costo de instalación:** $60.000',
                        '**Fibra incluida:** primeros 70 metros',
                        '**Costo metro adicional:** $1.700',
                        '',
                        '**Servicio de TV:** 1 televisor',
                        '**Puntos adicionales:** $35.000 c/u',
                        '**Requisitos y tiempos iguales**  a afiliación general'
                    ]
                },
                {
                    'subtitulo': 'Información Adicional',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Para asesores solicitar:**',
                        '• Barrio',
                        '• Dirección exacta', 
                        '• Nombre del titular',
                        '• 2 números de teléfono',
                        '',
                        '**Sin cláusula de permanencia**',
                        '**Pago por adelantado** después de firmar contrato',
                        '**Contrato**  se envía y recibe por el mismo medio'
                    ]
                }
            ]
        },
        'win_sports': {
            'titulo': '⚽ Win Sports +',
            'icono': 'fa-futbol',
            'contenido': [
                {
                    'subtitulo': '¡Llegó Win Sports + a M@STV Producciones!',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Precio:** $35.000 adicionales al mes',
                        '**Incluye:**',
                        '• Acceso a Win Sports +',
                        '• 14 canales premium',
                        '• Y mucho más contenido deportivo',
                        '',
                        '**TV Box:** $100.000 (costo único)',
                        '**No necesario** si TV es Android (con Google Play Store)',
                        '**Cláusula:** 6 meses',
                        '**Requisito:** Tener plan de internet con nosotros'
                    ]
                }
            ]
        },
        'oficinas': {
            'titulo': '🏢 Oficinas y Horarios',
            'icono': 'fa-building',
            'contenido': [
                {
                    'subtitulo': 'Horarios de Atención',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Lunes a Viernes:** 8:00 AM - 5:00 PM',
                        '**Sábados:** 8:00 AM - 12:00 PM'
                    ]
                },
                {
                    'subtitulo': 'Direcciones de Oficinas',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Facatativá:** Cl 11 #7A-04, Diurba',
                        '**Bojacá:** Cr 6 #5-146, Barrio Centro',
                        '**Zipacón:** Crr 4 #5-57, Frente al parque',
                        '**Rosal:** Cr 8 #8-08, Local 3 Centro',
                        '**El Triunfo:** Crr 3 #2-40, Frente al coliseo',
                        '**Viotá:** Cl 20 #11-10, Frente a estación de policía',
                        '**Girardot:** Crr 10 #18-44, Barrio Centro / Frente a Bancamía',
                        '**Cachipay:** Crr 3 #3-36, Barrio Centro',
                        '**Sasaima:** Crr 2 #3-30, Barrio 3 Esquinas',
                        '**La Mesa:** Cl 8 #16-59, Barrio Santa Bárbara',
                        '**Anolaima:** Crr 7 #02-57, Barrio Centro',
                        '**Mesitas del Colegio:** Cl 10 #6-37, Barrio Centro',
                        '**Anapoima:** Cr 2 #7-32, Local 2 Centro',
                        '**Albán:** Cl 4 #2-04, Punto de Servientrega',
                        '**Madrid:** Cl 12 #3-64, Barrio Arrayane',
                        '**Guayabal de Síquima:** Cl 3 #5-28',
                        '**Tocaima:** Cl 4 #9-75',
                        '**San Joaquín:** Cr 4 N 4-55, Al lado del árbol de los aburridos',
                        '**Apulo:** Cl 14 #6-23, Local 102',
                        '**Villeta:** Cr 5 #3-43, Local 6 Torre 4 Conjunto Santa Cruz',
                        '**Acacías:** Cl 15 #22-40, Local 12, Edificio Dark Gym',
                        '**San Martín:** Cl 7 #5-34, Barrio Fundadores',
                        '**Guamal:** Cl 10 #4A-04, Barrio Las Villas',
                        '**Quipile:** Crr 2 #6-07'
                    ]
                },
                {
                    'subtitulo': 'Puntos Autorizados Facatativá',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Bolos el Tunjo:** Cr 2 #6-105',
                        '**CLT Comunicaciones:** Cl 19 #1A-28 Sur, Prado de Cartagenita',
                        '**Portal de María:** Transversal 11 #5-04, Manzana 5 Casa 30 S.M.A.',
                        '**Papelería Expresate:** Cl 8 #10-05, Zambrano',
                        '**One Books:** Diagonal 5 Este #9E-02, Juan Pablo II',
                        '**Papelería Chico 1:** Cr 3 #5B-08 Este, Chico 1'
                    ]
                }
            ]
        },
        'procesos': {
            'titulo': '📋 Procesos y Trámites',
            'icono': 'fa-clipboard-list',
            'contenido': [
                {
                    'subtitulo': 'Cancelación de Servicio',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Requisitos:**',
                        '• Acercarse a la oficina',
                        '• Carta indicando razón de cancelación',
                        '• Paz y salvo',
                        '• Equipos instalados (equipos y cargadores)'
                    ]
                },
                {
                    'subtitulo': 'Cambio de Titular',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Requisitos:**',
                        '• Carta solicitando cambio, firmada por antiguo y nuevo titular',
                        '• Copia de cédula del nuevo titular',
                        '• Estar al día en los pagos'
                    ]
                },
                {
                    'subtitulo': 'Cambio de Plan',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Procedimiento:**',
                        '• Acercarse a la oficina',
                        '• Carta solicitando cambio de plan',
                        '• Estar al día en pagos',
                        '• Cancelar por adelantado valor del nuevo plan',
                        '• Ideal realizarlo a finales de mes'
                    ]
                },
                {
                    'subtitulo': 'Traslado de Domicilio',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Costo:** $20.000',
                        '**Puntos adicionales:** $10.000 c/u (movimiento)',
                        '**Tiempo:** 2-3 días hábiles',
                        '**Requisito:** Llevar equipos a la nueva residencia'
                    ]
                },
                {
                    'subtitulo': 'Solicitud de Facturas',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Datos requeridos:**',
                        '• Contrato',
                        '• Nombre completo',
                        '• Cédula',
                        '• Correo electrónico',
                        '• Teléfono',
                        '• Dirección completa',
                        '• Municipio y barrio',
                        '• Plan de internet',
                        '• Valor del plan',
                        '• Estrato',
                        '**Empresas:** enviar foto del RUT'
                    ]
                }
            ]
        },
        'contacto': {
            'titulo': '📞 Contacto y Soporte',
            'icono': 'fa-headset',
            'contenido': [
                {
                    'subtitulo': 'Información de Contacto',
                    'contenido_items': [  # CAMBIADO: items -> contenido_items
                        '**Email PQR:** pqr@mastvproducciones.net.co',
                        '**Email CARTERA:** auxiliaradministrativo@mastvproducciones.net.co',
                        '**Email INGENIERIA: ingenieria@mastvproducciones.net.co',
                        '**Email RECURSOS HUMANOS:** rh@mastvproducciones.net.co',
                        '**Chat de Soporte:** Solo mensajes escritos 3187777771',
                        '**No se reciben:** audios ni llamadas por WhatsApp'
                    ]
                }
            ]
        }
    }
    
    return render_template('informacion_general.html', informacion=informacion)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

# Ruta para cambiar contraseña (todos los usuarios)
@app.route('/cambiar_password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    if request.method == 'POST':
        password_actual = request.form['password_actual']
        nueva_password = request.form['nueva_password']
        confirmar_password = request.form['confirmar_password']
        
        # Validaciones
        if not password_actual or not nueva_password or not confirmar_password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('cambiar_password.html')
        
        if nueva_password != confirmar_password:
            flash('Las nuevas contraseñas no coinciden', 'error')
            return render_template('cambiar_password.html')
        
        if len(nueva_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('cambiar_password.html')
        
        # Verificar contraseña actual
        conexion = crear_conexion()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                cursor.execute("SELECT password FROM usuarios WHERE id = %s", (current_user.id,))
                usuario = cursor.fetchone()
                
                if usuario and check_password_hash(usuario['password'], password_actual):
                    # Actualizar contraseña
                    hash_nueva_password = generate_password_hash(nueva_password)
                    cursor.execute(
                        "UPDATE usuarios SET password = %s WHERE id = %s",
                        (hash_nueva_password, current_user.id)
                    )
                    conexion.commit()
                    flash('Contraseña actualizada correctamente', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('La contraseña actual es incorrecta', 'error')
                    
            except mysql.connector.Error as e:
                flash('Error al cambiar la contraseña', 'error')
                print(f"Error: {e}")
            finally:
                cursor.close()
                conexion.close()
    
    return render_template('cambiar_password.html')

# Ruta para gestionar usuarios (solo admin)
@app.route('/usuarios')
@login_required
def gestion_usuarios():
    if current_user.rol != 'admin':
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('index'))
    
    conexion = crear_conexion()
    usuarios = []
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios ORDER BY fecha_creacion DESC")
            usuarios = cursor.fetchall()
            
            # Parsear permisos JSON para cada usuario
            for usuario in usuarios:
                if usuario.get('permisos'):
                    try:
                        usuario['permisos_parsed'] = json.loads(usuario['permisos'])
                    except:
                        usuario['permisos_parsed'] = {}
                else:
                    usuario['permisos_parsed'] = {}
                    
        except mysql.connector.Error as e:
            flash('Error al cargar los usuarios', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    return render_template('gestion_usuarios.html', usuarios=usuarios)

# Ruta para editar usuario (solo admin)
@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if current_user.rol != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('index'))
    
    conexion = crear_conexion()
    usuario_data = None
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            
            if request.method == 'POST':
                usuario = request.form['usuario']
                password = request.form['password']
                rol = request.form['rol']
                
                # Obtener permisos del formulario (sin gestionar_usuarios)
                permisos = {
                    'ver_fichas': True,  # Siempre activo
                    'agregar_fichas': 'agregar_fichas' in request.form,
                    'editar_fichas': 'editar_fichas' in request.form,
                    'eliminar_fichas': 'eliminar_fichas' in request.form,
                    'cambiar_password': True  # Siempre permitido
                }
                
                permisos_json = json.dumps(permisos)
                
                if password:
                    hash_password = generate_password_hash(password)
                    cursor.execute(
                        "UPDATE usuarios SET usuario = %s, password = %s, rol = %s, permisos = %s WHERE id = %s",
                        (usuario, hash_password, rol, permisos_json, id)
                    )
                else:
                    cursor.execute(
                        "UPDATE usuarios SET usuario = %s, rol = %s, permisos = %s WHERE id = %s",
                        (usuario, rol, permisos_json, id)
                    )
                
                conexion.commit()
                flash('Usuario actualizado correctamente', 'success')
                return redirect(url_for('gestion_usuarios'))
            
            # GET: Cargar datos del usuario
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
            usuario_data = cursor.fetchone()
            
            if usuario_data and usuario_data.get('permisos'):
                try:
                    usuario_data['permisos_parsed'] = json.loads(usuario_data['permisos'])
                except:
                    usuario_data['permisos_parsed'] = {}
            else:
                usuario_data['permisos_parsed'] = {}
            
        except psycopg2.IntegrityError:
            flash('El usuario ya existe', 'error')
        except mysql.connector.Error as e:
            flash('Error al editar el usuario', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    if not usuario_data:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('gestion_usuarios'))
    
    return render_template('editar_usuario.html', usuario=usuario_data)

# Ruta para agregar usuario (solo admin)
@app.route('/agregar_usuario', methods=['GET', 'POST'])
@login_required
def agregar_usuario():
    if current_user.rol != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        rol = request.form['rol']
        
        if not usuario or not password:
            flash('Usuario y contraseña son obligatorios', 'error')
            return render_template('agregar_usuario.html')
        
        # Obtener permisos del formulario (sin gestionar_usuarios)
        permisos = {
            'ver_fichas': True,  # Siempre activo
            'agregar_fichas': 'agregar_fichas' in request.form,
            'editar_fichas': 'editar_fichas' in request.form,
            'eliminar_fichas': 'eliminar_fichas' in request.form,
            'cambiar_password': True  # Siempre permitido
        }
        
        permisos_json = json.dumps(permisos)
        hash_password = generate_password_hash(password)
        
        conexion = crear_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (usuario, password, rol, permisos) VALUES (%s, %s, %s, %s)",
                    (usuario, hash_password, rol, permisos_json)
                )
                conexion.commit()
                flash('Usuario agregado correctamente', 'success')
                return redirect(url_for('gestion_usuarios'))
            except psycopg2.IntegrityError:
                flash('El usuario ya existe', 'error')
            except mysql.connector.Error as e:
                flash('Error al agregar el usuario', 'error')
                print(f"Error: {e}")
            finally:
                cursor.close()
                conexion.close()
    
    return render_template('agregar_usuario.html')

# Ruta para eliminar usuario (solo admin)
@app.route('/eliminar_usuario/<int:id>')
@login_required
def eliminar_usuario(id):
    if current_user.rol != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('index'))
    
    if id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'error')
        return redirect(url_for('gestion_usuarios'))
    
    conexion = crear_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
            conexion.commit()
            flash('Usuario eliminado correctamente', 'success')
        except mysql.connector.Error as e:
            flash('Error al eliminar el usuario', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    return redirect(url_for('gestion_usuarios'))

# Rutas principales
@app.route('/')
@login_required
def index():
    if not current_user.puede('ver_fichas'):
        flash('No tienes permisos para ver las fichas', 'error')
        return redirect(url_for('login'))
    
    conexion = crear_conexion()
    fichas = []
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM fichas ORDER BY fecha_actualizacion DESC")
            fichas = cursor.fetchall()
        except mysql.connector.Error as e:
            flash('Error al cargar las fichas', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    return render_template('index.html', fichas=fichas, user=current_user)

@app.route('/agregar', methods=['GET', 'POST'])
@login_required
def agregar_ficha():
    if not current_user.puede('agregar_fichas'):
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Obtener datos del formulario - manejar problema real o seleccionado
        categoria = request.form['categoria']
        problema = request.form.get('problema_real') or request.form['problema']
        descripcion = request.form['descripcion']
        causas = request.form['causas']
        solucion = request.form['solucion']
        palabras_clave = request.form['palabras_clave']
        
        # Validar campos requeridos
        if not all([categoria, problema, causas, solucion]):
            flash('Por favor, complete todos los campos requeridos', 'error')
            return render_template('agregar_ficha.html')
        
        # Procesar causas (convertir saltos de línea a |)
        causas_items = [item.strip() for item in causas.split('\n') if item.strip()]
        causas_str = '|'.join(causas_items)
        
        conexion = crear_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute('''
                    INSERT INTO fichas (categoria, problema, descripcion, causas, solucion, palabras_clave)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (categoria, problema, descripcion, causas_str, solucion, palabras_clave))
                conexion.commit()
                flash('Ficha agregada correctamente', 'success')
                return redirect(url_for('index'))
            except mysql.connector.Error as e:
                flash('Error al agregar la ficha', 'error')
                print(f"Error: {e}")
            finally:
                cursor.close()
                conexion.close()
    
    return render_template('agregar_ficha.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_ficha(id):
    if not current_user.puede('editar_fichas'):
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('index'))
    
    conexion = crear_conexion()
    ficha = None
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            
            if request.method == 'POST':
                categoria = request.form['categoria']
                problema = request.form['problema']
                descripcion = request.form['descripcion']
                causas = request.form['causas']
                solucion = request.form['solucion']
                palabras_clave = request.form['palabras_clave']
                
                # Procesar causas (convertir saltos de línea a |)
                causas_items = [item.strip() for item in causas.split('\n') if item.strip()]
                causas_str = '|'.join(causas_items)
                
                cursor.execute('''
                    UPDATE fichas 
                    SET categoria=%s, problema=%s, descripcion=%s, 
                    causas=%s, solucion=%s, palabras_clave=%s 
                    WHERE id=%s
                ''', (categoria, problema, descripcion, causas_str, solucion, palabras_clave, id))
                
                conexion.commit()
                flash('Ficha actualizada correctamente', 'success')
                return redirect(url_for('index'))
            
            # GET: Cargar datos de la ficha
            cursor.execute("SELECT * FROM fichas WHERE id = %s", (id,))
            ficha = cursor.fetchone()
            
            # Convertir | de vuelta a saltos de línea para el formulario
            if ficha and ficha['causas']:
                ficha['causas'] = ficha['causas'].replace('|', '\n')
            
        except mysql.connector.Error as e:
            flash('Error al cargar/editar la ficha', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    if not ficha:
        flash('Ficha no encontrada', 'error')
        return redirect(url_for('index'))
    
    return render_template('editar_ficha.html', ficha=ficha)

@app.route('/eliminar/<int:id>')
@login_required
def eliminar_ficha(id):
    if not current_user.puede('eliminar_fichas'):
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('index'))
    
    conexion = crear_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM fichas WHERE id = %s", (id,))
            conexion.commit()
            flash('Ficha eliminada correctamente', 'success')
        except mysql.connector.Error as e:
            flash('Error al eliminar la ficha', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    return redirect(url_for('index'))

@app.route('/buscar')
@login_required
def buscar():
    if not current_user.puede('ver_fichas'):
        flash('No tienes permisos para ver las fichas', 'error')
        return redirect(url_for('index'))
    
    query = request.args.get('q', '')
    categoria = request.args.get('categoria', '')
    
    conexion = crear_conexion()
    fichas = []
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            
            if categoria and query:
                sql = "SELECT * FROM fichas WHERE categoria = %s AND (problema LIKE %s OR palabras_clave LIKE %s)"
                cursor.execute(sql, (categoria, f'%{query}%', f'%{query}%'))
            elif categoria:
                sql = "SELECT * FROM fichas WHERE categoria = %s"
                cursor.execute(sql, (categoria,))
            elif query:
                sql = "SELECT * FROM fichas WHERE problema LIKE %s OR palabras_clave LIKE %s"
                cursor.execute(sql, (f'%{query}%', f'%{query}%'))
            else:
                cursor.execute("SELECT * FROM fichas ORDER BY fecha_actualizacion DESC")
            
            fichas = cursor.fetchall()
        except mysql.connector.Error as e:
            flash('Error en la búsqueda', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    return render_template('buscar.html', fichas=fichas, query=query, categoria=categoria)

@app.route('/ficha/<int:id>')
@login_required
def ver_ficha(id):
    if not current_user.puede('ver_fichas'):
        flash('No tienes permisos para ver las fichas', 'error')
        return redirect(url_for('index'))
    
    conexion = crear_conexion()
    ficha = None
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM fichas WHERE id = %s", (id,))
            ficha = cursor.fetchone()
        except mysql.connector.Error as e:
            flash('Error al cargar la ficha', 'error')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    if not ficha:
        flash('Ficha no encontrada', 'error')
        return redirect(url_for('index'))
    
    return render_template('ver_ficha.html', ficha=ficha)

# API para obtener problemas por categoría
@app.route('/api/problemas/<categoria>')
@login_required
def obtener_problemas(categoria):
    problemas_por_categoria = {
        'TV': [
            'No hay señal en el televisor',
            'Imagen pixelada o con interferencias',
            'Sin sonido en algunos canales',
            'Problemas con la guía de programación',
            'Otro problema con TV'
        ],
        'Internet': [
            'Internet lento o intermitente',
            'Sin conexión a internet',
            'Problemas con WiFi',
            'No puedo conectarme a sitios específicos',
            'Velocidad inferior a la contratada',
            'Problemas con el módem/router',
            'Otro problema con Internet'
        ],
        'Equipo': [
            'Equipo no enciende',
            'Problemas con puertos HDMI/USB',
            'Dispositivo no da MAC',
            'Problemas niveles opticos',
            'Otro problema con Equipo'
        ]
    }
    
    problemas = problemas_por_categoria.get(categoria, [])
    return jsonify(problemas)

if __name__ == '__main__':
    with app.app_context():
        print("🚀 Iniciando aplicación Flask...")
        # Solo crear tablas cuando se ejecute la app, no en import
        from database import crear_tablas
        crear_tablas()
    app.run(host='0.0.0.0', port=5000, debug=True)

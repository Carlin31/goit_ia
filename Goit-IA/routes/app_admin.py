import os
import json
import shutil
import sys
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response, stream_with_context
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS (BASE = RAÍZ)
# ==========================================

# Obtenemos la ruta absoluta de ESTE archivo
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)

# LÓGICA: Buscar dónde está la carpeta 'data' para definir la RAÍZ del proyecto
# Caso 1: Si 'data' está al lado de este archivo, estamos en la raíz.
if os.path.exists(os.path.join(current_dir, 'data')):
    PROJECT_ROOT = current_dir
else:
    # Caso 2: Si no, estamos en una subcarpeta (ej. /src, /routes), subimos un nivel.
    PROJECT_ROOT = os.path.dirname(current_dir)

# Definimos las rutas absolutas a partir de la RAÍZ encontrada
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
REGISTRY_FILE = os.path.join(DATA_DIR, 'registry.json')

# Agregamos la raíz al sistema para que Python encuentre tus módulos (logic, data, models)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# --- DEBUG EN CONSOLA ---
print(f"✅ Raíz del proyecto detectada: {PROJECT_ROOT}")
print(f"✅ Carpeta de datos: {DATA_DIR}")

# ==========================================
# 2. IMPORTS DE MÓDULOS DEL PROYECTO
# ==========================================
try:
    # Importamos la lógica de base de datos (Entrenamiento)
    from data.admin_db import actualizar_base_datos_completa
    # Importamos la lógica de registro de usuarios (Estadísticas y Logs)
    from logic.access_tracker import obtener_estadisticas_diarias, obtener_todos_los_registros
except ImportError as e:
    print(f"❌ Error importando módulos locales: {e}")
    # Funciones vacías para evitar caídas si faltan archivos
    def obtener_estadisticas_diarias(): return {}
    def obtener_todos_los_registros(): return []
    def actualizar_base_datos_completa(reg): pass

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Asegurar que existan las carpetas físicas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Crear archivo de registro si no existe
if not os.path.exists(REGISTRY_FILE):
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump({"pdfs": [], "urls": []}, f)

# ==========================================
# 3. SEGURIDAD Y UTILIDADES
# ==========================================
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS_HASH = generate_password_hash(os.getenv("ADMIN_PASS", "admin"))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def load_registry():
    """Carga el JSON de registro de archivos."""
    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"pdfs": [], "urls": []}

def save_registry(data):
    """Guarda cambios en el JSON."""
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# ==========================================
# 4. RUTAS PRINCIPALES (DASHBOARD)
# ==========================================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        password = request.form.get('password')
        
        if user == ADMIN_USER and check_password_hash(ADMIN_PASS_HASH, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Credenciales incorrectas', 'error')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('inicio.index'))

@admin_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    registry = load_registry()
    
    # 1. Estadísticas para gráficas (Tarjetas)
    stats = obtener_estadisticas_diarias()
    
    # 2. Lista completa para la tabla detallada (Modal)
    access_logs = obtener_todos_los_registros()
    
    return render_template('admin/dashboard.html', 
                           pdfs=registry.get('pdfs', []), 
                           urls=registry.get('urls', []),
                           stats=stats,           # <-- Datos para tarjetas
                           access_logs=access_logs) # <-- Datos para tabla detallada

# ==========================================
# 5. GESTIÓN DE PDF (SUBIR, BORRAR, EDITAR)
# ==========================================

@admin_bp.route('/upload_pdf', methods=['POST'])
@login_required
def upload_pdf():
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('admin.dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Nombre de archivo vacío', 'error')
        return redirect(url_for('admin.dashboard'))

    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        
        # 1. Guardar Físicamente (Ruta Absoluta)
        abs_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(abs_path)
        
        # 2. Guardar en JSON (Ruta Relativa para compatibilidad)
        rel_path = os.path.join('data', 'uploads', filename).replace('\\', '/')
        
        registry = load_registry()
        if 'pdfs' not in registry: registry['pdfs'] = []

        if not any(c['filename'] == filename for c in registry['pdfs']):
            registry['pdfs'].append({
                "filename": filename,
                "path": rel_path,
                "status": "En espera" 
            })
            save_registry(registry)
            flash('PDF cargado correctamente.', 'success')
        else:
            flash('Este archivo ya existe.', 'warning')
    else:
        flash('Solo se permiten archivos PDF', 'error')
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_pdf', methods=['POST'])
@login_required
def delete_pdf():
    filename = request.form.get('filename')
    registry = load_registry()
    
    original_count = len(registry.get('pdfs', []))
    registry['pdfs'] = [p for p in registry.get('pdfs', []) if p['filename'] != filename]
    
    if len(registry['pdfs']) < original_count:
        # Borrado físico
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error borrando archivo físico: {e}")
        
        save_registry(registry)
        flash(f'PDF "{filename}" eliminado.', 'success')
    else:
        flash('No se encontró el archivo.', 'error')
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/edit_pdf', methods=['POST'])
@login_required
def edit_pdf():
    original_name = request.form.get('original_filename')
    new_name_input = request.form.get('new_filename')
    
    if not original_name or not new_name_input:
        flash('Faltan datos para renombrar.', 'error')
        return redirect(url_for('admin.dashboard'))

    # Asegurar extensión y nombre seguro
    if not new_name_input.lower().endswith('.pdf'):
        new_name_input += '.pdf'
    new_filename = secure_filename(new_name_input)
    
    registry = load_registry()
    found = False
    
    # Verificar duplicados
    if any(p['filename'] == new_filename for p in registry.get('pdfs', [])) and original_name != new_filename:
        flash('Ya existe un archivo con ese nombre.', 'warning')
        return redirect(url_for('admin.dashboard'))

    for item in registry.get('pdfs', []):
        if item['filename'] == original_name:
            # Renombrar físico
            old_abs_path = os.path.join(UPLOAD_FOLDER, original_name)
            new_abs_path = os.path.join(UPLOAD_FOLDER, new_filename)
            
            try:
                if os.path.exists(old_abs_path):
                    os.rename(old_abs_path, new_abs_path)
                    
                    # Actualizar JSON
                    item['filename'] = new_filename
                    item['path'] = os.path.join('data', 'uploads', new_filename).replace('\\', '/')
                    item['status'] = 'En espera'
                    found = True
                else:
                    flash('El archivo físico original no existe.', 'error')
            except Exception as e:
                print(f"Error renombrando: {e}")
                flash('Error del sistema al renombrar.', 'error')
            break
            
    if found:
        save_registry(registry)
        flash(f'Renombrado a "{new_filename}".', 'success')
    else:
        flash('No se encontró el registro.', 'error')

    return redirect(url_for('admin.dashboard'))

# ==========================================
# 6. GESTIÓN DE URLS (AGREGAR, BORRAR, EDITAR)
# ==========================================

@admin_bp.route('/add_url', methods=['POST'])
@login_required
def add_url():
    url = request.form.get('url')
    name = request.form.get('name') 
    
    if url and name:
        registry = load_registry()
        if 'urls' not in registry: registry['urls'] = []

        if not any(u['url'] == url for u in registry['urls']):
            registry['urls'].append({
                "name": name,
                "url": url,
                "status": "En espera"
            })
            save_registry(registry)
            flash('URL agregada.', 'success')
        else:
            flash('Esa URL ya está registrada.', 'warning')
            
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_url', methods=['POST'])
@login_required
def delete_url():
    url_to_delete = request.form.get('url')
    registry = load_registry()
    
    registry['urls'] = [u for u in registry.get('urls', []) if u['url'] != url_to_delete]
    save_registry(registry)
    flash('Enlace eliminado.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/edit_url', methods=['POST'])
@login_required
def edit_url():
    original_url = request.form.get('original_url')
    new_name = request.form.get('name')
    new_url = request.form.get('url')
    
    registry = load_registry()
    found = False
    
    for item in registry.get('urls', []):
        if item['url'] == original_url:
            item['name'] = new_name
            item['url'] = new_url
            item['status'] = 'En espera'
            found = True
            break
            
    if found:
        save_registry(registry)
        flash('Enlace actualizado.', 'success')
    else:
        flash('Error al editar.', 'error')
    return redirect(url_for('admin.dashboard'))

# ==========================================
# 7. ENTRENAMIENTO IA
# ==========================================

@admin_bp.route('/train_stream')
@login_required
def train_stream():
    """
    Ruta que devuelve un flujo de eventos (Server-Sent Events).
    El navegador se conecta aquí y recibe texto línea por línea.
    """
    registry = load_registry()
    
    # Obtenemos el generador
    generador = actualizar_base_datos_completa(registry)
    
    # Retornamos una respuesta de tipo streaming
    return Response(stream_with_context(generador), mimetype='text/event-stream')

@admin_bp.route('/train_complete', methods=['POST'])
@login_required
def train_complete():
    """
    Ruta para finalizar el proceso y actualizar estados en JSON.
    Se llama vía AJAX cuando el streaming termina.
    """
    registry = load_registry()
    
    # Actualizamos estados a 'Activo'
    if 'pdfs' in registry:
        for item in registry['pdfs']: item['status'] = 'Activo'
    for item in registry.get('urls', []): item['status'] = 'Activo'
        
    save_registry(registry)
    return {"status": "ok", "message": "Estados actualizados"}
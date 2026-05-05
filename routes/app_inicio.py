from flask import Blueprint, render_template

# Crear un Blueprint
inicio_bp = Blueprint('inicio', __name__)

@inicio_bp.route('/')
def index():
    # Renderiza la plantilla 'inicio.html' y le pasa la página activa
    return render_template('inicio.html', active_page='inicio')
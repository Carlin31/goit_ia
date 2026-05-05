from flask import Blueprint, render_template

# Crear un Blueprint
informacion_bp = Blueprint('informacion', __name__)

@informacion_bp.route('/informacion')
def info():
    return render_template('informacion.html', active_page='informacion')
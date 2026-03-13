from flask import Blueprint, render_template

# Crear un Blueprint
privacidad_bp = Blueprint('privacidad', __name__)

@privacidad_bp.route('/privacidad')
def privacidad():
    return render_template('privacidad.html') # No necesita página activa
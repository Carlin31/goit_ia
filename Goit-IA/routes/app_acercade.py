from flask import Blueprint, render_template

# Crear un Blueprint
acercade_bp = Blueprint('acercade', __name__)

@acercade_bp.route('/acerca-de')
def acerca_de():
    return render_template('acerca_de_nosotros.html', active_page='acerca_de')
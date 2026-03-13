import os
from flask import Flask
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar Blueprints existentes
from routes.app_inicio import inicio_bp
from routes.app_chatbot import chatbot_bp
from routes.app_informacion import informacion_bp
from routes.app_acercade import acercade_bp
from routes.app_privacidad import privacidad_bp
from routes.app_admin import admin_bp

app = Flask(__name__)

# Configuración de seguridad para sesiones
app.secret_key = os.getenv("SECRET_KEY", "clave-por-defecto-insegura")

# Registrar Blueprints
app.register_blueprint(inicio_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(informacion_bp)
app.register_blueprint(acercade_bp)
app.register_blueprint(privacidad_bp)
app.register_blueprint(admin_bp) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
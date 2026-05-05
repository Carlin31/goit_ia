from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import sys
import os
import re

# Configuración de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
template_dir = os.path.join(project_root, 'templates')
logic_dir = os.path.join(project_root, 'logic') 
models_dir = os.path.join(project_root, 'models')
data_dir_chroma = os.path.join(project_root, 'data', 'chroma_db_web')

if project_root not in sys.path:
    sys.path.append(project_root)

# --- IMPORTS DE BASE DE DATOS (MongoDB) ---
from database import faq_collection, insert_faq, update_faq  # ← reemplaza SessionLocal y FAQ

# Imports de lógica
from models import modelo_knn 
from models import modelo_llm
modelo_llm.CHROMA_PATH = data_dir_chroma
from logic.seleccion_modelo import SelectorDeModelo

from logic.access_tracker import registrar_acceso

chatbot_bp = Blueprint('chatbot', __name__, template_folder=template_dir)

selector = None
try:
    selector = SelectorDeModelo(usar_knn=True, usar_llm=True)
except Exception as e:
    print(f"Error al iniciar selector: {e}")


# --- FUNCIÓN PARA GUARDAR EN BASE DE DATOS (MongoDB) ---
def guardar_faq_db(pregunta, respuesta):
    """
    Busca si la pregunta ya existe.
    - Si EXISTE: Actualiza la respuesta.
    - Si NO EXISTE: Crea un documento nuevo.
    """
    try:
        # Buscar si ya existe la pregunta
        registro_existente = faq_collection.find_one({"pregunta": pregunta})

        if registro_existente:
            print(f"🔄 Pregunta existente encontrada. Actualizando respuesta...")
            update_faq(pregunta, respuesta)
        else:
            print(f"✅ Nueva pregunta detectada. Guardando...")
            insert_faq(pregunta, respuesta)

        # Recargar el modelo KNN para que aprenda el cambio
        try:
            modelo_knn.inicializar_knn()
        except Exception as e:
            print(f"⚠️ Error recargando KNN: {e}")

    except Exception as e:
        print(f"❌ Error en DB: {e}")


# --- RUTA PRINCIPAL (VISTA) ---
@chatbot_bp.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')


# --- RUTA CHAT ---
@chatbot_bp.route('/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        return redirect(url_for('chatbot.chatbot'))

    data = request.json
    user_input = data.get("message")
    mode = data.get("mode", "normal")
    
    if not user_input:
        return jsonify({"reply": "Por favor escribe algo."})

    forzar_llm = (mode == 'regenerate')

    respuesta_limpia, fuente = selector.responder(user_input, forzar_llm=forzar_llm)

    if "LLM" in fuente:
        pregunta_usuario = user_input.strip()
        guardar_faq_db(pregunta_usuario, respuesta_limpia)

    return jsonify({
        "reply": respuesta_limpia,
        "model": fuente
    })


# --- RUTA: REGISTRO DE ACCESOS ---
@chatbot_bp.route('/api/register_access', methods=['POST'])
def register_access():
    data = request.json
    programa = data.get('programa')
    
    if not programa:
        return jsonify({"status": "error", "message": "Programa no seleccionado"}), 400

    if request.headers.getlist("X-Forwarded-For"):
        user_ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        user_ip = request.remote_addr
        
    user_agent = request.headers.get('User-Agent')

    try:
        registrar_acceso(programa, user_ip, user_agent)
        return jsonify({"status": "success", "message": "Access logged"})
    except Exception as e:
        print(f"Error logging access: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
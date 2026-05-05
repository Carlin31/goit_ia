from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import sys
import os
import re

# Configuración de rutas
current_dir   = os.path.dirname(os.path.abspath(__file__))
project_root  = os.path.dirname(current_dir)
template_dir  = os.path.join(project_root, 'templates')
logic_dir     = os.path.join(project_root, 'logic')
models_dir    = os.path.join(project_root, 'models')
data_dir_chroma = os.path.join(project_root, 'data', 'chroma_db_web')

if project_root not in sys.path:
    sys.path.append(project_root)

# --- IMPORTS DE BASE DE DATOS (MongoDB) ---
from database import faq_collection, insert_faq, update_faq

# --- IMPORTS DE MODELOS ---
from models import modelo_knn
from models import modelo_llm
modelo_llm.CHROMA_PATH = data_dir_chroma
from logic.seleccion_modelo import SelectorDeModelo

# --- IMPORTS DE LÓGICA ---
from logic.access_tracker import registrar_acceso, registrar_pregunta

chatbot_bp = Blueprint('chatbot', __name__, template_folder=template_dir)

# Regex de validación de matrícula: S + exactamente 8 dígitos = 9 chars
MATRICULA_REGEX = re.compile(r'^[Ss]\d{8}$')

selector = None
try:
    selector = SelectorDeModelo(usar_knn=True, usar_llm=True)
except Exception as e:
    print(f"Error al iniciar selector: {e}")


# ──────────────────────────────────────────────────────────────
# GUARDAR EN FAQ (MongoDB)
# ──────────────────────────────────────────────────────────────

def guardar_faq_db(pregunta: str, respuesta: str) -> None:
    """Inserta o actualiza una FAQ no bloqueada; después recarga el modelo KNN."""
    try:
        registro_existente = faq_collection.find_one({"pregunta": pregunta})
        if registro_existente:
            # No sobreescribir si está bloqueada
            if registro_existente.get('bloqueado', False):
                return
            update_faq(pregunta, respuesta)
        else:
            insert_faq(pregunta, respuesta)

        try:
            modelo_knn.inicializar_knn()
        except Exception as e:
            print(f"⚠️ Error recargando KNN: {e}")

    except Exception as e:
        print(f"❌ Error en DB FAQ: {e}")


# ──────────────────────────────────────────────────────────────
# VISTAS
# ──────────────────────────────────────────────────────────────

@chatbot_bp.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')


# ──────────────────────────────────────────────────────────────
# RUTA CHAT
# ──────────────────────────────────────────────────────────────

@chatbot_bp.route('/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        return redirect(url_for('chatbot.chatbot'))

    data       = request.json
    user_input = data.get("message", "").strip()
    mode       = data.get("mode", "normal")
    matricula  = data.get("matricula", "").strip().upper()
    programa   = data.get("programa", "").strip()
    history_raw = data.get("history", [])

    if not user_input:
        return jsonify({"reply": "Por favor escribe algo."})

    # Formatear historial como texto para el LLM
    # Se espera una lista de {role: 'user'|'assistant', content: '...'}
    historial_texto = ""
    if isinstance(history_raw, list) and history_raw:
        lineas = []
        for entrada in history_raw[-8:]:   # máximo 4 intercambios (8 turnos)
            if not isinstance(entrada, dict):
                continue
            rol     = entrada.get("role", "")
            content = str(entrada.get("content", "")).strip()
            if not content:
                continue
            if rol == "user":
                lineas.append(f"Usuario: {content}")
            elif rol == "assistant":
                lineas.append(f"Asistente: {content}")
        historial_texto = "\n".join(lineas)

    forzar_llm = (mode == 'regenerate')

    # selector.responder retorna (respuesta, fuente, bloqueado)
    respuesta_limpia, fuente, bloqueado = selector.responder(
        user_input, historial=historial_texto, forzar_llm=forzar_llm
    )

    # Guardar en FAQ cuando responde el LLM (nunca si está bloqueado)
    if "LLM" in fuente and not bloqueado:
        guardar_faq_db(user_input, respuesta_limpia)

    # Registrar la pregunta asociada a la matrícula
    try:
        registrar_pregunta(
            matricula = matricula,
            programa  = programa,
            pregunta  = user_input,
            respuesta = respuesta_limpia,
            modelo    = fuente,
        )
    except Exception as e:
        print(f"⚠️ Error registrando pregunta: {e}")

    return jsonify({
        "reply":    respuesta_limpia,
        "model":    fuente,
        "bloqueado": bloqueado,
    })


# ──────────────────────────────────────────────────────────────
# RUTA REGISTRO DE ACCESO
# ──────────────────────────────────────────────────────────────

@chatbot_bp.route('/api/register_access', methods=['POST'])
def register_access():
    data      = request.json
    programa  = data.get('programa', '').strip()
    matricula = data.get('matricula', '').strip().upper()

    if not programa:
        return jsonify({"status": "error", "message": "Programa no seleccionado"}), 400

    # Validar formato de matrícula en el servidor también
    if matricula and not MATRICULA_REGEX.match(matricula):
        return jsonify({"status": "error", "message": "Formato de matrícula inválido"}), 400

    if request.headers.getlist("X-Forwarded-For"):
        user_ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        user_ip = request.remote_addr

    user_agent = request.headers.get('User-Agent', '')

    try:
        registrar_acceso(programa, user_ip, user_agent, matricula)
        return jsonify({"status": "success", "message": "Access logged"})
    except Exception as e:
        print(f"Error logging access: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

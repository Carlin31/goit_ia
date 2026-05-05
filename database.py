# database.py
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN ---
MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME", "goit_local")

if not MONGODB_URL:
    raise ValueError("❌ Error: No se ha definido MONGODB_URL en el archivo .env")

# Cliente MongoDB (síncrono, compatible con Flask)
client = MongoClient(MONGODB_URL)
db = client[DB_NAME]

# --- COLECCIONES ---
faq_collection: Collection          = db["faq"]
access_log_collection: Collection   = db["access_log"]
chat_logs_collection: Collection    = db["chat_logs"]


def init_db():
    """Crea índices para optimizar búsquedas."""
    print("🔄 Inicializando colecciones e índices en MongoDB...")

    faq_collection.create_index("pregunta", unique=False)

    access_log_collection.create_index("fecha")
    access_log_collection.create_index("ip")
    access_log_collection.create_index("matricula")

    chat_logs_collection.create_index("matricula")
    chat_logs_collection.create_index([("fecha", DESCENDING), ("hora", DESCENDING)])

    print("✅ MongoDB inicializado correctamente.")


# ──────────────────────────────────────────────
# FUNCIONES FAQ
# ──────────────────────────────────────────────

def get_all_faq() -> list[dict]:
    """Retorna todas las FAQs sin _id (uso interno del modelo KNN)."""
    return list(faq_collection.find({}, {"_id": 0}))

def get_all_faq_admin() -> list[dict]:
    """Retorna todas las FAQs con id como string y campo bloqueado (uso del panel admin)."""
    docs = list(faq_collection.find({}))
    result = []
    for doc in docs:
        doc['id'] = str(doc.pop('_id'))
        doc.setdefault('bloqueado', False)
        result.append(doc)
    return result

def insert_faq(pregunta: str, respuesta: str) -> None:
    faq_collection.insert_one({"pregunta": pregunta, "respuesta": respuesta, "bloqueado": False})

def update_faq(pregunta: str, nueva_respuesta: str) -> None:
    faq_collection.update_one(
        {"pregunta": pregunta},
        {"$set": {"respuesta": nueva_respuesta}}
    )

def update_faq_by_id(faq_id: str, pregunta: str, respuesta: str) -> bool:
    """Actualiza pregunta y respuesta de una FAQ identificada por su ID."""
    result = faq_collection.update_one(
        {"_id": ObjectId(faq_id)},
        {"$set": {"pregunta": pregunta, "respuesta": respuesta}}
    )
    return result.modified_count > 0

def delete_faq(pregunta: str) -> None:
    faq_collection.delete_one({"pregunta": pregunta})

def delete_faq_by_id(faq_id: str) -> bool:
    """Elimina una FAQ por su ID. Retorna True si se eliminó."""
    result = faq_collection.delete_one({"_id": ObjectId(faq_id)})
    return result.deleted_count > 0

def toggle_faq_block(faq_id: str) -> bool:
    """Alterna el estado de bloqueo de una FAQ. Retorna el nuevo estado."""
    doc = faq_collection.find_one({"_id": ObjectId(faq_id)}, {"bloqueado": 1})
    if not doc:
        raise ValueError("FAQ no encontrada")
    new_status = not doc.get('bloqueado', False)
    faq_collection.update_one(
        {"_id": ObjectId(faq_id)},
        {"$set": {"bloqueado": new_status}}
    )
    return new_status


# ──────────────────────────────────────────────
# FUNCIONES ACCESS LOG
# ──────────────────────────────────────────────

def insert_access_log(dia: str, fecha: str, hora: str,
                      programa: str, dispositivo: str,
                      ip: str, matricula: str = "") -> None:
    """Registra un acceso. El campo matricula es opcional para compatibilidad."""
    access_log_collection.insert_one({
        "dia":        dia,
        "fecha":      fecha,
        "hora":       hora,
        "programa":   programa,
        "dispositivo": dispositivo,
        "ip":         ip,
        "matricula":  matricula,
    })

def get_all_access_logs() -> list[dict]:
    return list(access_log_collection.find(
        {}, {"_id": 0}
    ).sort([("fecha", DESCENDING), ("hora", DESCENDING)]))


# ──────────────────────────────────────────────
# FUNCIONES CHAT LOGS
# ──────────────────────────────────────────────

def insert_chat_log(matricula: str, programa: str,
                    pregunta: str, respuesta: str,
                    modelo: str, fecha: str, hora: str) -> None:
    """Guarda una pregunta/respuesta asociada a la matrícula del alumno."""
    chat_logs_collection.insert_one({
        "matricula": matricula,
        "programa":  programa,
        "pregunta":  pregunta,
        "respuesta": respuesta,
        "modelo":    modelo,
        "fecha":     fecha,
        "hora":      hora,
    })

def get_all_chat_logs(limit: int = 500) -> list[dict]:
    """Retorna los registros más recientes de chat (máx. 500 por defecto)."""
    return list(
        chat_logs_collection
        .find({}, {"_id": 0})
        .sort([("fecha", DESCENDING), ("hora", DESCENDING)])
        .limit(limit)
    )

def get_chat_logs_by_matricula(matricula: str) -> list[dict]:
    """Retorna todos los registros de una matrícula específica."""
    return list(
        chat_logs_collection
        .find({"matricula": matricula}, {"_id": 0})
        .sort([("fecha", DESCENDING), ("hora", DESCENDING)])
    )

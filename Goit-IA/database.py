# database.py
from pymongo import MongoClient
from pymongo.collection import Collection
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

# --- COLECCIONES (equivalente a las tablas) ---
faq_collection: Collection = db["faq"]
access_log_collection: Collection = db["access_log"]

def init_db():
    """
    En MongoDB las colecciones se crean automáticamente al insertar.
    Esta función crea índices para optimizar las búsquedas.
    """
    print("🔄 Inicializando colecciones e índices en MongoDB...")

    # Índice único en FAQ para evitar preguntas duplicadas
    faq_collection.create_index("pregunta", unique=False)

    # Índices en access_log para consultas rápidas por fecha/IP
    access_log_collection.create_index("fecha")
    access_log_collection.create_index("ip")

    print("✅ MongoDB inicializado correctamente.")


# --- FUNCIONES AUXILIARES FAQ ---

def get_all_faq() -> list[dict]:
    """Retorna todas las FAQ como lista de dicts."""
    return list(faq_collection.find({}, {"_id": 0}))

def insert_faq(pregunta: str, respuesta: str) -> None:
    """Inserta una nueva FAQ."""
    faq_collection.insert_one({"pregunta": pregunta, "respuesta": respuesta})

def update_faq(pregunta: str, nueva_respuesta: str) -> None:
    """Actualiza la respuesta de una FAQ existente."""
    faq_collection.update_one(
        {"pregunta": pregunta},
        {"$set": {"respuesta": nueva_respuesta}}
    )

def delete_faq(pregunta: str) -> None:
    """Elimina una FAQ por su pregunta."""
    faq_collection.delete_one({"pregunta": pregunta})


# --- FUNCIONES AUXILIARES ACCESS LOG ---

def insert_access_log(dia: str, fecha: str, hora: str,
                      programa: str, dispositivo: str, ip: str) -> None:
    """Registra un acceso en el log."""
    access_log_collection.insert_one({
        "dia": dia,
        "fecha": fecha,
        "hora": hora,
        "programa": programa,
        "dispositivo": dispositivo,
        "ip": ip
    })

def get_all_access_logs() -> list[dict]:
    """Retorna todos los registros de acceso."""
    return list(access_log_collection.find({}, {"_id": 0}))
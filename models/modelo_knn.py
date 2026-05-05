# models/modelo_knn.py
import os
import sys
import numpy as np
from sklearn.neighbors import NearestNeighbors
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# --- IMPORTS DE BASE DE DATOS (MongoDB) ---
from database import faq_collection

# --- MODELO DE EMBEDDINGS VÍA API ---
HF_TOKEN = os.getenv("HF_TOKEN")

print("🔄 Conectando con API de embeddings (HuggingFace)...")
modelo_embedding = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    huggingfacehub_api_token=HF_TOKEN
)
print("✅ API de embeddings lista.")

# --- VARIABLES GLOBALES DEL MODELO KNN ---
knn_model = None
respuestas_knn = []
bloqueado_flags = []


def inicializar_knn():
    """
    Carga los datos desde MongoDB y entrena el modelo KNN.
    Usa n_neighbors=min(3, total) para verificar los mejores candidatos.
    Almacena el flag 'bloqueado' por cada FAQ.
    """
    global knn_model, respuestas_knn, bloqueado_flags

    try:
        print("🔄 Cargando base de conocimiento FAQ desde MongoDB...")

        documentos = list(faq_collection.find(
            {}, {"_id": 0, "pregunta": 1, "respuesta": 1, "bloqueado": 1}
        ))

        if not documentos:
            print("⚠️ La colección FAQ está vacía. El modelo KNN no sabrá nada.")
            knn_model = None
            respuestas_knn = []
            bloqueado_flags = []
            return

        preguntas = [doc['pregunta'] for doc in documentos]
        respuestas_knn = [doc['respuesta'] for doc in documentos]
        bloqueado_flags = [doc.get('bloqueado', False) for doc in documentos]

        # Embeddings vectoriales de todas las preguntas
        X_dataset = np.array(modelo_embedding.embed_documents(preguntas))

        # n_neighbors=min(3, total) permite verificar los top-3 candidatos
        n_vecinos = min(3, len(preguntas))
        knn_model = NearestNeighbors(n_neighbors=n_vecinos, metric='cosine')
        knn_model.fit(X_dataset)

        bloqueadas = sum(1 for b in bloqueado_flags if b)
        print(f"✅ Modelo KNN listo. Total: {len(respuestas_knn)} FAQs "
              f"({bloqueadas} bloqueadas, {n_vecinos} vecinos activos).")

    except Exception as e:
        print(f"⚠️ No se pudo inicializar KNN. Usando solo LLM. Detalle: {e}")
        knn_model = None


# Carga inicial al importar el módulo
inicializar_knn()


def obtener_respuesta_knn(pregunta_usuario):
    """
    Busca la FAQ más similar usando embeddings semánticos.

    Retorna una tupla (respuesta, distancia_coseno, bloqueado):
    - respuesta: texto de la FAQ más cercana, o None si no hay modelo.
    - distancia_coseno: 0.0 = idéntico, 1.0 = completamente diferente.
    - bloqueado: True si la FAQ tiene respuesta bloqueada (siempre fija).
    """
    global knn_model, respuestas_knn, bloqueado_flags

    if not knn_model:
        return None, 1.0, False

    try:
        X_usuario = np.array(modelo_embedding.embed_query(pregunta_usuario)).reshape(1, -1)

        distancias, indices = knn_model.kneighbors(X_usuario)

        # El índice [0][0] siempre es el vecino más cercano
        indice_mejor = indices[0][0]
        distancia_mejor = distancias[0][0]

        respuesta = respuestas_knn[indice_mejor]
        bloqueado = bloqueado_flags[indice_mejor] if bloqueado_flags else False

        print(f"[KNN] Distancia coseno: {distancia_mejor:.4f} | Bloqueado: {bloqueado}")

        return respuesta, distancia_mejor, bloqueado

    except Exception as e:
        print(f"Error en predicción KNN: {e}")
        return None, 1.0, False

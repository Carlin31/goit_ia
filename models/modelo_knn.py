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
# Sin descarga local — usa HuggingFace API con HF_TOKEN
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


def inicializar_knn():
    """
    Carga los datos desde MongoDB y entrena (o re-entrena) el modelo KNN
    usando embeddings vía API de HuggingFace.
    """
    global knn_model, respuestas_knn

    try:
        print("🔄 Cargando base de conocimiento FAQ desde MongoDB...")

        documentos = list(faq_collection.find({}, {"_id": 0, "pregunta": 1, "respuesta": 1}))

        if not documentos:
            print("⚠️ Advertencia: La colección FAQ está vacía. El modelo KNN no sabrá nada.")
            return

        preguntas = [doc['pregunta'] for doc in documentos]
        respuestas_knn = [doc['respuesta'] for doc in documentos]

        # Convertir preguntas a embeddings vía API
        X_dataset = np.array(modelo_embedding.embed_documents(preguntas))

        # Entrenar KNN con métrica coseno sobre los embeddings
        knn_model = NearestNeighbors(n_neighbors=1, metric='cosine')
        knn_model.fit(X_dataset)

        print(f"✅ Modelo KNN semántico listo. Total conocimientos: {len(respuestas_knn)}")

    except Exception as e:
        print(f"⚠️ Advertencia KNN: No se pudo inicializar. Usando solo LLM. Detalle: {e}")


# Carga inicial al importar el módulo
inicializar_knn()


def obtener_respuesta_knn(pregunta_usuario):
    """
    Busca en el modelo KNN usando embeddings semánticos vía API.
    Retorna la respuesta más cercana y su distancia coseno.
    Distancia cercana a 0 = muy similar, cercana a 1 = muy diferente.
    """
    global knn_model, respuestas_knn

    if not knn_model:
        return None, 1.0

    try:
        # Convertir pregunta del usuario a embedding vía API
        X_usuario = np.array(modelo_embedding.embed_query(pregunta_usuario)).reshape(1, -1)

        distancias, indices = knn_model.kneighbors(X_usuario)

        indice_respuesta = indices[0][0]
        distancia = distancias[0][0]
        respuesta = respuestas_knn[indice_respuesta]

        return respuesta, distancia

    except Exception as e:
        print(f"Error en predicción KNN: {e}")
        return None, 1.0
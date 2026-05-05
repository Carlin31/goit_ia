# --- modelo_llm.py ---
import os
from operator import itemgetter
from dotenv import load_dotenv
import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# --- CONFIGURACIÓN ---
MODELO_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODELO_GROQ = "openai/gpt-oss-120b"

# --- CLAVES ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")

if not GROQ_API_KEY:
    raise ValueError("❌ Error: No se encontró la GROQ_API_KEY en el archivo .env")
if not CHROMA_API_KEY:
    raise ValueError("❌ Error: No se encontró la CHROMA_API_KEY en el archivo .env")


def obtener_cadena_rag():

    # Conectar a Chroma Cloud
    chroma_client = chromadb.CloudClient(
        api_key=CHROMA_API_KEY,
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE
    )

    # Verificar si la colección existe
    colecciones = [c.name for c in chroma_client.list_collections()]
    if "goit_vectores" not in colecciones:
        print("⚠️ La colección 'goit_vectores' no existe en Chroma Cloud. Entrena primero desde el panel admin.")
        return None

    # Embeddings vía API de HuggingFace
    embedding_function = HuggingFaceEndpointEmbeddings(
        model=MODELO_EMBEDDING,
        huggingfacehub_api_token=HF_TOKEN
    )

    # Conectar vectorstore a Chroma Cloud
    vectorstore = Chroma(
        client=chroma_client,
        collection_name="goit_vectores",
        embedding_function=embedding_function
    )

    # MMR (Maximal Marginal Relevance): recupera resultados diversos y relevantes.
    # fetch_k=20 candidatos → selecciona los k=6 más variados (lambda_mult controla relevancia vs diversidad).
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 20, "lambda_mult": 0.7}
    )

    template = """Eres Goit-IA, el asistente virtual oficial de la Universidad Veracruzana (UV), especializado en responder preguntas a partir de los documentos institucionales que tienes disponibles.

=== HISTORIAL DE LA CONVERSACIÓN ===
{history}

=== INFORMACIÓN EXTRAÍDA DE LOS DOCUMENTOS ===
{context}

=== PREGUNTA ACTUAL DEL USUARIO ===
{question}

=== REGLAS QUE DEBES SEGUIR SIN EXCEPCIÓN ===

REGLA 1 - FUENTE EXCLUSIVA:
Responde ÚNICAMENTE con información que esté presente en los fragmentos de documentos mostrados arriba.
NO uses conocimiento externo, NO inventes datos, NO supongas información que no aparezca en los documentos.

REGLA 2 - USO DEL HISTORIAL:
Si el historial contiene mensajes anteriores relevantes para la pregunta actual, úsalos para dar continuidad y coherencia a la respuesta. Evita respuestas aisladas; construye una conversación fluida y natural.

REGLA 3 - CUANDO SÍ HAY INFORMACIÓN EN LOS DOCUMENTOS:
Responde directamente con la información encontrada. Sé claro, directo y amable.
Usa guiones (-) para listas. Evita asteriscos (*) y símbolos especiales.
Responde siempre en español, con tono formal pero cercano.

REGLA 4 - CUANDO NO HAY INFORMACIÓN SUFICIENTE EN LOS DOCUMENTOS:
Si los fragmentos recuperados no contienen información relevante para responder la pregunta, responde EXACTAMENTE en este orden:

Primero — Indica que no encontraste información:
Explica con claridad que los documentos disponibles no contienen información suficiente sobre ese tema específico.

Segundo — Sugiere reformular la pregunta:
Invita al usuario a intentar preguntar de otra forma o con palabras diferentes para que puedas ayudarle mejor.

Tercero — Ofrece un ejemplo orientativo (opcional pero recomendado):
Si es posible, proporciona un ejemplo concreto de cómo podría reformular su pregunta dentro del contexto de la Universidad Veracruzana.

Ejemplo de respuesta cuando no hay información:
"No encontré información sobre ese tema en los documentos disponibles. Intenta reformular tu pregunta; por ejemplo, en lugar de '[pregunta original simplificada]', podrías preguntar: '¿Cuáles son los requisitos para [tema relacionado] en la UV?'"
"""

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatGroq(model=MODELO_GROQ, api_key=GROQ_API_KEY)

    def format_docs(docs):
        partes = []
        for doc in docs:
            fuente = doc.metadata.get('fuente', doc.metadata.get('source', 'documento'))
            partes.append(f"[Fuente: {fuente}]\n{doc.page_content}")
        return "\n\n---\n\n".join(partes)

    rag_chain = (
        {
            "context": itemgetter("question") | retriever | format_docs,
            "question": itemgetter("question"),
            "history": itemgetter("history")
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain

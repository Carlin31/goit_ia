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

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    template = """
    Eres un asistente experto de la Universidad Veracruzana (Goit-IA).
    
    HISTORIAL DE CONVERSACIÓN:
    {history}

    CONTEXTO RECUPERADO DE LA BASE DE DATOS:
    {context}
    
    PREGUNTA ACTUAL DEL USUARIO:
    {question}
    
    INSTRUCCIONES:
    Responde basándote en el contexto y el historial. 
    Si la respuesta no está en el contexto, di "No tengo esa información".
    Sé directo y amable. Evita usar símbolos raros como '*' o '+' para listas, usa guiones o puntos.
    """

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatGroq(model=MODELO_GROQ, api_key=GROQ_API_KEY)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

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
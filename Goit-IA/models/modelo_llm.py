# --- modelo_llm.py ---
import os
from operator import itemgetter
from dotenv import load_dotenv # <--- NUEVA IMPORTACIÓN
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- CARGAR VARIABLES DE ENTORNO ---
# Esto busca el archivo .env y carga las variables
load_dotenv()

# --- CONFIGURACIÓN ---
CHROMA_PATH = "data/chroma_db_web" 
MODELO_EMBEDDING = "nomic-embed-text"
MODELO_GROQ = "openai/gpt-oss-120b"

# Ahora obtenemos la Key desde el entorno de manera segura
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

# Verificación de seguridad (opcional pero recomendada)
if not GROQ_API_KEY:
    raise ValueError("Error: No se encontró la GROQ_API_KEY en el archivo .env")

def obtener_cadena_rag():
    if not os.path.exists(CHROMA_PATH):
        return None 

    embedding_function = OllamaEmbeddings(model=MODELO_EMBEDDING)
    vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Configurar el recuperador
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # Template con Historial
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
    
    # Pasamos la API Key recuperada
    llm = ChatGroq(model=MODELO_GROQ, api_key=GROQ_API_KEY)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Usamos itemgetter para dirigir cada dato a donde corresponde
    rag_chain = (
        {
            # 1. El retriever SOLO recibe la pregunta (texto), NO el historial
            "context": itemgetter("question") | retriever | format_docs,
            
            # 2. Pasamos la pregunta y el historial limpios al prompt
            "question": itemgetter("question"),
            "history": itemgetter("history")
        } 
        | prompt 
        | llm 
        | StrOutputParser()
    )
    
    return rag_chain
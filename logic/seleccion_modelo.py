# --- seleccion_modelo.py ---
from models.modelo_knn import obtener_respuesta_knn
from models.modelo_llm import obtener_cadena_rag

class SelectorDeModelo:
    def __init__(self, usar_knn=True, usar_llm=True, umbral_distancia=0.2):
        self.usar_knn = usar_knn
        self.usar_llm = usar_llm
        self.UMBRAL_DISTANCIA_COSINE = umbral_distancia
        self.rag_chain = None
        
        if self.usar_llm:
            try:
                print("Iniciando y cargando el modelo LLM (RAG)...")
                self.rag_chain = obtener_cadena_rag() 
                print("✅ Modelo LLM listo.")
            except Exception as e:
                print(f"❌ Error LLM: {e}")
                self.usar_llm = False

    def responder(self, pregunta, historial="", forzar_llm=False):
        """
        Lógica híbrida:
        1. Si forzar_llm es True -> Salta KNN y usa LLM directo.
        2. Si no, intenta KNN (Caché semántico).
        3. Si KNN falla o la distancia es alta -> Fallback a LLM.
        """
        
        # 1. Intentar KNN (Solo si NO estamos forzando LLM)
        if self.usar_knn and not forzar_llm:
            respuesta_knn, distancia = obtener_respuesta_knn(pregunta)
            
            # Si hay respuesta y es muy similar (distancia baja)
            if respuesta_knn and distancia <= self.UMBRAL_DISTANCIA_COSINE:
                # Retornamos respuesta de caché
                return respuesta_knn, "KNN (Caché Semántico)"

        # 2. Uso del LLM (RAG)
        # Se ejecuta si forzamos LLM O si KNN no encontró coincidencia
        if self.usar_llm and self.rag_chain:
            try:
                respuesta_llm = self.rag_chain.invoke({
                    "question": pregunta, 
                    "history": historial
                })
                return respuesta_llm, "LLM (RAG Generativo)"
            except Exception as e:
                print(f"Error RAG: {e}")
                return "Error al generar respuesta con IA.", "Error"
        
        return "Lo siento, no tengo información sobre eso.", "Nulo"
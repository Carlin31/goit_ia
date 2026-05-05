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
        Lógica híbrida de selección de modelo:

        1. KNN: busca coincidencia semántica en el caché FAQ.
           - Si la FAQ está BLOQUEADA y la distancia es aceptable → siempre retorna esa respuesta,
             ignorando forzar_llm. La respuesta bloqueada nunca puede ser regenerada.
           - Si la FAQ NO está bloqueada y la distancia es aceptable → retorna solo si no se fuerza LLM.
        2. LLM (RAG): se usa cuando KNN no encuentra coincidencia o se fuerza regeneración.

        Retorna: (respuesta: str, fuente: str, bloqueado: bool)
        """

        # 1. Intentar KNN
        if self.usar_knn:
            respuesta_knn, distancia, bloqueado = obtener_respuesta_knn(pregunta)

            if respuesta_knn and distancia <= self.UMBRAL_DISTANCIA_COSINE:
                if bloqueado:
                    # Respuesta bloqueada: siempre fija, sin importar forzar_llm
                    print(f"[Selector] FAQ BLOQUEADA activada (distancia={distancia:.4f})")
                    return respuesta_knn, "KNN (Bloqueado)", True

                if not forzar_llm:
                    print(f"[Selector] KNN caché activado (distancia={distancia:.4f})")
                    return respuesta_knn, "KNN (Caché Semántico)", False

        # 2. LLM RAG (si KNN no aplica o se fuerza regeneración)
        if self.usar_llm and self.rag_chain:
            try:
                respuesta_llm = self.rag_chain.invoke({
                    "question": pregunta,
                    "history": historial
                })
                return respuesta_llm, "LLM (RAG Generativo)", False
            except Exception as e:
                print(f"Error RAG: {e}")
                return "Error al generar respuesta con IA.", "Error", False

        return "Lo siento, no tengo información sobre eso.", "Nulo", False

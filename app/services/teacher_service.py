"""
AI Teacher Service - Service Layer
Orquesta RAG + LLM para generar feedback educativo (SOLID: SRP + DIP)
"""
from app.models.simulation_state import SimulationState, TeacherResponse
from app.repositories.medical_knowledge_repo import get_repository
from app.llm.ollama_client import OllamaClient
from app.rag.prompts import PromptTemplates
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


class AITeacherService:
    """
    Servicio de IA educativa (Service Layer Pattern)
    Coordina: Retrieval (RAG) → Prompt Building → LLM Query → Response
    """
    
    def __init__(
        self,
        repository=None,  # Dependency Injection
        llm_client=None   # Dependency Injection
    ):
        self.settings = get_settings()
        self.repository = repository or get_repository()
        self.llm_client = llm_client or OllamaClient()
        self.prompt_templates = PromptTemplates()
    
    async def get_educational_feedback(
        self, 
        state: SimulationState
    ) -> TeacherResponse:
        """
        Genera feedback educativo basado en el estado de la simulación
        
        Pipeline:
        1. Construir query de búsqueda
        2. Retrieval de chunks relevantes (RAG)
        3. Construir prompt con contexto
        4. Query al LLM
        5. Parsear respuesta
        
        Args:
            state: Estado actual de la simulación
        
        Returns:
            TeacherResponse con explicación, recomendación y fuentes
        """
        logger.info(f"Generando feedback para paciente: {state.edad} años, "
                   f"volumen: {state.volumen_total:.2f} cm³")
        
        # Step 1: Construir query de búsqueda semántica
        search_query = self._build_search_query(state)
        logger.debug(f"Query de búsqueda: {search_query}")
        
        # Step 2: Retrieval (RAG)
        relevant_chunks = self.repository.retrieve_relevant_chunks(
            query=search_query,
            top_k=self.settings.retrieval_top_k
        )
        
        # Step 3: Construir prompt con contexto
        state_dict = state.model_dump()
        state_dict["estadio_aproximado"] = state.estadio_aproximado
        
        prompt = self.prompt_templates.build_teacher_prompt(
            state=state_dict,
            context_chunks=relevant_chunks
        )
        
        # Step 4: Query al LLM (mock o real)
        try:
            llm_response = self.llm_client.query(prompt)
        except Exception as e:
            logger.error(f"Error al consultar LLM: {e}")
            llm_response = "Error al generar respuesta. Usando fallback educativo."
        
        # Step 5: Parsear respuesta
        response = self._parse_llm_response(
            llm_response=llm_response,
            chunks=relevant_chunks,
            state=state
        )
        
        return response
    
    def _build_search_query(self, state: SimulationState) -> str:
        """
        Construye query optimizada para búsqueda semántica
        
        Estrategia: Combinar contexto clínico + pregunta específica
        """
        query_parts = []
        
        # Contexto del paciente
        query_parts.append(f"paciente {state.edad} años")
        
        if state.es_fumador:
            query_parts.append(f"fumador {state.pack_years} pack-years")
        
        # Estadio tumoral
        query_parts.append(f"{state.estadio_aproximado} NSCLC")
        
        # Tratamiento si está activo
        if state.tratamiento_activo != "ninguno":
            query_parts.append(f"tratamiento {state.tratamiento_activo}")
            if state.volumen_tumor_resistente > 0:
                query_parts.append("resistencia al tratamiento")
        
        # Pregunta específica según contexto
        if state.tratamiento_activo != "ninguno":
            query_parts.append("guías NCCN respuesta terapéutica")
        else:
            query_parts.append("opciones terapéuticas recomendadas")
        
        query = " ".join(query_parts)
        return query
    
    def _parse_llm_response(
        self, 
        llm_response: str, 
        chunks: list[dict],
        state: SimulationState
    ) -> TeacherResponse:
        """
        Parsea respuesta del LLM en formato estructurado
        
        Extrae:
        - Explicación (texto principal)
        - Recomendación (si está delimitada)
        - Fuentes (de los chunks recuperados)
        - Advertencia educativa
        """
        # Extraer secciones (si el LLM las formateó correctamente)
        explicacion = ""
        recomendacion = ""
        
        if "**Explicación:**" in llm_response:
            parts = llm_response.split("**Recomendación Educativa:**")
            explicacion = parts[0].replace("**Explicación:**", "").replace("**Explicación del Estado Actual:**", "").strip()
            if len(parts) > 1:
                recomendacion_parts = parts[1].split("**Disclaimer:**")
                recomendacion = recomendacion_parts[0].strip()
        else:
            # Fallback: toda la respuesta es explicación
            explicacion = llm_response.strip()
            recomendacion = "Consultar guías NCCN actualizadas para recomendaciones específicas."
        
        # Extraer fuentes de los chunks
        fuentes = list(set([
            chunk.get("metadata", {}).get("source", "Base de conocimiento médico")
            for chunk in chunks
        ]))
        
        # Advertencia educativa (siempre incluida)
        advertencia = (
            "⚠️ ADVERTENCIA EDUCATIVA: Este es un simulador con fines de enseñanza. "
            "Las decisiones clínicas reales requieren evaluación completa, biopsia, "
            "estadificación TNM, análisis molecular, y seguimiento por oncólogo certificado."
        )
        
        return TeacherResponse(
            explicacion=explicacion or "Análisis en progreso",
            recomendacion=recomendacion or "Consultar directrices clínicas",
            fuentes=fuentes,
            advertencia=advertencia,
            retrieved_chunks=len(chunks),
            llm_model="ollama-mock" if not self.llm_client.check_availability() else "ollama-real"
        )
    
    def get_case_summary(self, caso_id: str) -> dict:
        """
        Retorna resumen educativo de un caso de biblioteca
        (Funcionalidad futura - placeholder)
        """
        return {
            "caso_id": caso_id,
            "summary": "Funcionalidad de resumen de casos en desarrollo"
        }

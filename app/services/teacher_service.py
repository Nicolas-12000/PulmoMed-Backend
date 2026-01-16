"""
AI Teacher Service - Service Layer
Orquesta RAG + LLM para generar feedback educativo (SOLID: SRP + DIP)
OPTIMIZACIONES:
- Caché LRU de respuestas por estado similar (5 min TTL)
- Método async para no bloquear event loop
- Singleton pattern para reutilizar recursos
"""
import hashlib
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import get_settings
from app.llm.interface import LLMClient
from app.llm.ollama_client import OllamaClient
from app.models.simulation_state import SimulationState, TeacherResponse
from app.rag.prompts import PromptTemplates
from app.repositories.medical_knowledge_repo import get_repository
logger = logging.getLogger(__name__)
# Constantes de caché
CACHE_TTL_SECONDS = 300  # 5 minutos
MAX_CACHE_SIZE = 100  # Máximo 100 respuestas cacheadas


class AITeacherService:
    """
    Servicio de IA educativa (Service Layer Pattern)
    Coordina: Retrieval (RAG) → Prompt Building → LLM Query → Response
    """
    def __init__(
        self,
        repository=None,  # Dependency Injection
        llm_client: Optional[LLMClient] = None,  # Dependency Injection
    ) -> None:
        self.settings = get_settings()
        self.repository = repository or get_repository()
        self.llm_client: LLMClient = llm_client or OllamaClient()
        self.prompt_templates = PromptTemplates()

        # Caché de respuestas para evitar recomputar (optimización VR)
        self._response_cache: Dict[str, Tuple[TeacherResponse, float]] = {}

    def _get_cache_key(self, state: SimulationState) -> str:
        """Genera key de caché basada en estado clínicamente relevante.

        Solo cachea por parámetros que realmente afectan la respuesta:
        - Estadio aproximado
        - Tratamiento activo
        - Rango de pack-years (agrupado en decenas)
        - Si hay resistencia tumoral
        """
        has_resistance = state.resistant_tumor_volume > 0.1
        pack_years_bucket = int(state.pack_years / 10) * 10  # 0, 10, 20, 30...

        key_data = f"{state.approx_stage}_{state.active_treatment}_{pack_years_bucket}_{has_resistance}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]

    def _get_cached_response(self, cache_key: str) -> Optional[TeacherResponse]:
        """Retorna respuesta cacheada si existe y no ha expirado."""
        if cache_key in self._response_cache:
            response, timestamp = self._response_cache[cache_key]
            if time.time() - timestamp < CACHE_TTL_SECONDS:
                logger.info(f"📦 Cache HIT para key {cache_key}")
                return response
            else:
                # Expirado, eliminar
                del self._response_cache[cache_key]
        return None

    def _cache_response(self, cache_key: str, response: TeacherResponse) -> None:
        """Guarda respuesta en caché con timestamp."""
        # Limpiar caché si está lleno
        if len(self._response_cache) >= MAX_CACHE_SIZE:
            # Eliminar entrada más antigua
            oldest_key = min(self._response_cache, key=lambda k: self._response_cache[k][1])
            del self._response_cache[oldest_key]

        self._response_cache[cache_key] = (response, time.time())
        logger.debug(f"📦 Cache STORE para key {cache_key}")

    # --- Safety / RAG helpers ---
    def _is_malicious(self, text: str) -> bool:
        """Basic check for potentially dangerous/malicious prompts.

        This is intentionally simple: it prevents obvious unsafe instructions
        from being sent to the LLM. For production, use a safety library.
        """
        banned = [
            "rm -rf",
            "shutdown",
            "exec",
            "execute",
            "curl",
            "nc ",
            "reverse shell",
            "bomb",
            "kill ",
            "exploit",
            "malware",
        ]
        lower = text.lower()
        return any(b in lower for b in banned)

    def _filter_and_rerank_chunks(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank chunks by their returned 'distance' and filter by threshold.

        Uses `distance` returned by Chroma: lower is better. Keeps only
        chunks with distance < settings.rerank_distance_threshold.
        """
        if not chunks:
            return []

        threshold = self.settings.rerank_distance_threshold
        # Keep chunks that have numeric distance and are below threshold
        filtered = [c for c in chunks if isinstance(c.get("distance"), (int, float)) and c.get("distance") < threshold]
        # If none pass the threshold, return empty to signal insufficient grounding
        if not filtered:
            return []

        # Sort ascending (smaller distance = more relevant)
        filtered.sort(key=lambda c: float(c.get("distance", 1.0)))
        return filtered

    async def get_educational_feedback(self, state: SimulationState) -> TeacherResponse:
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
        logger.info(
            f"Generando feedback para paciente: {state.age} años, "
            f"volumen: {state.total_volume:.2f} cm³"
        )

        # OPTIMIZACIÓN: Verificar caché primero
        cache_key = self._get_cache_key(state)
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            return cached

        # Step 1: Construir query de búsqueda semántica
        search_query = self._build_search_query(state)
        logger.debug(f"Query de búsqueda: {search_query}")

        # Step 2: Retrieval (RAG)
        relevant_chunks = self.repository.retrieve_relevant_chunks(
            query=search_query, top_k=self.settings.retrieval_top_k
        )

        # Rerank and filter chunks by distance threshold for grounding
        relevant_chunks = self._filter_and_rerank_chunks(search_query, relevant_chunks)

        # If no chunks pass the grounding threshold, return safe insufficient-info response
        if not relevant_chunks:
            return TeacherResponse(
                explanation=(
                    "No dispongo de información suficiente en la base de conocimiento "
                    "para responder con fundamento."
                ),
                recommendation="No hay datos suficientes para recomendar una acción.",
                sources=[],
                warning=(
                    "⚠️ No hay suficiente información en la base de conocimiento "
                    "para proporcionar una respuesta fundamentada."
                ),
                retrieved_chunks=0,
                llm_model="none",
            )

        # Step 3: Construir prompt con contexto
        # The PromptTemplates expect Spanish keys (edad, es_fumador, etc.).
        # Map the English-named SimulationState fields into the Spanish keys.
        state_for_prompt = {
            "edad": state.age,
            "es_fumador": state.is_smoker,
            "pack_years": state.pack_years,
            "dieta": state.diet,
            "volumen_tumor_sensible": state.sensitive_tumor_volume,
            "volumen_tumor_resistente": state.resistant_tumor_volume,
            "estadio_aproximado": state.approx_stage,
            "tratamiento_activo": state.active_treatment,
            "dias_tratamiento": state.treatment_days,
        }

        prompt = self.prompt_templates.build_teacher_prompt(
            state=state_for_prompt, context_chunks=relevant_chunks
        )

        # Step 4: Query al LLM (mock o real)
        # Security: sanitize prompt before sending to LLM
        if self._is_malicious(prompt) or self._is_malicious(search_query):
            return TeacherResponse(
                explanation=(
                    "Solicitud rechazada: el contenido proporcionado parece ser "
                    "potencialmente malicioso o realizar instrucciones peligrosas."
                ),
                recommendation="No puedo procesar solicitudes que contengan instrucciones peligrosas.",
                sources=[],
                warning=(
                    "⚠️ Solicitud rechazada por medidas de seguridad. Proporcione datos clínicos válidos."
                ),
                retrieved_chunks=0,
                llm_model="safety-filter",
            )

        # Send prompt to LLM (ASYNC)
        try:
            llm_response = await self.llm_client.query(prompt)
        except Exception as e:
            logger.error(f"Error al consultar LLM: {e}")
            llm_response = "Error al generar respuesta. Usando fallback educativo."

        # Step 5: Parsear respuesta
        response = self._parse_llm_response(
            llm_response=llm_response, chunks=relevant_chunks, state=state
        )

        # OPTIMIZACIÓN: Guardar en caché para queries similares
        self._cache_response(cache_key, response)

        return response

    def _build_search_query(self, state: SimulationState) -> str:
        """
        Construye query optimizada para búsqueda semántica

        Estrategia: Combinar contexto clínico + pregunta específica
        """
        query_parts = []

        # Contexto del paciente
        query_parts.append(f"paciente {state.age} años")

        if state.is_smoker:
            query_parts.append(f"fumador {state.pack_years} pack-years")

        # Estadio tumoral
        query_parts.append(f"{state.approx_stage} NSCLC")

        # Tratamiento si está activo
        if state.active_treatment != "ninguno":
            query_parts.append(f"tratamiento {state.active_treatment}")
            if state.resistant_tumor_volume > 0:
                query_parts.append("resistencia al tratamiento")

        # Pregunta específica según contexto
        if state.active_treatment != "ninguno":
            query_parts.append("guías NCCN respuesta terapéutica")
        else:
            query_parts.append("opciones terapéuticas recomendadas")

        query = " ".join(query_parts)
        return query

    def _parse_llm_response(
        self, llm_response: str, chunks: list[dict], state: SimulationState
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
        explanation = ""
        recommendation = ""

        if "**Explicación:**" in llm_response:
            parts = llm_response.split("**Recomendación Educativa:**")
            explanation = (
                parts[0]
                .replace("**Explicación:**", "")
                .replace("**Explicación del Estado Actual:**", "")
                .strip()
            )
            if len(parts) > 1:
                recommendation_parts = parts[1].split("**Disclaimer:**")
                recommendation = recommendation_parts[0].strip()
        else:
            # Fallback: toda la respuesta es explicación
            explanation = llm_response.strip()
            recommendation = (
                "Consultar guías NCCN actualizadas para recomendaciones específicas."
            )

        # Extraer fuentes de los chunks
        sources = list(
            set(
                [
                    chunk.get("metadata", {}).get(
                        "source", "Base de conocimiento médico"
                    )
                    for chunk in chunks
                ]
            )
        )

        # Advertencia educativa (siempre incluida)
        warning = (
            "⚠️ ADVERTENCIA EDUCATIVA: Este es un simulador con fines de "
            "enseñanza. Las decisiones clínicas reales requieren evaluación "
            "completa, biopsia, estadificación TNM, análisis molecular, y "
            "seguimiento por oncólogo certificado."
        )

        llm_model = (
            "ollama-mock"
            if not self.llm_client.check_availability()
            else "ollama-real"
        )

        # Mapear campos parseados a TeacherResponse
        return TeacherResponse(
            explanation=explanation or "Análisis en progreso",
            recommendation=recommendation or "Consultar directrices clínicas",
            sources=sources,
            warning=warning,
            retrieved_chunks=len(chunks),
            llm_model=llm_model,
        )

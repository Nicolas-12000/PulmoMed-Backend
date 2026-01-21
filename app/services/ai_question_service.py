"""
AI Question Generator Service
Genera preguntas personalizadas usando el profesor IA (RAG + LLM)
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import (
    AIGeneratedQuestion,
    MedicalTopic,
)
from app.services.stats_service import StudentStatsService

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 15
LLM_MAX_RETRIES = 2
LLM_MAX_CONSECUTIVE_FAILURES = 3
LLM_COOLDOWN_SECONDS = 30

# Mapeo de topics a descripciones para el prompt
TOPIC_DESCRIPTIONS = {
    MedicalTopic.TUMOR_STAGING: "estadificación tumoral TNM y clasificación de estadios",
    MedicalTopic.TUMOR_BIOLOGY: "biología tumoral, crecimiento celular y metástasis",
    MedicalTopic.TREATMENT_SURGERY: "tratamiento quirúrgico, lobectomía y resección",
    MedicalTopic.TREATMENT_CHEMO: "quimioterapia, agentes citotóxicos y protocolos",
    MedicalTopic.TREATMENT_RADIO: "radioterapia, dosimetría y efectos secundarios",
    MedicalTopic.TREATMENT_IMMUNO: "inmunoterapia, inhibidores de checkpoint y PD-L1",
    MedicalTopic.DIAGNOSIS: "diagnóstico, técnicas de imagen y biopsia",
    MedicalTopic.RISK_FACTORS: "factores de riesgo, tabaquismo y exposiciones",
    MedicalTopic.PROGNOSIS: "pronóstico, supervivencia y factores predictivos",
    MedicalTopic.ANATOMY: "anatomía pulmonar, lóbulos y segmentos bronquiales",
    MedicalTopic.PHARMACOLOGY: "farmacología oncológica y mecanismos de acción",
    MedicalTopic.PATIENT_CARE: "cuidado del paciente, manejo de síntomas y calidad de vida",
}

DIFFICULTY_DESCRIPTIONS = {
    1: "básica, conceptos fundamentales",
    2: "fácil, aplicación directa de conocimientos",
    3: "intermedia, requiere análisis",
    4: "avanzada, casos clínicos complejos",
    5: "experta, integración de múltiples conceptos",
}

REASON_PROMPTS = {
    "weakness": (
        "El estudiante tiene dificultades con este tema. Genera una pregunta "
        "que ayude a reforzar conceptos básicos de forma clara."
    ),
    "intermediate": (
        "El estudiante está progresando en este tema. Genera una pregunta "
        "que desafíe un poco más para consolidar conocimientos."
    ),
    "forgotten_strength": (
        "El estudiante dominaba este tema pero no lo ha practicado recientemente. "
        "Genera una pregunta de repaso."
    ),
    "strength_refresh": (
        "El estudiante es fuerte en este tema. Genera una pregunta de "
        "mantenimiento."
    ),
    "challenge": (
        "El estudiante domina este tema. Genera una pregunta desafiante "
        "para llevarlo al siguiente nivel."
    ),
    "recent_errors": (
        "El estudiante ha cometido errores recientes aquí. Genera una pregunta "
        "que aborde conceptos que suelen confundirse."
    ),
    "new_topic": (
        "El estudiante no ha visto este tema. Genera una pregunta introductoria."
    ),
    "reinforcement": ("Genera una pregunta de refuerzo general."),
}


class AIQuestionGenerator:
    """
    Genera preguntas personalizadas usando el profesor IA.
    Se integra con el sistema RAG para preguntas basadas en evidencia.
    """

    def __init__(self, db: AsyncSession, llm_client=None, repository=None):
        self.db = db
        self.llm_client = llm_client
        self.repository = repository
        self.stats_service = StudentStatsService(db)
        self._llm_fail_count = 0
        self._llm_last_failure_ts = 0.0

    async def generate_personalized_questions(
        self,
        student_id: UUID,
        attempt_id: Optional[UUID] = None,
        count: int = 4
    ) -> List[AIGeneratedQuestion]:
        """
        Genera 4 preguntas personalizadas basadas en el perfil del estudiante.
        Usa el algoritmo de selección de topics y el LLM para generar contenido.
        """
        # Obtener targets del algoritmo de personalización
        targets = await self.stats_service.get_personalized_question_targets(
            student_id, count
        )

        questions = []
        for topic, reason, difficulty in targets:
            question = await self._generate_single_question(
                student_id=student_id,
                attempt_id=attempt_id,
                topic=topic,
                reason=reason,
                difficulty=difficulty
            )
            if question:
                questions.append(question)

        return questions

    async def generate_topic_questions(
        self,
        student_id: UUID,
        topic: MedicalTopic,
        attempt_id: Optional[UUID] = None,
        count: int = 4,
        reason: str = "reinforcement",
        difficulty: int = 3,
    ) -> List[AIGeneratedQuestion]:
        """Genera preguntas IA forzando un tema específico."""
        questions = []
        for _ in range(count):
            q = await self._generate_single_question(
                student_id=student_id,
                attempt_id=attempt_id,
                topic=topic,
                reason=reason,
                difficulty=difficulty,
            )
            if q:
                questions.append(q)
        return questions

    async def _generate_single_question(
        self,
        student_id: UUID,
        attempt_id: Optional[UUID],
        topic: MedicalTopic,
        reason: str,
        difficulty: int
    ) -> Optional[AIGeneratedQuestion]:
        """Genera una pregunta individual usando LLM"""

        # Construir prompt para el LLM (se integra más abajo)

        # Si no hay LLM disponible, usar pregunta de fallback
        if not self.llm_client:
            return await self._create_fallback_question(
                student_id, attempt_id, topic, reason, difficulty
            )

        # Circuit breaker simple
        now = time.time()
        if (
            self._llm_fail_count >= LLM_MAX_CONSECUTIVE_FAILURES
            and (now - self._llm_last_failure_ts) < LLM_COOLDOWN_SECONDS
        ):
            logger.warning("Circuit breaker activo para LLM; usando fallback")
            return await self._create_fallback_question(
                student_id, attempt_id, topic, reason, difficulty
            )

        try:
            # Obtener contexto RAG si hay repositorio
            context = ""
            if self.repository:
                topic_desc = TOPIC_DESCRIPTIONS.get(topic, topic.value)
                chunks = self.repository.retrieve_relevant_chunks(
                    query=f"pregunta de examen sobre {topic_desc}",
                    top_k=3
                )
                if chunks:
                    context = "\n".join([c.get("content", "") for c in chunks])

            # Llamar al LLM con timeout
            full_prompt = (
                "Eres un profesor de medicina especializado en oncología pulmonar.\n"
                f"{REASON_PROMPTS.get(reason, '')}\n\n"
                "Contexto médico relevante:\n"
                f"{context[:2000] if context else 'No hay contexto adicional.'}\n\n"
                "Genera una pregunta de opción múltiple sobre: "
                f"{TOPIC_DESCRIPTIONS.get(topic, topic.value)}\n"
                "Dificultad: "
                f"{DIFFICULTY_DESCRIPTIONS.get(difficulty, 'intermedia')}\n\n"
                "IMPORTANTE: Responde SOLO con un JSON válido con esta estructura:\n"
                "{\n"
                '    "question": "texto de la pregunta",\n'
                '    "options": ["opción A", "opción B", "opción C", "opción D"],\n'
                '    "correct_index": 0,\n'
                '    "explanation": "explicación educativa de por qué es correcta"\n'
                "}\n"
            )
            response = None
            for attempt in range(1, LLM_MAX_RETRIES + 2):  # intentos totales = retries + 1
                try:
                    response = await asyncio.wait_for(
                        self.llm_client.generate(full_prompt),
                        timeout=LLM_TIMEOUT_SECONDS,
                    )
                    break
                except asyncio.TimeoutError:
                    logger.warning("Timeout LLM intento %s/%s", attempt, LLM_MAX_RETRIES + 1)
                except Exception as e:
                    logger.warning("Error LLM intento %s/%s: %s", attempt, LLM_MAX_RETRIES + 1, e)

            if response is None:
                self._llm_fail_count += 1
                self._llm_last_failure_ts = time.time()
                return await self._create_fallback_question(
                    student_id, attempt_id, topic, reason, difficulty
                )

            # Parsear respuesta JSON
            question_data = self._parse_llm_response(response)
            if not question_data:
                self._llm_fail_count += 1
                self._llm_last_failure_ts = time.time()
                return await self._create_fallback_question(
                    student_id, attempt_id, topic, reason, difficulty
                )

            # Crear registro en BD
            ai_question = AIGeneratedQuestion(
                student_id=student_id,
                attempt_id=attempt_id,
                topic=topic,
                question_text=question_data["question"],
                options=json.dumps(question_data["options"]),
                correct_answer=str(question_data["correct_index"]),
                explanation=question_data.get("explanation", ""),
                generation_reason=reason,
                target_difficulty=difficulty,
            )
            self.db.add(ai_question)
            await self.db.flush()
            await self.db.refresh(ai_question)

            logger.info(f"Pregunta IA generada: {topic.value} ({reason})")
            self._llm_fail_count = 0
            self._llm_last_failure_ts = 0.0
            return ai_question

        except Exception as e:
            logger.error(f"Error generando pregunta IA: {e}")
            self._llm_fail_count += 1
            self._llm_last_failure_ts = time.time()
            return await self._create_fallback_question(
                student_id, attempt_id, topic, reason, difficulty
            )

    def _build_question_prompt(
        self,
        topic: MedicalTopic,
        reason: str,
        difficulty: int
    ) -> str:
        """Construye el prompt para generar la pregunta"""
        topic_desc = TOPIC_DESCRIPTIONS.get(topic, topic.value)
        difficulty_desc = DIFFICULTY_DESCRIPTIONS.get(difficulty, "intermedia")
        reason_guidance = REASON_PROMPTS.get(reason, "")

        return f"""
Tema: {topic_desc}
Dificultad: {difficulty_desc}
Contexto pedagógico: {reason_guidance}
"""

    def _parse_llm_response(self, response: str) -> Optional[Dict]:
        """Parsea la respuesta del LLM a estructura de pregunta"""
        try:
            # Buscar JSON en la respuesta
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                # Validar campos requeridos y tipos básicos
                if not all(k in data for k in ["question", "options", "correct_index"]):
                    return None

                question_text = str(data.get("question", "")).strip()
                options_raw = data.get("options", [])
                if not isinstance(options_raw, list):
                    return None
                options = [str(o).strip() for o in options_raw if str(o).strip()]
                if len(options) < 2:
                    return None

                try:
                    correct_index = int(data.get("correct_index", 0))
                except (TypeError, ValueError):
                    return None
                if correct_index < 0 or correct_index >= len(options):
                    return None

                explanation = str(data.get("explanation", "")).strip()

                return {
                    "question": question_text,
                    "options": options,
                    "correct_index": correct_index,
                    "explanation": explanation,
                }
        except json.JSONDecodeError:
            pass

        return None

    async def _create_fallback_question(
        self,
        student_id: UUID,
        attempt_id: Optional[UUID],
        topic: MedicalTopic,
        reason: str,
        difficulty: int
    ) -> AIGeneratedQuestion:
        """Crea una pregunta de fallback cuando el LLM no está disponible"""

        # Banco de preguntas de fallback por tema
        fallback_questions = {
            MedicalTopic.TUMOR_STAGING: {
                "question": "¿Cuál es el tamaño máximo de un tumor T1 según la clasificación TNM?",
                "options": ["≤ 1 cm", "≤ 2 cm", "≤ 3 cm", "≤ 4 cm"],
                "correct_index": 2,
                "explanation": "Según TNM 8va edición, T1 incluye tumores ≤ 3 cm."
            },
            MedicalTopic.TREATMENT_CHEMO: {
                "question": "¿Cuál es el mecanismo de acción del cisplatino?",
                "options": [
                    "Inhibición de topoisomerasa",
                    "Entrecruzamiento de ADN",
                    "Inhibición de microtúbulos",
                    "Bloqueo de receptores"
                ],
                "correct_index": 1,
                "explanation": "El cisplatino forma aductos con el ADN causando entrecruzamientos."
            },
            MedicalTopic.RISK_FACTORS: {
                "question": "¿Cuántos pack-years se considera alto riesgo para screening de cáncer pulmonar?",
                "options": ["≥ 10", "≥ 20", "≥ 30", "≥ 40"],
                "correct_index": 1,
                "explanation": "Las guías USPSTF recomiendan screening con ≥ 20 pack-years."
            },
        }

        # Obtener pregunta del banco o usar genérica
        default = {
            "question": f"Pregunta sobre {TOPIC_DESCRIPTIONS.get(topic, topic.value)}",
            "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "correct_index": 0,
            "explanation": "Esta es una pregunta de práctica."
        }
        q_data = fallback_questions.get(topic, default)

        ai_question = AIGeneratedQuestion(
            student_id=student_id,
            attempt_id=attempt_id,
            topic=topic,
            question_text=q_data["question"],
            options=json.dumps(q_data["options"]),
            correct_answer=str(q_data["correct_index"]),
            explanation=q_data["explanation"],
            generation_reason=reason,
            target_difficulty=difficulty,
        )
        self.db.add(ai_question)
        await self.db.flush()
        await self.db.refresh(ai_question)

        return ai_question

    async def record_answer(
        self,
        question_id: UUID,
        student_answer: str,
        is_correct: bool
    ) -> AIGeneratedQuestion:
        """Registra la respuesta del estudiante a una pregunta IA"""
        from sqlalchemy import select

        result = await self.db.execute(
            select(AIGeneratedQuestion).where(AIGeneratedQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()

        if question:
            question.was_answered = True
            question.was_correct = is_correct
            question.student_answer = student_answer
            question.answered_at = datetime.utcnow()
            await self.db.flush()

            # Actualizar stats del estudiante
            await self.stats_service.update_stats_after_answer(
                student_id=question.student_id,
                topic_str=question.topic.value,
                is_correct=is_correct,
                difficulty=question.target_difficulty
            )

        return question


def get_ai_question_generator(
    db: AsyncSession,
    llm_client=None,
    repository=None
) -> AIQuestionGenerator:
    """Factory para AIQuestionGenerator"""
    return AIQuestionGenerator(db, llm_client, repository)

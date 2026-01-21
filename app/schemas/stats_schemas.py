"""
Pydantic Schemas for Student Stats
DTOs para estadísticas de desempeño del estudiante
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# MedicalTopic not required here; remove unused import


# =============================================================================
# TOPIC PERFORMANCE SCHEMAS
# =============================================================================

class TopicStatsResponse(BaseModel):
    """Stats de un tema individual (como stat de videojuego)"""
    topic: str
    topic_display: str = ""  # Nombre legible del tema
    mastery_score: float = Field(..., ge=0, le=100)
    accuracy_rate: float = Field(..., ge=0, le=100)
    total_questions: int
    correct_answers: int = 0
    incorrect_answers: int = 0
    current_streak: int
    best_streak: int
    performance_level: str  # "expert", "advanced", "intermediate", etc.
    is_strength: bool
    needs_review: bool
    last_seen: Optional[datetime]
    trend: float  # -1 a 1, indica si mejora o empeora

    model_config = {"from_attributes": True}


class StudentStatsSummary(BaseModel):
    """Resumen completo de stats del estudiante (perfil)"""
    student_id: UUID
    student_name: str = ""
    overall_score: float = Field(..., ge=0, le=100, description="Puntuación global")
    total_questions_answered: int
    total_correct: int
    accuracy_rate: float
    topics_count: int
    strengths_count: int = Field(..., description="Número de puntos fuertes")
    weaknesses_count: int = Field(..., description="Número de puntos débiles")
    needs_review_count: int = Field(..., description="Temas que necesitan repaso")
    topics: List[TopicStatsResponse]

    model_config = {
        "json_schema_extra": {
            "example": {
                "student_id": "123e4567-e89b-12d3-a456-426614174000",
                "student_name": "María García",
                "overall_score": 72.5,
                "total_questions_answered": 150,
                "total_correct": 108,
                "accuracy_rate": 72.0,
                "topics_count": 12,
                "strengths_count": 4,
                "weaknesses_count": 2,
                "needs_review_count": 3,
                "topics": []
            }
        }
    }


# =============================================================================
# CLASS STATS (PROFESSOR VIEW)
# =============================================================================

class StudentInClassStats(BaseModel):
    """Stats de un estudiante para vista del profesor"""
    student_id: UUID
    student_name: str
    student_email: str
    overall_score: float
    total_questions_answered: int
    accuracy_rate: float
    strengths_count: int
    weaknesses_count: int
    topics: List[TopicStatsResponse] = []


class ClassStatsResponse(BaseModel):
    """Stats de toda la clase para el profesor"""
    professor_id: UUID
    total_students: int
    class_average_score: float
    students: List[StudentInClassStats]


# =============================================================================
# AI GENERATED QUESTIONS
# =============================================================================

class AIQuestionResponse(BaseModel):
    """Respuesta de pregunta generada por IA"""
    id: UUID
    topic: str
    topic_display: str = ""
    question_text: str
    options: List[str]  # Parseado de JSON
    generation_reason: str
    reason_display: str = ""  # Descripción legible
    target_difficulty: int = Field(..., ge=1, le=5)

    model_config = {"from_attributes": True}


class AIQuestionWithAnswerResponse(AIQuestionResponse):
    """Pregunta IA con respuesta correcta (para después de responder)"""
    correct_answer: int  # Índice de la respuesta correcta
    explanation: str
    was_correct: Optional[bool]
    student_answer: Optional[str]


class TopicQuizRequest(BaseModel):
    """Solicitud para generar un quiz IA de un tema específico"""
    topic: str
    count: int = Field(4, ge=1, le=10)
    difficulty: int = Field(3, ge=1, le=5)


class TopicQuizResponse(BaseModel):
    """Respuesta con preguntas IA para un tema"""
    topic: str
    questions: List[AIQuestionResponse]
    summary: str = "Quiz IA generado"


class PersonalizedQuestionsResponse(BaseModel):
    """Set de preguntas personalizadas para el estudiante"""
    student_id: UUID
    attempt_id: Optional[UUID]
    generation_summary: str  # Explicación de por qué se eligieron estos temas
    questions: List[AIQuestionResponse]


class AnswerAIQuestionRequest(BaseModel):
    """Request para responder una pregunta IA"""
    question_id: UUID
    selected_option: int = Field(..., ge=0, le=3)


class AnswerAIQuestionResponse(BaseModel):
    """Resultado de responder pregunta IA"""
    question_id: UUID
    is_correct: bool
    correct_answer: int
    explanation: str
    mastery_change: float  # Cuánto cambió el mastery score
    new_mastery_score: float


# =============================================================================
# TOPIC ENUM INFO
# =============================================================================

class TopicInfo(BaseModel):
    """Información sobre un tema médico"""
    code: str
    name: str
    description: str


TOPIC_DISPLAY_NAMES = {
    "tumor_staging": "Estadificación Tumoral",
    "tumor_biology": "Biología Tumoral",
    "treatment_surgery": "Tratamiento Quirúrgico",
    "treatment_chemo": "Quimioterapia",
    "treatment_radio": "Radioterapia",
    "treatment_immuno": "Inmunoterapia",
    "diagnosis": "Diagnóstico",
    "risk_factors": "Factores de Riesgo",
    "prognosis": "Pronóstico",
    "anatomy": "Anatomía Pulmonar",
    "pharmacology": "Farmacología",
    "patient_care": "Cuidado del Paciente",
}

REASON_DISPLAY_NAMES = {
    "weakness": "Área a mejorar",
    "intermediate": "En progreso",
    "forgotten_strength": "Repaso de fortaleza",
    "strength_refresh": "Mantenimiento",
    "challenge": "Desafío avanzado",
    "recent_errors": "Refuerzo por errores",
    "new_topic": "Tema nuevo",
    "reinforcement": "Refuerzo general",
}


def enrich_topic_stats(stats: dict) -> TopicStatsResponse:
    """Enriquece stats con nombres legibles"""
    stats["topic_display"] = TOPIC_DISPLAY_NAMES.get(
        stats.get("topic", ""), stats.get("topic", "")
    )
    return TopicStatsResponse(**stats)

"""
Pydantic Schemas for Exams
DTOs para requests/responses de exámenes
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.db_models import AttemptStatus, ExamStatus, ExamType, QuestionType


# =============================================================================
# QUESTION SCHEMAS
# =============================================================================

class QuestionCreate(BaseModel):
    """Request para crear una pregunta"""
    question_type: QuestionType
    text: str = Field(..., min_length=10)
    points: float = Field(default=1.0, ge=0)
    order: int = 0
    options: Optional[str] = None  # JSON string: ["A", "B", "C", "D"]
    correct_answer: Optional[str] = None
    topic: Optional[str] = None
    difficulty: int = Field(default=1, ge=1, le=5)

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_type": "multiple_choice",
                "text": "¿Cuál es el estadío tumoral si el diámetro es de 4cm?",
                "points": 2.0,
                "options": '["Estadío IA", "Estadío IB", "Estadío IIA", "Estadío IIB"]',
                "correct_answer": "1",
                "topic": "tumor_staging",
                "difficulty": 2
            }
        }
    }


class QuestionUpdate(BaseModel):
    """Request para actualizar una pregunta"""
    text: Optional[str] = None
    points: Optional[float] = None
    order: Optional[int] = None
    options: Optional[str] = None
    correct_answer: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[int] = None


class QuestionResponse(BaseModel):
    """Response de pregunta (para profesor, incluye respuesta correcta)"""
    id: UUID
    question_type: QuestionType
    text: str
    points: float
    order: int
    options: Optional[str]
    correct_answer: Optional[str]
    topic: Optional[str]
    difficulty: int
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionStudentResponse(BaseModel):
    """Response de pregunta (para estudiante, sin respuesta correcta)"""
    id: UUID
    question_type: QuestionType
    text: str
    points: float
    order: int
    options: Optional[str]
    topic: Optional[str]
    difficulty: int

    model_config = {"from_attributes": True}


# =============================================================================
# EXAM SCHEMAS
# =============================================================================

class ExamCreate(BaseModel):
    """Request para crear un examen"""
    title: str = Field(..., min_length=5, max_length=255)
    description: Optional[str] = None
    course_id: Optional[UUID] = Field(
        default=None,
        description="ID del curso al que pertenece el examen. Si es None, es un examen privado del profesor."
    )
    exam_type: ExamType = Field(
        default=ExamType.MODULE_EVAL,
        description="Tipo de examen: mini_quiz (5-10), module_eval (15-25), full_exam (30-50)"
    )
    time_limit_minutes: Optional[int] = Field(
        default=None, ge=5,
        description="Límite de tiempo en minutos. Si es None, usa el sugerido por tipo"
    )
    passing_score: float = Field(default=60.0, ge=0, le=100)
    max_attempts: int = Field(default=1, ge=1)
    shuffle_questions: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Evaluación - Estadificación Tumoral",
                "description": "Examen sobre clasificación TNM y estadios",
                "course_id": "123e4567-e89b-12d3-a456-426614174000",
                "exam_type": "module_eval",
                "time_limit_minutes": 30,
                "passing_score": 70.0,
                "max_attempts": 2
            }
        }
    }


class ExamUpdate(BaseModel):
    """Request para actualizar un examen"""
    title: Optional[str] = None
    description: Optional[str] = None
    course_id: Optional[UUID] = None  # Puede reasignarse a otro curso
    exam_type: Optional[ExamType] = None
    time_limit_minutes: Optional[int] = None
    passing_score: Optional[float] = None
    max_attempts: Optional[int] = None
    shuffle_questions: Optional[bool] = None
    status: Optional[ExamStatus] = None


class ExamResponse(BaseModel):
    """Response de examen"""
    id: UUID
    title: str
    description: Optional[str]
    course_id: Optional[UUID] = None  # ID del curso (None si es privado)
    course_name: Optional[str] = None  # Nombre del curso para display
    exam_type: ExamType
    exam_type_display: str = ""  # Nombre legible del tipo
    status: ExamStatus
    time_limit_minutes: Optional[int]
    passing_score: float
    max_attempts: int
    shuffle_questions: bool
    creator_id: UUID
    question_count: int = 0
    min_questions: int = 0  # Mínimo según tipo
    max_questions: int = 0  # Máximo según tipo
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ExamDetailResponse(ExamResponse):
    """Response de examen con preguntas (para profesor)"""
    questions: List[QuestionResponse] = []


class ExamStudentResponse(BaseModel):
    """Response de examen para estudiante (sin respuestas correctas)"""
    id: UUID
    title: str
    description: Optional[str]
    time_limit_minutes: Optional[int]
    passing_score: float
    question_count: int
    questions: List[QuestionStudentResponse] = []

    model_config = {"from_attributes": True}


# =============================================================================
# ANSWER SCHEMAS
# =============================================================================

class AnswerSubmit(BaseModel):
    """Request para enviar una respuesta"""
    question_id: UUID
    answer_text: Optional[str] = None
    selected_option: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_id": "123e4567-e89b-12d3-a456-426614174000",
                "selected_option": 1
            }
        }
    }


class AnswerResponse(BaseModel):
    """Response de respuesta"""
    id: UUID
    question_id: UUID
    answer_text: Optional[str]
    selected_option: Optional[int]
    is_correct: Optional[bool]
    points_earned: Optional[float]
    feedback: Optional[str]
    answered_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# EXAM ATTEMPT SCHEMAS
# =============================================================================

class AttemptStartResponse(BaseModel):
    """Response al iniciar un intento de examen"""
    attempt_id: UUID
    exam: ExamStudentResponse
    started_at: datetime
    time_remaining_minutes: Optional[int]


class AttemptSubmitRequest(BaseModel):
    """Request para enviar examen completo"""
    answers: List[AnswerSubmit]


class AttemptResultResponse(BaseModel):
    """Response con resultado del examen"""
    attempt_id: UUID
    exam_id: UUID
    exam_title: str
    status: AttemptStatus
    score: Optional[float]
    total_points: Optional[float]
    earned_points: Optional[float]
    passed: Optional[bool]
    passing_score: float
    started_at: datetime
    submitted_at: Optional[datetime]
    answers: List[AnswerResponse] = []

    model_config = {"from_attributes": True}


class AttemptListResponse(BaseModel):
    """Response con lista de intentos del estudiante"""
    exam_id: UUID
    exam_title: str
    attempts: List[AttemptResultResponse]
    remaining_attempts: int

"""
Exam Endpoints - /exams/*
Endpoints para gestión de exámenes por profesores
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_endpoint import get_current_active_professor, get_current_user
from app.core.database import get_db
from app.models.db_models import Exam, ExamStatus, ExamType, User
from app.schemas.auth_schemas import MessageResponse
from app.schemas.exam_schemas import (
    AttemptResultResponse,
    AttemptStartResponse,
    AttemptSubmitRequest,
    ExamCreate,
    ExamDetailResponse,
    ExamResponse,
    ExamStudentResponse,
    ExamUpdate,
    QuestionCreate,
    QuestionResponse,
    QuestionStudentResponse,
    QuestionUpdate,
)
from app.services.exam_service import ExamService
from app.models.db_models import EXAM_TYPE_LIMITS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exams", tags=["Exámenes"])

# Nombres legibles para tipos de examen
EXAM_TYPE_DISPLAY = {
    "mini_quiz": "Mini Quiz (5-10 preguntas)",
    "module_eval": "Evaluación de Módulo (15-25 preguntas)",
    "full_exam": "Examen Completo (30-50 preguntas)",
    "ai_personalized": "Quiz Personalizado IA (4 preguntas)",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_exam_or_404(
    exam_id: UUID,
    service: ExamService
) -> Exam:
    """Obtiene un examen o lanza 404 (DRY helper)"""
    exam = await service.get_exam(exam_id)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado"
        )
    return exam


def verify_exam_ownership(
    exam,
    current_user: User,
    action: str = "acceder a"
) -> None:
    """Verifica que el usuario sea dueño del examen o admin (DRY helper)"""
    if exam.creator_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permiso para {action} este examen"
        )


def validate_publish_limits(
    exam,
    question_count: int
) -> None:
    """Valida que el número de preguntas esté en los límites del tipo de examen"""
    limits = EXAM_TYPE_LIMITS.get(exam.exam_type, {"min": 1, "max": 100})

    if question_count < limits["min"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El examen tipo '{exam.exam_type.value}' requiere mínimo "
                   f"{limits['min']} preguntas. Tienes {question_count}."
        )
    if question_count > limits["max"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El examen tipo '{exam.exam_type.value}' permite máximo "
                   f"{limits['max']} preguntas. Tienes {question_count}."
        )


def exam_to_response(exam, question_count: int = 0) -> ExamResponse:
    """Convierte Exam a ExamResponse"""
    # Obtener límites según tipo de examen
    limits = EXAM_TYPE_LIMITS.get(exam.exam_type, {"min": 1, "max": 100})

    # Obtener nombre del curso si existe
    course_name = None
    if exam.course_id and hasattr(exam, 'course') and exam.course:
        course_name = exam.course.name

    return ExamResponse(
        id=exam.id,
        title=exam.title,
        description=exam.description,
        course_id=exam.course_id,
        course_name=course_name,
        exam_type=exam.exam_type,
        exam_type_display=EXAM_TYPE_DISPLAY.get(exam.exam_type.value, exam.exam_type.value),
        status=exam.status,
        time_limit_minutes=exam.time_limit_minutes or limits.get("time_suggested"),
        passing_score=exam.passing_score,
        max_attempts=exam.max_attempts,
        shuffle_questions=exam.shuffle_questions,
        creator_id=exam.creator_id,
        question_count=question_count or len(exam.questions) if hasattr(exam, 'questions') else 0,
        min_questions=limits.get("min", 1),
        max_questions=limits.get("max", 100),
        created_at=exam.created_at,
        updated_at=exam.updated_at,
        published_at=exam.published_at,
    )


# =============================================================================
# PROFESSOR ENDPOINTS - EXAM CRUD
# =============================================================================

@router.post(
    "/",
    response_model=ExamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear examen (profesor)"
)
async def create_exam(
    request: ExamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """
    Crea un nuevo examen en estado borrador.
    Solo profesores y admins pueden crear exámenes.
    """
    service = ExamService(db)
    exam = await service.create_exam(request, current_user)
    return exam_to_response(exam)


@router.get(
    "/my-exams",
    response_model=List[ExamResponse],
    summary="Listar mis exámenes (profesor)"
)
async def list_my_exams(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Lista todos los exámenes creados por el profesor actual."""
    service = ExamService(db)
    exams = await service.get_exams_by_creator(current_user.id, limit=limit, offset=offset)

    result = []
    for exam in exams:
        count = await service.get_exam_question_count(exam.id)
        result.append(exam_to_response(exam, count))

    return result


@router.get(
    "/{exam_id}",
    response_model=ExamDetailResponse,
    summary="Obtener examen con preguntas (profesor)"
)
async def get_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """
    Obtiene un examen con todas sus preguntas y respuestas correctas.
    Solo el creador del examen puede verlo en detalle.
    """
    service = ExamService(db)
    exam = await get_exam_or_404(exam_id, service)
    verify_exam_ownership(exam, current_user, "ver")

    response = exam_to_response(exam)
    return ExamDetailResponse(
        **response.model_dump(),
        questions=[QuestionResponse.model_validate(q) for q in exam.questions]
    )


@router.patch(
    "/{exam_id}",
    response_model=ExamResponse,
    summary="Actualizar examen (profesor)"
)
async def update_exam(
    exam_id: UUID,
    request: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Actualiza un examen existente."""
    service = ExamService(db)
    exam = await get_exam_or_404(exam_id, service)
    verify_exam_ownership(exam, current_user, "editar")

    # Validar número de preguntas si se intenta publicar
    if request.status and request.status.value == "published":
        count = await service.get_exam_question_count(exam_id)
        validate_publish_limits(exam, count)

    updated = await service.update_exam(exam, request)
    count = await service.get_exam_question_count(exam_id)
    return exam_to_response(updated, count)


@router.delete(
    "/{exam_id}",
    response_model=MessageResponse,
    summary="Eliminar examen (profesor)"
)
async def delete_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Elimina un examen y todas sus preguntas."""
    service = ExamService(db)
    exam = await get_exam_or_404(exam_id, service)
    verify_exam_ownership(exam, current_user, "eliminar")

    await service.delete_exam(exam)
    return MessageResponse(message="Examen eliminado exitosamente")


# =============================================================================
# PROFESSOR ENDPOINTS - QUESTIONS
# =============================================================================

@router.post(
    "/{exam_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar pregunta (profesor)"
)
async def add_question(
    exam_id: UUID,
    request: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Agrega una nueva pregunta al examen."""
    service = ExamService(db)
    exam = await get_exam_or_404(exam_id, service)
    verify_exam_ownership(exam, current_user, "editar")

    question = await service.add_question(exam, request)
    return QuestionResponse.model_validate(question)


@router.get(
    "/{exam_id}/questions",
    response_model=List[QuestionResponse],
    summary="Listar preguntas (profesor)"
)
async def list_questions(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Lista todas las preguntas de un examen (incluye respuestas correctas)."""
    service = ExamService(db)
    exam = await get_exam_or_404(exam_id, service)
    verify_exam_ownership(exam, current_user, "ver")

    questions = await service.get_exam_questions(exam_id)
    return [QuestionResponse.model_validate(q) for q in questions]


@router.patch(
    "/{exam_id}/questions/{question_id}",
    response_model=QuestionResponse,
    summary="Actualizar pregunta (profesor)"
)
async def update_question(
    exam_id: UUID,
    question_id: UUID,
    request: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Actualiza una pregunta existente."""
    service = ExamService(db)
    question = await service.get_question(question_id)

    if not question or question.exam_id != exam_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada"
        )

    exam = await get_exam_or_404(exam_id, service)
    verify_exam_ownership(exam, current_user, "editar")

    updated = await service.update_question(question, request)
    return QuestionResponse.model_validate(updated)


@router.delete(
    "/{exam_id}/questions/{question_id}",
    response_model=MessageResponse,
    summary="Eliminar pregunta (profesor)"
)
async def delete_question(
    exam_id: UUID,
    question_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Elimina una pregunta del examen."""
    service = ExamService(db)
    question = await service.get_question(question_id)

    if not question or question.exam_id != exam_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada"
        )

    exam = await get_exam_or_404(exam_id, service)
    verify_exam_ownership(exam, current_user, "editar")

    await service.delete_question(question)
    return MessageResponse(message="Pregunta eliminada exitosamente")


# =============================================================================
# STUDENT ENDPOINTS
# =============================================================================

@router.get(
    "/available",
    response_model=List[ExamResponse],
    summary="Listar exámenes disponibles (estudiante)"
)
async def list_available_exams(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos los exámenes publicados disponibles para el estudiante.
    Solo muestra exámenes de cursos donde está inscrito.
    Si no está inscrito en ningún curso, retorna lista vacía.
    """
    from app.services.course_service import CourseService

    course_service = CourseService(db)
    exams = await course_service.get_student_available_exams(
        current_user.id,
        limit=limit,
        offset=offset,
    )

    result = []
    for exam in exams:
        count = len(exam.questions) if exam.questions else 0
        result.append(exam_to_response(exam, count))

    return result


@router.post(
    "/{exam_id}/start",
    response_model=AttemptStartResponse,
    summary="Iniciar examen (estudiante)"
)
async def start_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inicia un intento de examen.
    Retorna el examen con preguntas (sin respuestas correctas).

    El estudiante debe estar inscrito en el curso del examen.
    """
    from app.services.course_service import CourseService

    service = ExamService(db)
    course_service = CourseService(db)
    exam = await service.get_exam(exam_id)

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado"
        )

    if exam.status != ExamStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este examen no está disponible"
        )

    # Verificar que el estudiante esté inscrito en el curso del examen
    if exam.course_id:
        is_enrolled = await course_service.is_student_enrolled_in_exam_course(
            current_user.id, exam
        )
        if not is_enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No estás inscrito en el curso de este examen"
            )
    else:
        # Exámenes sin curso: permitir a cualquier estudiante si son IA personalizadas
        if exam.exam_type != ExamType.AI_PERSONALIZED and exam.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este examen privado solo lo puede usar su creador"
            )

    try:
        attempt = await service.start_attempt(exam, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    questions = await service.get_exam_questions(exam_id)

    return AttemptStartResponse(
        attempt_id=attempt.id,
        exam=ExamStudentResponse(
            id=exam.id,
            title=exam.title,
            description=exam.description,
            time_limit_minutes=exam.time_limit_minutes,
            passing_score=exam.passing_score,
            question_count=len(questions),
            questions=[QuestionStudentResponse.model_validate(q) for q in questions]
        ),
        started_at=attempt.started_at,
        time_remaining_minutes=exam.time_limit_minutes
    )


@router.post(
    "/{exam_id}/attempts/{attempt_id}/submit",
    response_model=AttemptResultResponse,
    summary="Enviar examen (estudiante)"
)
async def submit_exam(
    exam_id: UUID,
    attempt_id: UUID,
    request: AttemptSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envía el examen completo con todas las respuestas.
    Las preguntas objetivas se califican automáticamente.
    """
    service = ExamService(db)
    attempt = await service.get_attempt(attempt_id)

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intento no encontrado"
        )

    if attempt.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este no es tu intento de examen"
        )

    if attempt.exam_id != exam_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El intento no corresponde a este examen"
        )

    if attempt.status.value != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este examen ya fue enviado"
        )

    result = await service.submit_exam(attempt, request.answers)

    return AttemptResultResponse(
        attempt_id=result.id,
        exam_id=result.exam_id,
        exam_title=result.exam.title,
        status=result.status,
        score=result.score,
        total_points=result.total_points,
        earned_points=result.earned_points,
        passed=result.passed,
        passing_score=result.exam.passing_score,
        started_at=result.started_at,
        submitted_at=result.submitted_at,
        answers=[]  # No mostrar respuestas correctas inmediatamente
    )


@router.get(
    "/{exam_id}/my-attempts",
    response_model=List[AttemptResultResponse],
    summary="Ver mis intentos (estudiante)"
)
async def get_my_attempts(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos los intentos del estudiante en un examen."""
    service = ExamService(db)

    exam = await service.get_exam(exam_id)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado"
        )

    attempts = await service.get_student_attempts(exam_id, current_user.id)

    return [
        AttemptResultResponse(
            attempt_id=a.id,
            exam_id=a.exam_id,
            exam_title=exam.title,
            status=a.status,
            score=a.score,
            total_points=a.total_points,
            earned_points=a.earned_points,
            passed=a.passed,
            passing_score=exam.passing_score,
            started_at=a.started_at,
            submitted_at=a.submitted_at,
            answers=[]
        )
        for a in attempts
    ]

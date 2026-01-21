"""
Stats Endpoints - /stats/*
Endpoints para estadísticas de desempeño y preguntas personalizadas
"""

import json
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_endpoint import get_current_active_professor, get_current_user
from app.core.database import get_db
from app.models.db_models import User
from app.api.rate_limiter import rate_limit
from app.schemas.stats_schemas import (
    AnswerAIQuestionRequest,
    AnswerAIQuestionResponse,
    AIQuestionResponse,
    ClassStatsResponse,
    PersonalizedQuestionsResponse,
    REASON_DISPLAY_NAMES,
    StudentInClassStats,
    StudentStatsSummary,
    TOPIC_DISPLAY_NAMES,
    TopicStatsResponse,
    enrich_topic_stats,
    TopicQuizRequest,
    TopicQuizResponse,
)
from app.services.ai_question_service import AIQuestionGenerator
from app.services.stats_service import StudentStatsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["Estadísticas"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def topic_performance_to_response(tp) -> TopicStatsResponse:
    """Convierte TopicPerformance model a TopicStatsResponse (DRY helper)"""
    return TopicStatsResponse(
        topic=tp.topic.value,
        topic_display=TOPIC_DISPLAY_NAMES.get(tp.topic.value, tp.topic.value),
        mastery_score=tp.mastery_score,
        accuracy_rate=tp.accuracy_rate,
        total_questions=tp.total_questions,
        correct_answers=tp.correct_answers,
        incorrect_answers=tp.incorrect_answers,
        current_streak=tp.current_streak,
        best_streak=tp.best_streak,
        performance_level=tp.performance_level,
        is_strength=tp.is_strength,
        needs_review=tp.needs_review,
        last_seen=tp.last_seen,
        trend=tp.trend
    )


# =============================================================================
# STUDENT ENDPOINTS
# =============================================================================

@router.get(
    "/my-stats",
    response_model=StudentStatsSummary,
    summary="Ver mis estadísticas (estudiante)"
)
async def get_my_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene las estadísticas de desempeño del estudiante actual.
    Similar a stats de un videojuego: muestra puntos fuertes, débiles,
    tendencias y progreso por cada tema médico.
    """
    service = StudentStatsService(db)
    summary = await service.get_student_stats_summary(current_user.id)

    # Formatear topics con nombres legibles
    formatted_topics = [enrich_topic_stats(t) for t in summary["topics"]]

    return StudentStatsSummary(
        student_id=current_user.id,
        student_name=current_user.full_name,
        overall_score=summary["overall_score"],
        total_questions_answered=summary["total_questions_answered"],
        total_correct=summary["total_correct"],
        accuracy_rate=summary["accuracy_rate"],
        topics_count=summary["topics_count"],
        strengths_count=summary["strengths_count"],
        weaknesses_count=summary["weaknesses_count"],
        needs_review_count=summary["needs_review_count"],
        topics=formatted_topics
    )


@router.get(
    "/my-strengths",
    response_model=List[TopicStatsResponse],
    summary="Ver mis puntos fuertes"
)
async def get_my_strengths(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista los temas donde el estudiante tiene mejor desempeño."""
    service = StudentStatsService(db)
    all_stats = await service.get_all_student_stats(current_user.id)

    strengths = [
        topic_performance_to_response(s)
        for s in all_stats
        if s.is_strength
    ]

    return sorted(strengths, key=lambda x: x.mastery_score, reverse=True)


@router.get(
    "/my-weaknesses",
    response_model=List[TopicStatsResponse],
    summary="Ver mis áreas a mejorar"
)
async def get_my_weaknesses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista los temas donde el estudiante necesita mejorar."""
    service = StudentStatsService(db)
    all_stats = await service.get_all_student_stats(current_user.id)

    weaknesses = [
        topic_performance_to_response(s)
        for s in all_stats
        if s.needs_review or s.mastery_score < 50
    ]

    return sorted(weaknesses, key=lambda x: x.mastery_score)


@router.post(
    "/ai-quiz",
    response_model=TopicQuizResponse,
    summary="Generar quiz IA por tema (estudiante, sin curso)"
)
async def generate_ai_quiz_by_topic(
    request: TopicQuizRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Genera un quiz IA de `count` preguntas para un tema específico."""
    try:
        from app.models.db_models import MedicalTopic
        topic_enum = MedicalTopic(request.topic)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tema inválido"
        )

    # Obtener LLM client y repository si están disponibles
    llm_client = None
    repository = None

    try:
        from app.repositories.medical_knowledge_repo import get_repository
        repository = get_repository()
    except Exception:
        pass

    try:
        from app.llm.ollama_client import OllamaClient
        llm_client = OllamaClient()
        if not llm_client.check_availability():
            llm_client = None
    except Exception:
        pass

    generator = AIQuestionGenerator(db, llm_client, repository)
    questions = await generator.generate_topic_questions(
        student_id=current_user.id,
        topic=topic_enum,
        count=request.count,
        reason="reinforcement",
        difficulty=request.difficulty,
    )

    formatted_questions = []
    for q in questions:
        try:
            options = json.loads(q.options) if q.options else []
        except json.JSONDecodeError:
            options = []

        formatted_questions.append(AIQuestionResponse(
            id=q.id,
            topic=q.topic.value,
            topic_display=TOPIC_DISPLAY_NAMES.get(q.topic.value, q.topic.value),
            question_text=q.question_text,
            options=options,
            generation_reason=q.generation_reason,
            reason_display=REASON_DISPLAY_NAMES.get(
                q.generation_reason, q.generation_reason
            ),
            target_difficulty=q.target_difficulty
        ))

    return TopicQuizResponse(
        topic=topic_enum.value,
        questions=formatted_questions,
        summary=f"Quiz IA generado para {TOPIC_DISPLAY_NAMES.get(topic_enum.value, topic_enum.value)}"
    )
    service = StudentStatsService(db)
    all_stats = await service.get_all_student_stats(current_user.id)

    weaknesses = [
        topic_performance_to_response(s)
        for s in all_stats
        if s.needs_review or s.mastery_score < 50
    ]

    return sorted(weaknesses, key=lambda x: x.mastery_score)


# =============================================================================
# PERSONALIZED AI QUESTIONS
# =============================================================================

@router.post(
    "/personalized-questions",
    response_model=PersonalizedQuestionsResponse,
    summary="Generar preguntas personalizadas (IA)"
)
async def generate_personalized_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera 4 preguntas personalizadas basadas en el perfil del estudiante.

    El algoritmo selecciona:
    - 1 pregunta sobre punto débil crítico
    - 1 pregunta sobre área intermedia
    - 1 pregunta de repaso de fortaleza olvidada
    - 1 pregunta de desafío avanzado
    """
    # Obtener LLM client y repository si están disponibles
    llm_client = None
    repository = None

    try:
        from app.repositories.medical_knowledge_repo import get_repository
        repository = get_repository()
    except Exception:
        pass

    try:
        from app.llm.ollama_client import OllamaClient
        llm_client = OllamaClient()
        if not llm_client.check_availability():
            llm_client = None
    except Exception:
        pass

    generator = AIQuestionGenerator(db, llm_client, repository)
    # Rate limit por usuario para personalizadas
    await rate_limit(f"ia-personalized:{current_user.id}", limit=5, window_seconds=60)
    questions = await generator.generate_personalized_questions(
        student_id=current_user.id,
        count=4
    )

    # Formatear respuesta
    formatted_questions = []
    for q in questions:
        try:
            options = json.loads(q.options) if q.options else []
        except json.JSONDecodeError:
            options = []

        formatted_questions.append(AIQuestionResponse(
            id=q.id,
            topic=q.topic.value,
            topic_display=TOPIC_DISPLAY_NAMES.get(q.topic.value, q.topic.value),
            question_text=q.question_text,
            options=options,
            generation_reason=q.generation_reason,
            reason_display=REASON_DISPLAY_NAMES.get(
                q.generation_reason, q.generation_reason
            ),
            target_difficulty=q.target_difficulty
        ))

    # Generar resumen de por qué se eligieron estos temas
    reasons = [q.generation_reason for q in questions]
    summary_parts = []
    if "weakness" in reasons or "recent_errors" in reasons:
        summary_parts.append("reforzar áreas débiles")
    if "intermediate" in reasons:
        summary_parts.append("consolidar conocimientos intermedios")
    if "forgotten_strength" in reasons or "strength_refresh" in reasons:
        summary_parts.append("repasar fortalezas")
    if "challenge" in reasons:
        summary_parts.append("desafiarte en áreas dominadas")

    generation_summary = (
        f"Estas preguntas fueron seleccionadas para: {', '.join(summary_parts)}."
        if summary_parts else "Preguntas de práctica general."
    )

    return PersonalizedQuestionsResponse(
        student_id=current_user.id,
        attempt_id=None,
        generation_summary=generation_summary,
        questions=formatted_questions
    )


@router.post(
    "/personalized-questions/{question_id}/answer",
    response_model=AnswerAIQuestionResponse,
    summary="Responder pregunta personalizada"
)
async def answer_personalized_question(
    question_id: UUID,
    request: AnswerAIQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Responde una pregunta generada por IA y actualiza estadísticas.
    Retorna si fue correcta y la explicación educativa.
    """
    from sqlalchemy import select
    from app.models.db_models import AIGeneratedQuestion

    # Verificar que la pregunta existe y pertenece al usuario
    result = await db.execute(
        select(AIGeneratedQuestion).where(
            AIGeneratedQuestion.id == question_id,
            AIGeneratedQuestion.student_id == current_user.id
        )
    )
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada"
        )

    if question.was_answered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta pregunta ya fue respondida"
        )

    # Verificar respuesta
    try:
        correct_index = int(question.correct_answer)
    except (ValueError, TypeError):
        correct_index = 0

    is_correct = request.selected_option == correct_index

    # Obtener mastery score antes
    stats_service = StudentStatsService(db)
    old_stats = await stats_service.get_or_create_topic_stats(
        current_user.id,
        question.topic
    )
    old_mastery = old_stats.mastery_score

    # Registrar respuesta y actualizar stats
    generator = AIQuestionGenerator(db)
    await generator.record_answer(
        question_id=question_id,
        student_answer=str(request.selected_option),
        is_correct=is_correct
    )

    # Obtener nuevo mastery score
    new_stats = await stats_service.get_or_create_topic_stats(
        current_user.id,
        question.topic
    )

    return AnswerAIQuestionResponse(
        question_id=question_id,
        is_correct=is_correct,
        correct_answer=correct_index,
        explanation=question.explanation or "Sin explicación disponible.",
        mastery_change=round(new_stats.mastery_score - old_mastery, 1),
        new_mastery_score=round(new_stats.mastery_score, 1)
    )


# =============================================================================
# PROFESSOR ENDPOINTS
# =============================================================================

@router.get(
    "/class",
    response_model=ClassStatsResponse,
    summary="Ver estadísticas de la clase (profesor)"
)
async def get_class_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """
    Obtiene las estadísticas de todos los estudiantes que han tomado
    exámenes creados por este profesor.
    """
    service = StudentStatsService(db)
    class_stats = await service.get_class_stats(current_user.id)

    # Formatear cada estudiante
    students = []
    for s in class_stats:
        formatted_topics = [enrich_topic_stats(t) for t in s.get("topics", [])]
        students.append(StudentInClassStats(
            student_id=UUID(s["student_id"]),
            student_name=s["student_name"],
            student_email=s["student_email"],
            overall_score=s["overall_score"],
            total_questions_answered=s["total_questions_answered"],
            accuracy_rate=s["accuracy_rate"],
            strengths_count=s["strengths_count"],
            weaknesses_count=s["weaknesses_count"],
            topics=formatted_topics
        ))

    # Calcular promedio de la clase
    class_average = (
        sum(s.overall_score for s in students) / len(students)
        if students else 0
    )

    return ClassStatsResponse(
        professor_id=current_user.id,
        total_students=len(students),
        class_average_score=round(class_average, 1),
        students=students
    )


@router.get(
    "/student/{student_id}",
    response_model=StudentStatsSummary,
    summary="Ver stats de un estudiante (profesor)"
)
async def get_student_stats(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """
    Permite al profesor ver las estadísticas detalladas de un estudiante.
    """
    from sqlalchemy import select
    from app.models.db_models import Exam, ExamAttempt

    # Verificar que el estudiante ha tomado exámenes de este profesor
    result = await db.execute(
        select(ExamAttempt)
        .join(Exam, ExamAttempt.exam_id == Exam.id)
        .where(
            ExamAttempt.student_id == student_id,
            Exam.creator_id == current_user.id
        )
        .limit(1)
    )
    has_attempts = result.scalar_one_or_none()

    if not has_attempts and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver las estadísticas de este estudiante"
        )

    # Obtener info del estudiante
    result = await db.execute(
        select(User).where(User.id == student_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudiante no encontrado"
        )

    service = StudentStatsService(db)
    summary = await service.get_student_stats_summary(student_id)

    formatted_topics = [enrich_topic_stats(t) for t in summary["topics"]]

    return StudentStatsSummary(
        student_id=student_id,
        student_name=student.full_name,
        overall_score=summary["overall_score"],
        total_questions_answered=summary["total_questions_answered"],
        total_correct=summary["total_correct"],
        accuracy_rate=summary["accuracy_rate"],
        topics_count=summary["topics_count"],
        strengths_count=summary["strengths_count"],
        weaknesses_count=summary["weaknesses_count"],
        needs_review_count=summary["needs_review_count"],
        topics=formatted_topics
    )

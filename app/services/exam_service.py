"""
Exam Service - Business Logic
Servicio para gestión de exámenes, preguntas e intentos
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db_models import (
    Answer,
    AttemptStatus,
    Exam,
    ExamAttempt,
    ExamStatus,
    Question,
    User,
)
from app.schemas.exam_schemas import (
    AnswerSubmit,
    ExamCreate,
    ExamUpdate,
    QuestionCreate,
    QuestionUpdate,
)

logger = logging.getLogger(__name__)


class ExamService:
    """Servicio de exámenes (SOLID: Single Responsibility)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # EXAM CRUD
    # =========================================================================

    async def create_exam(self, request: ExamCreate, creator: User) -> Exam:
        """Crea un nuevo examen"""
        exam = Exam(
            title=request.title,
            description=request.description,
            course_id=request.course_id,  # Puede ser None para examen privado
            exam_type=request.exam_type,
            time_limit_minutes=request.time_limit_minutes,
            passing_score=request.passing_score,
            max_attempts=request.max_attempts,
            shuffle_questions=request.shuffle_questions,
            creator_id=creator.id,
            status=ExamStatus.DRAFT,
        )
        self.db.add(exam)
        await self.db.flush()
        await self.db.refresh(exam)
        logger.info(f"Examen creado: {exam.title} por {creator.email}")
        return exam

    async def get_exam(self, exam_id: UUID) -> Optional[Exam]:
        """Obtiene un examen por ID con su curso"""
        result = await self.db.execute(
            select(Exam)
            .options(
                selectinload(Exam.questions),
                selectinload(Exam.course)
            )
            .where(Exam.id == exam_id)
        )
        return result.scalar_one_or_none()

    async def get_exams_by_creator(
        self,
        creator_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Exam]:
        """Lista exámenes creados por un profesor (paginado)"""
        result = await self.db.execute(
            select(Exam)
            .where(Exam.creator_id == creator_id)
            .order_by(Exam.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_published_exams(self) -> List[Exam]:
        """Lista exámenes publicados (para estudiantes)"""
        result = await self.db.execute(
            select(Exam)
            .where(Exam.status == ExamStatus.PUBLISHED)
            .order_by(Exam.published_at.desc())
        )
        return list(result.scalars().all())

    async def update_exam(
        self,
        exam: Exam,
        request: ExamUpdate
    ) -> Exam:
        """Actualiza un examen"""
        update_data = request.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(exam, field, value)

        # Si se publica, registrar fecha
        if request.status == ExamStatus.PUBLISHED and exam.published_at is None:
            exam.published_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(exam)
        return exam

    async def delete_exam(self, exam: Exam) -> None:
        """Elimina un examen (cascade elimina preguntas)"""
        await self.db.delete(exam)
        await self.db.flush()
        logger.info(f"Examen eliminado: {exam.title}")

    # =========================================================================
    # QUESTION CRUD
    # =========================================================================

    async def add_question(
        self,
        exam: Exam,
        request: QuestionCreate
    ) -> Question:
        """Agrega una pregunta a un examen"""
        question = Question(
            exam_id=exam.id,
            question_type=request.question_type,
            text=request.text,
            points=request.points,
            order=request.order,
            options=request.options,
            correct_answer=request.correct_answer,
            topic=request.topic,
            difficulty=request.difficulty,
        )
        self.db.add(question)
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def get_question(self, question_id: UUID) -> Optional[Question]:
        """Obtiene una pregunta por ID"""
        result = await self.db.execute(
            select(Question).where(Question.id == question_id)
        )
        return result.scalar_one_or_none()

    async def update_question(
        self,
        question: Question,
        request: QuestionUpdate
    ) -> Question:
        """Actualiza una pregunta"""
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def delete_question(self, question: Question) -> None:
        """Elimina una pregunta"""
        await self.db.delete(question)
        await self.db.flush()

    async def get_exam_questions(self, exam_id: UUID) -> List[Question]:
        """Obtiene todas las preguntas de un examen"""
        result = await self.db.execute(
            select(Question)
            .where(Question.exam_id == exam_id)
            .order_by(Question.order)
        )
        return list(result.scalars().all())

    # =========================================================================
    # EXAM ATTEMPTS
    # =========================================================================

    async def start_attempt(
        self,
        exam: Exam,
        student: User
    ) -> ExamAttempt:
        """
        Inicia un nuevo intento de examen

        Raises:
            ValueError: Si excedió el máximo de intentos
        """
        # Verificar intentos anteriores
        existing_attempts = await self.get_student_attempts(exam.id, student.id)

        if len(existing_attempts) >= exam.max_attempts:
            raise ValueError(
                f"Has alcanzado el máximo de {exam.max_attempts} intentos"
            )

        # Verificar si hay intentos en progreso
        in_progress = [
            a for a in existing_attempts
            if a.status == AttemptStatus.IN_PROGRESS
        ]
        if in_progress:
            return in_progress[0]  # Retornar intento existente

        attempt = ExamAttempt(
            exam_id=exam.id,
            student_id=student.id,
            status=AttemptStatus.IN_PROGRESS,
        )
        self.db.add(attempt)
        await self.db.flush()
        await self.db.refresh(attempt)

        logger.info(
            f"Intento iniciado: {student.email} en {exam.title}"
        )
        return attempt

    async def get_attempt(self, attempt_id: UUID) -> Optional[ExamAttempt]:
        """Obtiene un intento por ID"""
        result = await self.db.execute(
            select(ExamAttempt)
            .options(
                selectinload(ExamAttempt.answers),
                selectinload(ExamAttempt.exam)
            )
            .where(ExamAttempt.id == attempt_id)
        )
        return result.scalar_one_or_none()

    async def get_student_attempts(
        self,
        exam_id: UUID,
        student_id: UUID
    ) -> List[ExamAttempt]:
        """Lista intentos de un estudiante en un examen"""
        result = await self.db.execute(
            select(ExamAttempt)
            .where(
                ExamAttempt.exam_id == exam_id,
                ExamAttempt.student_id == student_id
            )
            .order_by(ExamAttempt.started_at.desc())
        )
        return list(result.scalars().all())

    async def submit_answer(
        self,
        attempt: ExamAttempt,
        answer_data: AnswerSubmit
    ) -> Answer:
        """Guarda una respuesta a una pregunta"""
        # Verificar si ya existe respuesta para esta pregunta
        result = await self.db.execute(
            select(Answer).where(
                Answer.attempt_id == attempt.id,
                Answer.question_id == answer_data.question_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Actualizar respuesta existente
            existing.answer_text = answer_data.answer_text
            existing.selected_option = answer_data.selected_option
            existing.answered_at = datetime.utcnow()
            await self.db.flush()
            return existing

        # Crear nueva respuesta
        answer = Answer(
            attempt_id=attempt.id,
            question_id=answer_data.question_id,
            answer_text=answer_data.answer_text,
            selected_option=answer_data.selected_option,
        )
        self.db.add(answer)
        await self.db.flush()
        await self.db.refresh(answer)
        return answer

    async def submit_exam(
        self,
        attempt: ExamAttempt,
        answers: List[AnswerSubmit]
    ) -> ExamAttempt:
        """
        Envía el examen completo y calcula la calificación

        Returns:
            ExamAttempt con score calculado
        """
        # Guardar todas las respuestas
        for answer_data in answers:
            await self.submit_answer(attempt, answer_data)

        # Obtener preguntas del examen
        questions = await self.get_exam_questions(attempt.exam_id)
        questions_dict = {q.id: q for q in questions}

        # Calificar automáticamente respuestas objetivas
        total_points = sum(q.points for q in questions)
        earned_points = 0.0

        # Recargar respuestas
        result = await self.db.execute(
            select(Answer).where(Answer.attempt_id == attempt.id)
        )
        attempt_answers = list(result.scalars().all())

        for answer in attempt_answers:
            question = questions_dict.get(answer.question_id)
            if not question:
                continue

            # Calificar según tipo
            if question.question_type.value in ["multiple_choice", "true_false", "ai_generated"]:
                is_correct = self._grade_objective_answer(question, answer)
                answer.is_correct = is_correct
                answer.points_earned = question.points if is_correct else 0.0
                earned_points += answer.points_earned

                # Actualizar estadísticas del estudiante por tema
                if question.topic:
                    await self._update_student_topic_stats(
                        student_id=attempt.student_id,
                        topic=question.topic,
                        is_correct=is_correct,
                        difficulty=question.difficulty
                    )

        # Actualizar intento
        attempt.status = AttemptStatus.SUBMITTED
        attempt.submitted_at = datetime.utcnow()
        attempt.total_points = total_points
        attempt.earned_points = earned_points
        attempt.score = (earned_points / total_points * 100) if total_points > 0 else 0

        # Obtener passing_score del examen
        exam = await self.get_exam(attempt.exam_id)
        attempt.passed = attempt.score >= exam.passing_score

        # Si todas las respuestas son objetivas, marcar como calificado
        has_open_ended = any(
            q.question_type.value == "open_ended" for q in questions
        )
        if not has_open_ended:
            attempt.status = AttemptStatus.GRADED
            attempt.graded_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(attempt)

        logger.info(
            f"Examen enviado: intento {attempt.id}, "
            f"score={attempt.score:.1f}%, passed={attempt.passed}"
        )
        return attempt

    def _grade_objective_answer(
        self,
        question: Question,
        answer: Answer
    ) -> bool:
        """Califica respuesta objetiva (multiple choice/true-false)"""
        if question.correct_answer is None:
            return False

        # Comparar índice seleccionado con respuesta correcta
        if answer.selected_option is not None:
            try:
                correct_index = int(question.correct_answer)
                return answer.selected_option == correct_index
            except ValueError:
                pass

        # Comparar texto
        if answer.answer_text:
            return (
                answer.answer_text.strip().lower() ==
                question.correct_answer.strip().lower()
            )

        return False

    async def get_exam_question_count(self, exam_id: UUID) -> int:
        """Cuenta preguntas de un examen"""
        result = await self.db.execute(
            select(func.count(Question.id))
            .where(Question.exam_id == exam_id)
        )
        return result.scalar() or 0

    async def _update_student_topic_stats(
        self,
        student_id: UUID,
        topic: str,
        is_correct: bool,
        difficulty: int
    ) -> None:
        """Actualiza estadísticas del estudiante después de responder pregunta"""
        try:
            from app.services.stats_service import StudentStatsService
            stats_service = StudentStatsService(self.db)
            await stats_service.update_stats_after_answer(
                student_id=student_id,
                topic_str=topic,
                is_correct=is_correct,
                difficulty=difficulty
            )
        except Exception as e:
            # No fallar el examen si falla la actualización de stats
            logger.warning(f"Error actualizando stats: {e}")


def get_exam_service(db: AsyncSession) -> ExamService:
    """Factory para ExamService (Dependency Injection)"""
    return ExamService(db)

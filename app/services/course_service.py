"""
Course Service - Business Logic
Servicio para gestión de cursos e inscripciones
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db_models import (
    Course,
    CourseEnrollment,
    EnrollmentStatus,
    Exam,
    ExamStatus,
    ExamType,
    User,
    generate_enrollment_code,
)
from app.schemas.course_schemas import CourseCreate, CourseUpdate

logger = logging.getLogger(__name__)


class CourseService:
    """
    Servicio de cursos e inscripciones.

    Reglas de negocio:
    - Solo profesores pueden crear cursos
    - Estudiantes se inscriben con código de 6 caracteres
    - Un estudiante puede estar en múltiples cursos
    - Un profesor puede tener múltiples cursos
    - Exámenes se asignan a cursos específicos
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_unique_code(self, max_attempts: int = 5) -> str:
        """Genera un código de inscripción único con reintentos."""
        for _ in range(max_attempts):
            candidate = generate_enrollment_code()
            existing = await self.get_course_by_code(candidate)
            if not existing:
                return candidate
        raise ValueError("No se pudo generar un código de inscripción único. Intenta nuevamente.")

    # =========================================================================
    # COURSE CRUD
    # =========================================================================

    async def create_course(
        self,
        request: CourseCreate,
        professor: User
    ) -> Course:
        """Crea un nuevo curso"""
        enrollment_code = await self._generate_unique_code()
        course = Course(
            name=request.name,
            description=request.description,
            semester=request.semester,
            max_students=request.max_students,
            professor_id=professor.id,
            enrollment_code=enrollment_code,
        )
        self.db.add(course)
        await self.db.flush()
        await self.db.refresh(course)
        logger.info(f"Curso creado: {course.name} ({course.enrollment_code}) por {professor.email}")
        return course

    async def get_course(self, course_id: UUID) -> Optional[Course]:
        """Obtiene un curso por ID con sus inscripciones"""
        result = await self.db.execute(
            select(Course)
            .options(
                selectinload(Course.enrollments).selectinload(CourseEnrollment.student),
                selectinload(Course.professor)
            )
            .where(Course.id == course_id)
        )
        return result.scalar_one_or_none()

    async def get_course_by_code(self, enrollment_code: str) -> Optional[Course]:
        """Busca un curso por código de inscripción"""
        result = await self.db.execute(
            select(Course)
            .options(selectinload(Course.professor))
            .where(Course.enrollment_code == enrollment_code.upper())
        )
        return result.scalar_one_or_none()

    async def get_professor_courses(
        self,
        professor_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Course]:
        """Lista cursos de un profesor (paginado)"""
        result = await self.db.execute(
            select(Course)
            .options(selectinload(Course.enrollments))
            .where(Course.professor_id == professor_id)
            .order_by(Course.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_course(
        self,
        course: Course,
        request: CourseUpdate
    ) -> Course:
        """Actualiza un curso"""
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        await self.db.flush()
        await self.db.refresh(course)
        return course

    async def delete_course(self, course: Course) -> None:
        """Elimina un curso (cascade elimina inscripciones)"""
        await self.db.delete(course)
        await self.db.flush()
        logger.info(f"Curso eliminado: {course.name}")

    async def regenerate_enrollment_code(self, course: Course) -> Course:
        """Regenera el código de inscripción del curso"""
        course.enrollment_code = await self._generate_unique_code()
        await self.db.flush()
        await self.db.refresh(course)
        logger.info(f"Código regenerado para {course.name}: {course.enrollment_code}")
        return course

    # =========================================================================
    # ENROLLMENT MANAGEMENT
    # =========================================================================

    async def enroll_student(
        self,
        enrollment_code: str,
        student: User
    ) -> CourseEnrollment:
        """
        Inscribe a un estudiante en un curso usando el código.

        Raises:
            ValueError: Si el código es inválido, curso inactivo, o límite alcanzado
        """
        # Buscar curso por código
        course = await self.get_course_by_code(enrollment_code)
        if not course:
            raise ValueError("Código de inscripción inválido")

        if not course.is_active:
            raise ValueError("Este curso no está aceptando inscripciones")

        # Verificar si ya está inscrito
        existing = await self.get_enrollment(course.id, student.id)
        if existing:
            if existing.status == EnrollmentStatus.ACTIVE:
                raise ValueError("Ya estás inscrito en este curso")
            elif existing.status == EnrollmentStatus.INACTIVE:
                # Reactivar inscripción
                existing.status = EnrollmentStatus.ACTIVE
                await self.db.flush()
                return existing

        # Verificar límite de estudiantes
        if course.max_students:
            active_count = await self.get_active_enrollment_count(course.id)
            if active_count >= course.max_students:
                raise ValueError("El curso ha alcanzado el límite de estudiantes")

        # Crear inscripción
        enrollment = CourseEnrollment(
            course_id=course.id,
            student_id=student.id,
            status=EnrollmentStatus.ACTIVE,
        )
        self.db.add(enrollment)
        await self.db.flush()
        await self.db.refresh(enrollment)

        logger.info(f"Estudiante {student.email} inscrito en {course.name}")
        return enrollment

    async def get_enrollment(
        self,
        course_id: UUID,
        student_id: UUID
    ) -> Optional[CourseEnrollment]:
        """Obtiene inscripción de un estudiante en un curso"""
        result = await self.db.execute(
            select(CourseEnrollment)
            .options(
                selectinload(CourseEnrollment.course),
                selectinload(CourseEnrollment.student)
            )
            .where(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.student_id == student_id
            )
        )
        return result.scalar_one_or_none()

    async def get_student_enrollments(
        self,
        student_id: UUID,
        active_only: bool = True
    ) -> List[CourseEnrollment]:
        """Lista inscripciones de un estudiante"""
        query = (
            select(CourseEnrollment)
            .options(
                selectinload(CourseEnrollment.course).selectinload(Course.professor)
            )
            .where(CourseEnrollment.student_id == student_id)
        )
        if active_only:
            query = query.where(CourseEnrollment.status == EnrollmentStatus.ACTIVE)

        result = await self.db.execute(query.order_by(CourseEnrollment.enrolled_at.desc()))
        return list(result.scalars().all())

    async def get_course_enrollments(
        self,
        course_id: UUID,
        status: Optional[EnrollmentStatus] = None
    ) -> List[CourseEnrollment]:
        """Lista inscripciones de un curso"""
        query = (
            select(CourseEnrollment)
            .options(selectinload(CourseEnrollment.student))
            .where(CourseEnrollment.course_id == course_id)
        )
        if status:
            query = query.where(CourseEnrollment.status == status)

        result = await self.db.execute(query.order_by(CourseEnrollment.enrolled_at.desc()))
        return list(result.scalars().all())

    async def get_active_enrollment_count(self, course_id: UUID) -> int:
        """Cuenta inscripciones activas en un curso"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(CourseEnrollment.id))
            .where(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            )
        )
        return result.scalar() or 0

    async def update_enrollment_status(
        self,
        enrollment: CourseEnrollment,
        new_status: EnrollmentStatus
    ) -> CourseEnrollment:
        """Actualiza el estado de una inscripción (profesor)"""
        enrollment.status = new_status
        if new_status == EnrollmentStatus.COMPLETED:
            from datetime import datetime
            enrollment.completed_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(enrollment)
        return enrollment

    async def leave_course(
        self,
        course_id: UUID,
        student_id: UUID
    ) -> None:
        """Estudiante abandona un curso"""
        enrollment = await self.get_enrollment(course_id, student_id)
        if enrollment:
            enrollment.status = EnrollmentStatus.INACTIVE
            await self.db.flush()
            logger.info(f"Estudiante {student_id} abandonó curso {course_id}")

    # =========================================================================
    # COURSE EXAMS
    # =========================================================================

    async def get_course_exams(
        self,
        course_id: UUID,
        published_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Exam]:
        """Obtiene exámenes de un curso (paginado)"""
        query = (
            select(Exam)
            .options(selectinload(Exam.questions))
            .where(Exam.course_id == course_id)
        )
        if published_only:
            query = query.where(Exam.status == ExamStatus.PUBLISHED)

        result = await self.db.execute(
            query.order_by(Exam.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def get_student_available_exams(
        self,
        student_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Exam]:
        """
        Obtiene exámenes disponibles para un estudiante.
        Solo exámenes publicados de cursos donde está inscrito.
        """
        # Obtener IDs de cursos donde está inscrito
        enrolled_courses = await self.get_student_enrollments(student_id, active_only=True)
        course_ids = [e.course_id for e in enrolled_courses]

        queries = []

        # Exámenes de cursos donde está inscrito
        if course_ids:
            queries.append(
                select(Exam)
                .options(selectinload(Exam.questions), selectinload(Exam.course))
                .where(
                    Exam.course_id.in_(course_ids),
                    Exam.status == ExamStatus.PUBLISHED
                )
            )

        # Exámenes IA globales (sin curso) publicados
        queries.append(
            select(Exam)
            .options(selectinload(Exam.questions), selectinload(Exam.course))
            .where(
                Exam.course_id.is_(None),
                Exam.exam_type == ExamType.AI_PERSONALIZED,
                Exam.status == ExamStatus.PUBLISHED
            )
        )

        results: List[Exam] = []
        for query in queries:
            res = await self.db.execute(
                query.order_by(Exam.published_at.desc()).limit(limit).offset(offset)
            )
            results.extend(list(res.scalars().all()))

        return results

    async def is_student_enrolled_in_exam_course(
        self,
        student_id: UUID,
        exam: Exam
    ) -> bool:
        """Verifica si el estudiante está inscrito en el curso del examen"""
        if exam.course_id is None:
            return False  # Examen sin curso, no accesible

        enrollment = await self.get_enrollment(exam.course_id, student_id)
        return enrollment is not None and enrollment.status == EnrollmentStatus.ACTIVE


def get_course_service(db: AsyncSession) -> CourseService:
    """Factory para CourseService (Dependency Injection)"""
    return CourseService(db)

"""
Course Endpoints - /courses/*
Endpoints para gestión de cursos e inscripciones
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_endpoint import get_current_active_professor, get_current_user
from app.core.database import get_db
from app.models.db_models import User
from app.schemas.auth_schemas import MessageResponse
from app.schemas.course_schemas import (
    CourseCreate,
    CourseDetailResponse,
    CourseExamResponse,
    CourseResponse,
    CourseUpdate,
    EnrollmentRequest,
    EnrollmentResponse,
    EnrollmentStatusUpdate,
    StudentCourseResponse,
)
from app.services.course_service import CourseService
from app.api.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["Cursos"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def course_to_response(course, include_code: bool = True) -> CourseResponse:
    """Convierte Course a CourseResponse"""
    return CourseResponse(
        id=course.id,
        name=course.name,
        description=course.description,
        enrollment_code=course.enrollment_code if include_code else "******",
        is_active=course.is_active,
        max_students=course.max_students,
        semester=course.semester,
        professor_id=course.professor_id,
        professor_name=course.professor.full_name if course.professor else "",
        student_count=course.student_count,
        created_at=course.created_at,
    )


def enrollment_to_response(enrollment) -> EnrollmentResponse:
    """Convierte CourseEnrollment a EnrollmentResponse"""
    return EnrollmentResponse(
        id=enrollment.id,
        course_id=enrollment.course_id,
        course_name=enrollment.course.name if enrollment.course else "",
        student_id=enrollment.student_id,
        student_name=enrollment.student.full_name if enrollment.student else "",
        student_email=enrollment.student.email if enrollment.student else "",
        status=enrollment.status,
        enrolled_at=enrollment.enrolled_at,
        completed_at=enrollment.completed_at,
    )


# =============================================================================
# PROFESSOR ENDPOINTS
# =============================================================================

@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear curso (profesor)"
)
async def create_course(
    request: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """
    Crea un nuevo curso. Genera automáticamente un código de inscripción único.
    Solo profesores y admins pueden crear cursos.
    """
    service = CourseService(db)
    try:
        course = await service.create_course(request, current_user)
        # Refrescar para obtener professor relationship
        course = await service.get_course(course.id)
        return course_to_response(course)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/my-courses",
    response_model=List[CourseResponse],
    summary="Listar mis cursos (profesor)"
)
async def list_my_courses(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Lista todos los cursos creados por el profesor actual."""
    service = CourseService(db)
    courses = await service.get_professor_courses(current_user.id, limit=limit, offset=offset)
    # Necesitamos cargar el profesor para cada curso
    result = []
    for course in courses:
        full_course = await service.get_course(course.id)
        result.append(course_to_response(full_course))
    return result


@router.get(
    "/{course_id}",
    response_model=CourseDetailResponse,
    summary="Ver detalle de curso (profesor)"
)
async def get_course_detail(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """
    Obtiene el detalle de un curso incluyendo lista de estudiantes.
    Solo el profesor dueño puede ver el detalle completo.
    """
    service = CourseService(db)
    course = await service.get_course(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )

    if course.professor_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este curso"
        )

    enrollments = await service.get_course_enrollments(course_id)

    return CourseDetailResponse(
        **course_to_response(course).model_dump(),
        students=[enrollment_to_response(e) for e in enrollments]
    )


@router.patch(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Actualizar curso (profesor)"
)
async def update_course(
    course_id: UUID,
    request: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Actualiza la configuración de un curso."""
    service = CourseService(db)
    course = await service.get_course(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )

    if course.professor_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para editar este curso"
        )

    updated = await service.update_course(course, request)
    updated = await service.get_course(updated.id)
    return course_to_response(updated)


@router.post(
    "/{course_id}/regenerate-code",
    response_model=CourseResponse,
    summary="Regenerar código de inscripción (profesor)"
)
async def regenerate_code(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """
    Regenera el código de inscripción del curso.
    Útil si el código fue compartido incorrectamente.
    """
    service = CourseService(db)
    course = await service.get_course(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )

    if course.professor_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este curso"
        )

    try:
        updated = await service.regenerate_enrollment_code(course)
        updated = await service.get_course(updated.id)
        return course_to_response(updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{course_id}",
    response_model=MessageResponse,
    summary="Eliminar curso (profesor)"
)
async def delete_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Elimina un curso y todas sus inscripciones."""
    service = CourseService(db)
    course = await service.get_course(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )

    if course.professor_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este curso"
        )

    await service.delete_course(course)
    return MessageResponse(message="Curso eliminado exitosamente")


# =============================================================================
# PROFESSOR - ENROLLMENT MANAGEMENT
# =============================================================================

@router.patch(
    "/{course_id}/enrollments/{student_id}",
    response_model=EnrollmentResponse,
    summary="Cambiar estado de inscripción (profesor)"
)
async def update_enrollment_status(
    course_id: UUID,
    student_id: UUID,
    request: EnrollmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """
    Permite al profesor cambiar el estado de inscripción de un estudiante.
    Útil para dar de baja, reactivar, o marcar como completado.
    """
    service = CourseService(db)
    course = await service.get_course(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )

    if course.professor_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para gestionar este curso"
        )

    enrollment = await service.get_enrollment(course_id, student_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inscripción no encontrada"
        )

    updated = await service.update_enrollment_status(enrollment, request.status)
    return enrollment_to_response(updated)


@router.get(
    "/{course_id}/exams",
    response_model=List[CourseExamResponse],
    summary="Listar exámenes del curso (profesor)"
)
async def list_course_exams(
    course_id: UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_professor)
):
    """Lista todos los exámenes asignados a un curso."""
    service = CourseService(db)
    course = await service.get_course(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )

    if course.professor_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este curso"
        )

    exams = await service.get_course_exams(course_id, limit=limit, offset=offset)
    return [
        CourseExamResponse(
            id=e.id,
            title=e.title,
            description=e.description,
            exam_type=e.exam_type.value,
            status=e.status.value,
            question_count=len(e.questions) if e.questions else 0,
            time_limit_minutes=e.time_limit_minutes,
            passing_score=e.passing_score,
            max_attempts=e.max_attempts,
            published_at=e.published_at,
        )
        for e in exams
    ]


# =============================================================================
# STUDENT ENDPOINTS
# =============================================================================

@router.post(
    "/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscribirse a un curso (estudiante)"
)
async def enroll_in_course(
    request: EnrollmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inscribe al estudiante en un curso usando el código de inscripción.
    El código es proporcionado por el profesor del curso.
    """
    if current_user.role.value == "professor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los profesores no pueden inscribirse como estudiantes"
        )

    service = CourseService(db)

    # Rate limit para inscripciones por usuario
    await rate_limit(f"enroll:{current_user.id}", limit=5, window_seconds=300)

    try:
        enrollment = await service.enroll_student(
            enrollment_code=request.enrollment_code,
            student=current_user
        )
        # Recargar con relaciones
        enrollment = await service.get_enrollment(enrollment.course_id, enrollment.student_id)
        return enrollment_to_response(enrollment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/my-enrollments",
    response_model=List[StudentCourseResponse],
    summary="Ver mis cursos (estudiante)"
)
async def get_my_enrollments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista los cursos en los que el estudiante está inscrito."""
    service = CourseService(db)
    enrollments = await service.get_student_enrollments(
        current_user.id,
        active_only=False  # Mostrar todos para historial
    )

    return [
        StudentCourseResponse(
            id=e.course.id,
            name=e.course.name,
            description=e.course.description,
            semester=e.course.semester,
            professor_name=e.course.professor.full_name if e.course.professor else "",
            professor_email=e.course.professor.email if e.course.professor else "",
            enrollment_status=e.status,
            enrolled_at=e.enrolled_at,
        )
        for e in enrollments
    ]


@router.post(
    "/{course_id}/leave",
    response_model=MessageResponse,
    summary="Abandonar curso (estudiante)"
)
async def leave_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """El estudiante abandona un curso voluntariamente."""
    service = CourseService(db)

    enrollment = await service.get_enrollment(course_id, current_user.id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No estás inscrito en este curso"
        )

    await service.leave_course(course_id, current_user.id)
    return MessageResponse(message="Has abandonado el curso")


@router.get(
    "/available-exams",
    response_model=List[CourseExamResponse],
    summary="Ver exámenes disponibles (estudiante)"
)
async def get_available_exams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista los exámenes disponibles para el estudiante.
    Solo muestra exámenes publicados de cursos donde está inscrito.

    Si el estudiante no está inscrito en ningún curso,
    retorna lista vacía (solo puede usar preguntas IA personalizadas).
    """
    service = CourseService(db)
    exams = await service.get_student_available_exams(current_user.id)

    return [
        CourseExamResponse(
            id=e.id,
            title=e.title,
            description=e.description,
            exam_type=e.exam_type.value,
            status=e.status.value,
            question_count=len(e.questions) if e.questions else 0,
            time_limit_minutes=e.time_limit_minutes,
            passing_score=e.passing_score,
            max_attempts=e.max_attempts,
            published_at=e.published_at,
        )
        for e in exams
    ]

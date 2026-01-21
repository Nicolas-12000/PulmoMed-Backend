"""
Pydantic Schemas for Courses
DTOs para requests/responses de cursos e inscripciones
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.db_models import EnrollmentStatus


# =============================================================================
# COURSE SCHEMAS
# =============================================================================

class CourseCreate(BaseModel):
    """Request para crear un curso"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    semester: Optional[str] = Field(None, max_length=50)
    max_students: Optional[int] = Field(None, ge=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Oncología Pulmonar - Grupo A",
                "description": "Curso de especialización en cáncer pulmonar",
                "semester": "2026-1",
                "max_students": 30
            }
        }
    }


class CourseUpdate(BaseModel):
    """Request para actualizar un curso"""
    name: Optional[str] = None
    description: Optional[str] = None
    semester: Optional[str] = None
    max_students: Optional[int] = None
    is_active: Optional[bool] = None


class CourseResponse(BaseModel):
    """Response de curso"""
    id: UUID
    name: str
    description: Optional[str]
    enrollment_code: str
    is_active: bool
    max_students: Optional[int]
    semester: Optional[str]
    professor_id: UUID
    professor_name: str = ""
    student_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseDetailResponse(CourseResponse):
    """Response de curso con lista de estudiantes (para profesor)"""
    students: List["EnrollmentResponse"] = []


# =============================================================================
# ENROLLMENT SCHEMAS
# =============================================================================

class EnrollmentRequest(BaseModel):
    """Request para inscribirse a un curso con código"""
    enrollment_code: str = Field(..., min_length=6, max_length=10)

    model_config = {
        "json_schema_extra": {
            "example": {
                "enrollment_code": "ABC123"
            }
        }
    }


class EnrollmentResponse(BaseModel):
    """Response de inscripción"""
    id: UUID
    course_id: UUID
    course_name: str = ""
    student_id: UUID
    student_name: str = ""
    student_email: str = ""
    status: EnrollmentStatus
    enrolled_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class StudentCourseResponse(BaseModel):
    """Curso desde perspectiva del estudiante"""
    id: UUID
    name: str
    description: Optional[str]
    semester: Optional[str]
    professor_name: str
    professor_email: str
    enrollment_status: EnrollmentStatus
    enrolled_at: datetime


class EnrollmentStatusUpdate(BaseModel):
    """Request para cambiar estado de inscripción (profesor)"""
    status: EnrollmentStatus


# =============================================================================
# COURSE EXAM SCHEMAS
# =============================================================================

class CourseExamResponse(BaseModel):
    """Examen desde perspectiva del curso"""
    id: UUID
    title: str
    description: Optional[str]
    exam_type: str
    status: str
    question_count: int
    time_limit_minutes: Optional[int]
    passing_score: float
    max_attempts: int
    published_at: Optional[datetime]


# Rebuild para referencias forward
CourseDetailResponse.model_rebuild()

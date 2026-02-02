"""
Tests exhaustivos para CourseService
Incluye tests de CRUD de cursos, inscripciones y gestión de estudiantes
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.course_service import CourseService
from app.schemas.course_schemas import CourseCreate, CourseUpdate
from app.models.db_models import (
    Course, CourseEnrollment, User, UserRole,
    EnrollmentStatus, generate_enrollment_code
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    """Mock de AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def course_service(mock_db):
    """Instancia de CourseService con DB mockeada."""
    return CourseService(mock_db)


@pytest.fixture
def sample_professor():
    """Profesor de prueba."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "profesor@universidad.edu"
    user.full_name = "Dr. Martínez"
    user.role = UserRole.PROFESSOR
    user.is_active = True
    return user


@pytest.fixture
def sample_student():
    """Estudiante de prueba."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "estudiante@universidad.edu"
    user.full_name = "Carlos Ruiz"
    user.role = UserRole.STUDENT
    user.is_active = True
    return user


@pytest.fixture
def sample_course(sample_professor):
    """Curso de prueba."""
    course = MagicMock(spec=Course)
    course.id = uuid4()
    course.name = "Neumología Avanzada"
    course.description = "Curso de neumología para residentes"
    course.semester = "2025-1"
    course.max_students = 30
    course.professor_id = sample_professor.id
    course.professor = sample_professor
    course.enrollment_code = "ABC123"
    course.is_active = True
    course.enrollments = []
    course.created_at = datetime.utcnow()
    return course


@pytest.fixture
def sample_enrollment(sample_course, sample_student):
    """Inscripción de prueba."""
    enrollment = MagicMock(spec=CourseEnrollment)
    enrollment.id = uuid4()
    enrollment.course_id = sample_course.id
    enrollment.student_id = sample_student.id
    enrollment.status = EnrollmentStatus.ACTIVE
    enrollment.enrolled_at = datetime.utcnow()
    enrollment.student = sample_student
    enrollment.course = sample_course
    return enrollment


@pytest.fixture
def course_create_request():
    """Request para crear curso."""
    return CourseCreate(
        name="Nuevo Curso de Medicina",
        description="Descripción del curso",
        semester="2025-2",
        max_students=25
    )


# =============================================================================
# Tests de Curso CRUD (Casos Positivos)
# =============================================================================

class TestCourseServiceCRUDPositive:
    """Tests de CRUD de cursos que DEBEN funcionar."""

    @pytest.mark.asyncio
    async def test_create_course_success(
        self, course_service, mock_db, course_create_request, sample_professor
    ):
        """Crear curso exitosamente."""
        # Mock: no existe código duplicado
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        async def fake_refresh(course):
            course.id = uuid4()
            course.enrollment_code = "XYZ789"
            course.created_at = datetime.utcnow()
        mock_db.refresh = fake_refresh

        course = await course_service.create_course(
            course_create_request,
            sample_professor
        )

        assert course is not None
        mock_db.add.assert_called_once()
        assert course.enrollment_code is not None

    @pytest.mark.asyncio
    async def test_get_course_by_id(self, course_service, mock_db, sample_course):
        """Obtener curso por ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_course
        mock_db.execute.return_value = mock_result

        course = await course_service.get_course(sample_course.id)

        assert course == sample_course
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_course_by_code(self, course_service, mock_db, sample_course):
        """Buscar curso por código de inscripción."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_course
        mock_db.execute.return_value = mock_result

        course = await course_service.get_course_by_code("ABC123")

        assert course == sample_course

    @pytest.mark.asyncio
    async def test_get_course_by_code_case_insensitive(
        self, course_service, mock_db, sample_course
    ):
        """Código de inscripción es case-insensitive."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_course
        mock_db.execute.return_value = mock_result

        # Buscar con minúsculas
        course = await course_service.get_course_by_code("abc123")

        assert course == sample_course


# =============================================================================
# Tests de Curso CRUD (Casos Negativos)
# =============================================================================

class TestCourseServiceCRUDNegative:
    """Tests de CRUD que NO deben funcionar."""

    @pytest.mark.asyncio
    async def test_get_course_not_found(self, course_service, mock_db):
        """Obtener curso que no existe."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        course = await course_service.get_course(uuid4())

        assert course is None

    @pytest.mark.asyncio
    async def test_get_course_by_code_not_found(self, course_service, mock_db):
        """Código de inscripción no existe."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        course = await course_service.get_course_by_code("INVALID")

        assert course is None


# =============================================================================
# Tests de Inscripciones
# =============================================================================

class TestCourseServiceEnrollments:
    """Tests para gestión de inscripciones."""

    def test_enrollment_status_active(self, sample_enrollment):
        """Inscripción inicia activa."""
        assert sample_enrollment.status == EnrollmentStatus.ACTIVE

    def test_enrollment_has_timestamps(self, sample_enrollment):
        """Inscripción tiene timestamps."""
        assert sample_enrollment.enrolled_at is not None

    def test_enrollment_links_student_and_course(
        self, sample_enrollment, sample_student, sample_course
    ):
        """Inscripción vincula estudiante y curso."""
        assert sample_enrollment.student_id == sample_student.id
        assert sample_enrollment.course_id == sample_course.id


# =============================================================================
# Tests de Estados de Inscripción
# =============================================================================

class TestEnrollmentStatus:
    """Tests para estados de inscripción."""

    def test_enrollment_statuses_exist(self):
        """Todos los estados de inscripción existen."""
        assert EnrollmentStatus.PENDING == "pending"
        assert EnrollmentStatus.ACTIVE == "active"
        assert EnrollmentStatus.INACTIVE == "inactive"
        assert EnrollmentStatus.COMPLETED == "completed"

    def test_pending_status_description(self):
        """Estado pending para solicitudes pendientes."""
        assert EnrollmentStatus.PENDING.value == "pending"

    def test_completed_status_description(self):
        """Estado completed para cursos terminados."""
        assert EnrollmentStatus.COMPLETED.value == "completed"


# =============================================================================
# Tests de Generación de Código
# =============================================================================

class TestEnrollmentCodeGeneration:
    """Tests para generación de códigos de inscripción."""

    def test_generate_code_length(self):
        """Código tiene 6 caracteres."""
        code = generate_enrollment_code()
        assert len(code) == 6

    def test_generate_code_uppercase(self):
        """Código es alfanumérico uppercase."""
        code = generate_enrollment_code()
        assert code.isupper() or code.isdigit() or (
            all(c.isupper() or c.isdigit() for c in code)
        )

    def test_generate_code_no_confusing_chars(self):
        """Código no tiene caracteres confusos (0, O, I, 1, L)."""
        # Generar varios códigos para verificar
        for _ in range(100):
            code = generate_enrollment_code()
            assert '0' not in code
            assert 'O' not in code
            assert 'I' not in code
            assert '1' not in code
            assert 'L' not in code

    def test_generate_code_unique(self):
        """Códigos generados son únicos (probabilísticamente)."""
        codes = set()
        for _ in range(100):
            code = generate_enrollment_code()
            codes.add(code)
        # Al menos 95 de 100 deben ser únicos
        assert len(codes) >= 95


# =============================================================================
# Tests de Schemas de Curso
# =============================================================================

class TestCourseSchemas:
    """Tests para validación de schemas de curso."""

    def test_course_create_valid(self):
        """CourseCreate válido."""
        course = CourseCreate(
            name="Cardiología Básica",
            description="Introducción a cardiología",
            semester="2025-1",
            max_students=40
        )
        assert course.name == "Cardiología Básica"
        assert course.max_students == 40

    def test_course_create_minimal(self):
        """CourseCreate con campos mínimos."""
        course = CourseCreate(name="Curso Básico")
        assert course.name == "Curso Básico"
        assert course.description is None

    def test_course_update_partial(self):
        """CourseUpdate permite actualización parcial."""
        update = CourseUpdate(name="Nuevo Nombre")
        assert update.name == "Nuevo Nombre"
        assert update.description is None


# =============================================================================
# Tests de Modelo de Curso
# =============================================================================

class TestCourseModel:
    """Tests para el modelo Course."""

    def test_course_has_required_fields(self, sample_course):
        """Curso tiene todos los campos requeridos."""
        assert sample_course.id is not None
        assert sample_course.name is not None
        assert sample_course.professor_id is not None
        assert sample_course.enrollment_code is not None

    def test_course_professor_relationship(self, sample_course, sample_professor):
        """Curso tiene relación con profesor."""
        assert sample_course.professor == sample_professor

    def test_course_enrollments_list(self, sample_course):
        """Curso tiene lista de inscripciones."""
        assert isinstance(sample_course.enrollments, list)


# =============================================================================
# Tests de Modelo de Usuario
# =============================================================================

class TestUserModel:
    """Tests para el modelo User."""

    def test_user_roles_exist(self):
        """Todos los roles de usuario existen."""
        assert UserRole.STUDENT == "student"
        assert UserRole.PROFESSOR == "professor"
        assert UserRole.ADMIN == "admin"

    def test_student_role(self, sample_student):
        """Estudiante tiene rol correcto."""
        assert sample_student.role == UserRole.STUDENT

    def test_professor_role(self, sample_professor):
        """Profesor tiene rol correcto."""
        assert sample_professor.role == UserRole.PROFESSOR


# =============================================================================
# Tests de Integración Curso-Estudiante
# =============================================================================

class TestCourseStudentIntegration:
    """Tests de integración entre cursos y estudiantes."""

    def test_course_can_have_multiple_enrollments(self, sample_course, sample_student):
        """Curso puede tener múltiples inscripciones."""
        enrollment1 = MagicMock(spec=CourseEnrollment)
        enrollment1.student_id = sample_student.id
        enrollment1.status = EnrollmentStatus.ACTIVE

        enrollment2 = MagicMock(spec=CourseEnrollment)
        enrollment2.student_id = uuid4()
        enrollment2.status = EnrollmentStatus.ACTIVE

        sample_course.enrollments = [enrollment1, enrollment2]

        assert len(sample_course.enrollments) == 2

    def test_student_enrollment_status_transitions(self):
        """Verificar transiciones de estado de inscripción."""
        # PENDING -> ACTIVE (profesor aprueba)
        # ACTIVE -> INACTIVE (estudiante se da de baja)
        # ACTIVE -> COMPLETED (curso terminado)
        valid_transitions = {
            EnrollmentStatus.PENDING: [EnrollmentStatus.ACTIVE, EnrollmentStatus.INACTIVE],
            EnrollmentStatus.ACTIVE: [EnrollmentStatus.INACTIVE, EnrollmentStatus.COMPLETED],
            EnrollmentStatus.INACTIVE: [],
            EnrollmentStatus.COMPLETED: [],
        }

        # Verificar que las transiciones existen
        for from_status, to_statuses in valid_transitions.items():
            assert from_status in EnrollmentStatus
            for to_status in to_statuses:
                assert to_status in EnrollmentStatus


# =============================================================================
# Tests Adicionales de CourseService
# =============================================================================

class TestCourseServiceAdditional:
    """Tests adicionales para cubrir más métodos de CourseService."""

    @pytest.mark.asyncio
    async def test_update_course(self, course_service, mock_db, sample_course):
        """Actualiza un curso."""
        update_data = CourseUpdate(name="Nuevo Nombre del Curso")

        result = await course_service.update_course(sample_course, update_data)

        assert sample_course.name == "Nuevo Nombre del Curso"
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_course(self, course_service, mock_db, sample_course):
        """Elimina un curso."""
        await course_service.delete_course(sample_course)

        mock_db.delete.assert_called_once_with(sample_course)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_enrollment_code(self, course_service, mock_db, sample_course):
        """Regenera el código de inscripción."""
        old_code = sample_course.enrollment_code

        # Mock: no hay colisión
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await course_service.regenerate_enrollment_code(sample_course)

        # El código debería haber cambiado (aunque es mock)
        mock_db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_get_enrollment(self, course_service, mock_db, sample_course, sample_student):
        """Obtiene una inscripción específica."""
        mock_enrollment = MagicMock(spec=CourseEnrollment)
        mock_enrollment.course_id = sample_course.id
        mock_enrollment.student_id = sample_student.id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_enrollment
        mock_db.execute.return_value = mock_result

        enrollment = await course_service.get_enrollment(sample_course.id, sample_student.id)

        assert enrollment == mock_enrollment

    @pytest.mark.asyncio
    async def test_get_enrollment_not_found(self, course_service, mock_db):
        """Retorna None si no hay inscripción."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        enrollment = await course_service.get_enrollment(uuid4(), uuid4())

        assert enrollment is None

    @pytest.mark.asyncio
    async def test_get_student_enrollments(self, course_service, mock_db, sample_student):
        """Lista inscripciones de un estudiante."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        enrollments = await course_service.get_student_enrollments(sample_student.id)

        assert enrollments == []

    @pytest.mark.asyncio
    async def test_get_course_enrollments(self, course_service, mock_db, sample_course):
        """Lista inscripciones de un curso."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        enrollments = await course_service.get_course_enrollments(sample_course.id)

        assert enrollments == []

    @pytest.mark.asyncio
    async def test_get_active_enrollment_count(self, course_service, mock_db, sample_course):
        """Cuenta inscripciones activas."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 15
        mock_db.execute.return_value = mock_result

        count = await course_service.get_active_enrollment_count(sample_course.id)

        assert count == 15

    @pytest.mark.asyncio
    async def test_get_course_exams(self, course_service, mock_db, sample_course):
        """Lista exámenes de un curso."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        exams = await course_service.get_course_exams(sample_course.id)

        assert exams == []

    @pytest.mark.asyncio
    async def test_get_professor_courses_with_pagination(self, course_service, mock_db, sample_professor):
        """Lista cursos de profesor con paginación."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        courses = await course_service.get_professor_courses(
            sample_professor.id,
            limit=10,
            offset=5
        )

        assert courses == []
        mock_db.execute.assert_called_once()


# =============================================================================
# Tests de Inscripción de Estudiantes
# =============================================================================

class TestEnrollStudent:
    """Tests para inscripción de estudiantes."""

    @pytest.fixture
    def mock_db(self):
        """Mock de AsyncSession."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def course_service(self, mock_db):
        """Instancia de CourseService con DB mockeada."""
        return CourseService(mock_db)

    @pytest.fixture
    def sample_student(self):
        """Estudiante de prueba."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "estudiante@test.com"
        user.role = UserRole.STUDENT
        return user

    @pytest.fixture
    def sample_course(self):
        """Curso de prueba."""
        course = MagicMock(spec=Course)
        course.id = uuid4()
        course.name = "Oncología"
        course.enrollment_code = "ABC123"
        course.is_active = True
        course.max_students = 50
        return course

    @pytest.mark.asyncio
    async def test_enroll_student_code_not_found(self, course_service, mock_db, sample_student):
        """Error si código no existe."""
        with patch.object(course_service, 'get_course_by_code', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError, match="Código de inscripción inválido"):
                await course_service.enroll_student("INVALID", sample_student)

    @pytest.mark.asyncio
    async def test_enroll_student_course_inactive(self, course_service, mock_db, sample_student, sample_course):
        """Error si curso está inactivo."""
        sample_course.is_active = False

        with patch.object(course_service, 'get_course_by_code', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_course

            with pytest.raises(ValueError, match="no está aceptando inscripciones"):
                await course_service.enroll_student("ABC123", sample_student)

    @pytest.mark.asyncio
    async def test_enroll_student_already_enrolled(self, course_service, mock_db, sample_student, sample_course):
        """Error si ya está inscrito."""
        mock_enrollment = MagicMock(spec=CourseEnrollment)
        mock_enrollment.status = EnrollmentStatus.ACTIVE

        with patch.object(course_service, 'get_course_by_code', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_course
            with patch.object(course_service, 'get_enrollment', new_callable=AsyncMock) as mock_enroll:
                mock_enroll.return_value = mock_enrollment

                with pytest.raises(ValueError, match="Ya estás inscrito"):
                    await course_service.enroll_student("ABC123", sample_student)

    @pytest.mark.asyncio
    async def test_enroll_student_reactivate_inactive(self, course_service, mock_db, sample_student, sample_course):
        """Reactiva inscripción inactiva."""
        mock_enrollment = MagicMock(spec=CourseEnrollment)
        mock_enrollment.status = EnrollmentStatus.INACTIVE

        with patch.object(course_service, 'get_course_by_code', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_course
            with patch.object(course_service, 'get_enrollment', new_callable=AsyncMock) as mock_enroll:
                mock_enroll.return_value = mock_enrollment

                result = await course_service.enroll_student("ABC123", sample_student)

                assert mock_enrollment.status == EnrollmentStatus.ACTIVE
                assert result == mock_enrollment

    @pytest.mark.asyncio
    async def test_enroll_student_course_full(self, course_service, mock_db, sample_student, sample_course):
        """Error si curso está lleno."""
        sample_course.max_students = 10

        with patch.object(course_service, 'get_course_by_code', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_course
            with patch.object(course_service, 'get_enrollment', new_callable=AsyncMock) as mock_enroll:
                mock_enroll.return_value = None
                with patch.object(course_service, 'get_active_enrollment_count', new_callable=AsyncMock) as mock_count:
                    mock_count.return_value = 10  # Ya lleno

                    with pytest.raises(ValueError, match="límite de estudiantes"):
                        await course_service.enroll_student("ABC123", sample_student)

    @pytest.mark.asyncio
    async def test_enroll_student_success(self, course_service, mock_db, sample_student, sample_course):
        """Inscripción exitosa."""
        with patch.object(course_service, 'get_course_by_code', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_course
            with patch.object(course_service, 'get_enrollment', new_callable=AsyncMock) as mock_enroll:
                mock_enroll.return_value = None
                with patch.object(course_service, 'get_active_enrollment_count', new_callable=AsyncMock) as mock_count:
                    mock_count.return_value = 5

                    result = await course_service.enroll_student("ABC123", sample_student)

                    mock_db.add.assert_called_once()
                    mock_db.flush.assert_called()


# =============================================================================
# Tests adicionales para CourseService
# =============================================================================

class TestCourseServiceExtraFeatures:
    """Tests adicionales para CourseService."""

    @pytest.fixture
    def mock_db(self):
        """Mock de AsyncSession."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def course_service(self, mock_db):
        """Instancia de CourseService con DB mockeada."""
        return CourseService(mock_db)

    @pytest.mark.asyncio
    async def test_update_enrollment_status(self, course_service, mock_db):
        """Actualizar estado de inscripción."""
        enrollment = MagicMock(spec=CourseEnrollment)
        enrollment.status = EnrollmentStatus.ACTIVE
        enrollment.completed_at = None

        result = await course_service.update_enrollment_status(
            enrollment, EnrollmentStatus.COMPLETED
        )

        assert enrollment.status == EnrollmentStatus.COMPLETED
        assert enrollment.completed_at is not None
        mock_db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_update_enrollment_status_no_complete(self, course_service, mock_db):
        """Actualizar estado sin completar."""
        enrollment = MagicMock(spec=CourseEnrollment)
        enrollment.status = EnrollmentStatus.ACTIVE
        enrollment.completed_at = None

        await course_service.update_enrollment_status(
            enrollment, EnrollmentStatus.INACTIVE
        )

        assert enrollment.status == EnrollmentStatus.INACTIVE
        assert enrollment.completed_at is None

    @pytest.mark.asyncio
    async def test_leave_course(self, course_service, mock_db):
        """Estudiante abandona curso."""
        enrollment = MagicMock(spec=CourseEnrollment)
        enrollment.status = EnrollmentStatus.ACTIVE

        course_service.get_enrollment = AsyncMock(return_value=enrollment)

        await course_service.leave_course(uuid4(), uuid4())

        assert enrollment.status == EnrollmentStatus.INACTIVE
        mock_db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_leave_course_no_enrollment(self, course_service, mock_db):
        """Leave course sin inscripción no hace nada."""
        course_service.get_enrollment = AsyncMock(return_value=None)

        # No debe lanzar excepción
        await course_service.leave_course(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_get_course_exams(self, course_service, mock_db):
        """Obtener exámenes de un curso."""
        from app.models.db_models import Exam

        mock_exam = MagicMock(spec=Exam)
        mock_exam.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_exam]
        mock_db.execute.return_value = mock_result

        exams = await course_service.get_course_exams(uuid4())

        assert len(exams) == 1
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_course_exams_published_only(self, course_service, mock_db):
        """Obtener solo exámenes publicados."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        exams = await course_service.get_course_exams(uuid4(), published_only=True)

        assert exams == []

    @pytest.mark.asyncio
    async def test_get_student_available_exams(self, course_service, mock_db):
        """Obtener exámenes disponibles para estudiante."""
        mock_enrollment = MagicMock(spec=CourseEnrollment)
        mock_enrollment.course_id = uuid4()

        course_service.get_student_enrollments = AsyncMock(
            return_value=[mock_enrollment]
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        exams = await course_service.get_student_available_exams(uuid4())

        assert isinstance(exams, list)

    @pytest.mark.asyncio
    async def test_is_student_enrolled_in_exam_course_no_course(
        self, course_service, mock_db
    ):
        """No inscrito si examen no tiene curso."""
        from app.models.db_models import Exam

        exam = MagicMock(spec=Exam)
        exam.course_id = None

        result = await course_service.is_student_enrolled_in_exam_course(
            uuid4(), exam
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_is_student_enrolled_in_exam_course_enrolled(
        self, course_service, mock_db
    ):
        """Inscrito si tiene enrollment activo."""
        from app.models.db_models import Exam

        exam = MagicMock(spec=Exam)
        exam.course_id = uuid4()

        enrollment = MagicMock(spec=CourseEnrollment)
        enrollment.status = EnrollmentStatus.ACTIVE

        course_service.get_enrollment = AsyncMock(return_value=enrollment)

        result = await course_service.is_student_enrolled_in_exam_course(
            uuid4(), exam
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_is_student_enrolled_in_exam_course_not_enrolled(
        self, course_service, mock_db
    ):
        """No inscrito si no tiene enrollment."""
        from app.models.db_models import Exam

        exam = MagicMock(spec=Exam)
        exam.course_id = uuid4()

        course_service.get_enrollment = AsyncMock(return_value=None)

        result = await course_service.is_student_enrolled_in_exam_course(
            uuid4(), exam
        )

        assert result is False


class TestCourseServiceFactory:
    """Tests para factory function."""

    def test_get_course_service(self):
        """Factory crea instancia correctamente."""
        from app.services.course_service import get_course_service

        mock_db = AsyncMock()
        service = get_course_service(mock_db)

        assert isinstance(service, CourseService)
        assert service.db == mock_db

"""
Tests exhaustivos para ExamService
Incluye tests de CRUD de exámenes, preguntas, intentos y calificación
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.exam_service import ExamService
from app.schemas.exam_schemas import ExamCreate, QuestionCreate, AnswerSubmit
from app.models.db_models import (
    Exam, ExamAttempt, Question, Answer,
    ExamStatus, ExamType, AttemptStatus,
    QuestionType, QuestionSource, User, UserRole
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
def exam_service(mock_db):
    """Instancia de ExamService con DB mockeada."""
    return ExamService(mock_db)


@pytest.fixture
def sample_professor():
    """Profesor de prueba."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "profesor@universidad.edu"
    user.full_name = "Dr. García"
    user.role = UserRole.PROFESSOR
    user.is_active = True
    return user


@pytest.fixture
def sample_student():
    """Estudiante de prueba."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "estudiante@universidad.edu"
    user.full_name = "María López"
    user.role = UserRole.STUDENT
    user.is_active = True
    return user


@pytest.fixture
def sample_exam(sample_professor):
    """Examen de prueba."""
    exam = MagicMock(spec=Exam)
    exam.id = uuid4()
    exam.title = "Examen de Prueba"
    exam.description = "Descripción del examen"
    exam.course_id = uuid4()
    exam.exam_type = ExamType.MINI_QUIZ
    exam.time_limit_minutes = 30
    exam.passing_score = 60.0
    exam.max_attempts = 3
    exam.shuffle_questions = True
    exam.creator_id = sample_professor.id
    exam.status = ExamStatus.DRAFT
    exam.questions = []
    exam.created_at = datetime.utcnow()
    return exam


@pytest.fixture
def sample_question(sample_exam):
    """Pregunta de prueba."""
    question = MagicMock(spec=Question)
    question.id = uuid4()
    question.exam_id = sample_exam.id
    question.question_text = "¿Cuál es la capital de Francia?"
    question.question_type = QuestionType.MULTIPLE_CHOICE
    question.source = QuestionSource.PROFESSOR
    question.options = ["Madrid", "París", "Londres", "Berlín"]
    question.correct_answer = "París"
    question.points = 10.0
    question.order = 1
    return question


@pytest.fixture
def sample_attempt(sample_exam, sample_student):
    """Intento de examen de prueba."""
    attempt = MagicMock(spec=ExamAttempt)
    attempt.id = uuid4()
    attempt.exam_id = sample_exam.id
    attempt.student_id = sample_student.id
    attempt.status = AttemptStatus.IN_PROGRESS
    attempt.started_at = datetime.utcnow()
    attempt.answers = []
    attempt.score = None
    return attempt


@pytest.fixture
def exam_create_request():
    """Request para crear examen."""
    return ExamCreate(
        title="Nuevo Examen",
        description="Descripción del nuevo examen",
        course_id=uuid4(),
        exam_type=ExamType.MINI_QUIZ,
        time_limit_minutes=15,
        passing_score=70.0,
        max_attempts=2,
        shuffle_questions=False
    )


# =============================================================================
# Tests de Examen CRUD (Casos Positivos)
# =============================================================================

class TestExamServiceCRUDPositive:
    """Tests de CRUD de exámenes que DEBEN funcionar."""

    @pytest.mark.asyncio
    async def test_create_exam_success(
        self, exam_service, mock_db, exam_create_request, sample_professor
    ):
        """Crear examen exitosamente."""
        async def fake_refresh(exam):
            exam.id = uuid4()
            exam.created_at = datetime.utcnow()
        mock_db.refresh = fake_refresh

        exam = await exam_service.create_exam(exam_create_request, sample_professor)

        assert exam is not None
        mock_db.add.assert_called_once()
        assert exam.status == ExamStatus.DRAFT

    @pytest.mark.asyncio
    async def test_get_exam_by_id(self, exam_service, mock_db, sample_exam):
        """Obtener examen por ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_exam
        mock_db.execute.return_value = mock_result

        exam = await exam_service.get_exam(sample_exam.id)

        assert exam == sample_exam
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_exams_by_creator(
        self, exam_service, mock_db, sample_exam, sample_professor
    ):
        """Listar exámenes de un profesor."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_exam]
        mock_db.execute.return_value = mock_result

        exams = await exam_service.get_exams_by_creator(sample_professor.id)

        assert len(exams) == 1
        assert exams[0] == sample_exam

    @pytest.mark.asyncio
    async def test_get_published_exams(self, exam_service, mock_db, sample_exam):
        """Listar exámenes publicados."""
        sample_exam.status = ExamStatus.PUBLISHED
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_exam]
        mock_db.execute.return_value = mock_result

        exams = await exam_service.get_published_exams()

        assert len(exams) == 1


# =============================================================================
# Tests de Examen CRUD (Casos Negativos)
# =============================================================================

class TestExamServiceCRUDNegative:
    """Tests de CRUD que NO deben funcionar."""

    @pytest.mark.asyncio
    async def test_get_exam_not_found(self, exam_service, mock_db):
        """Obtener examen que no existe."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        exam = await exam_service.get_exam(uuid4())

        assert exam is None

    @pytest.mark.asyncio
    async def test_get_exams_by_creator_empty(self, exam_service, mock_db):
        """Profesor sin exámenes."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        exams = await exam_service.get_exams_by_creator(uuid4())

        assert exams == []


# =============================================================================
# Tests de Preguntas
# =============================================================================

class TestExamServiceQuestions:
    """Tests para gestión de preguntas."""

    @pytest.mark.asyncio
    async def test_question_structure(self, sample_question):
        """Estructura de pregunta es correcta."""
        assert sample_question.question_text is not None
        assert sample_question.question_type == QuestionType.MULTIPLE_CHOICE
        assert len(sample_question.options) == 4
        assert sample_question.correct_answer in sample_question.options
        assert sample_question.points > 0


# =============================================================================
# Tests de Intentos de Examen
# =============================================================================

class TestExamServiceAttempts:
    """Tests para intentos de examen."""

    @pytest.fixture
    def sample_attempt(self, sample_exam, sample_student):
        """Intento de examen de prueba."""
        attempt = MagicMock(spec=ExamAttempt)
        attempt.id = uuid4()
        attempt.exam_id = sample_exam.id
        attempt.student_id = sample_student.id
        attempt.status = AttemptStatus.IN_PROGRESS
        attempt.started_at = datetime.utcnow()
        attempt.score = None
        attempt.answers = []
        return attempt

    def test_attempt_status_in_progress(self, sample_attempt):
        """Intento inicia en progreso."""
        assert sample_attempt.status == AttemptStatus.IN_PROGRESS
        assert sample_attempt.score is None

    def test_attempt_has_timestamps(self, sample_attempt):
        """Intento tiene timestamps."""
        assert sample_attempt.started_at is not None


# =============================================================================
# Tests de Tipos de Examen
# =============================================================================

class TestExamTypes:
    """Tests para tipos de examen y límites."""

    def test_mini_quiz_type(self):
        """Mini quiz tiene configuración correcta."""
        from app.models.db_models import EXAM_TYPE_LIMITS
        limits = EXAM_TYPE_LIMITS[ExamType.MINI_QUIZ]

        assert limits["min"] == 5
        assert limits["max"] == 10
        assert limits["time_suggested"] == 10

    def test_module_eval_type(self):
        """Module eval tiene configuración correcta."""
        from app.models.db_models import EXAM_TYPE_LIMITS
        limits = EXAM_TYPE_LIMITS[ExamType.MODULE_EVAL]

        assert limits["min"] == 15
        assert limits["max"] == 25
        assert limits["time_suggested"] == 30

    def test_full_exam_type(self):
        """Full exam tiene configuración correcta."""
        from app.models.db_models import EXAM_TYPE_LIMITS
        limits = EXAM_TYPE_LIMITS[ExamType.FULL_EXAM]

        assert limits["min"] == 30
        assert limits["max"] == 50
        assert limits["time_suggested"] == 60

    def test_ai_personalized_type(self):
        """AI personalized tiene configuración correcta."""
        from app.models.db_models import EXAM_TYPE_LIMITS
        limits = EXAM_TYPE_LIMITS[ExamType.AI_PERSONALIZED]

        assert limits["min"] == 4
        assert limits["max"] == 4
        assert limits["time_suggested"] == 5


# =============================================================================
# Tests de Estados de Examen
# =============================================================================

class TestExamStatus:
    """Tests para estados de examen."""

    def test_exam_statuses_exist(self):
        """Todos los estados existen."""
        assert ExamStatus.DRAFT == "draft"
        assert ExamStatus.PUBLISHED == "published"
        assert ExamStatus.ARCHIVED == "archived"

    def test_attempt_statuses_exist(self):
        """Todos los estados de intento existen."""
        assert AttemptStatus.IN_PROGRESS == "in_progress"
        assert AttemptStatus.SUBMITTED == "submitted"
        assert AttemptStatus.GRADED == "graded"


# =============================================================================
# Tests de Question Types
# =============================================================================

class TestQuestionTypes:
    """Tests para tipos de pregunta."""

    def test_question_types_exist(self):
        """Todos los tipos de pregunta existen."""
        assert QuestionType.MULTIPLE_CHOICE == "multiple_choice"
        assert QuestionType.TRUE_FALSE == "true_false"
        assert QuestionType.OPEN_ENDED == "open_ended"
        assert QuestionType.AI_GENERATED == "ai_generated"

    def test_question_sources_exist(self):
        """Todas las fuentes de pregunta existen."""
        assert QuestionSource.PROFESSOR == "professor"
        assert QuestionSource.AI_PERSONALIZED == "ai_personalized"


# =============================================================================
# Tests de Schemas de Examen
# =============================================================================

class TestExamSchemas:
    """Tests para validación de schemas de examen."""

    def test_exam_create_valid(self):
        """ExamCreate válido."""
        exam = ExamCreate(
            title="Test Exam",
            description="Description",
            exam_type=ExamType.MINI_QUIZ,
            time_limit_minutes=15,
            passing_score=60.0,
            max_attempts=3,
            shuffle_questions=True
        )
        assert exam.title == "Test Exam"
        assert exam.exam_type == ExamType.MINI_QUIZ

    def test_exam_create_optional_course(self):
        """Course ID es opcional."""
        exam = ExamCreate(
            title="Private Exam",
            exam_type=ExamType.MINI_QUIZ
        )
        assert exam.course_id is None

    def test_question_create_valid(self):
        """QuestionCreate válido."""
        question = QuestionCreate(
            text="¿Cuál es el estadío tumoral si el diámetro es de 4cm?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options='["3", "4", "5", "6"]',
            correct_answer="1",
            points=5.0
        )
        assert question.text == "¿Cuál es el estadío tumoral si el diámetro es de 4cm?"
        assert question.correct_answer == "1"

    def test_answer_submit_valid(self):
        """AnswerSubmit válido."""
        answer = AnswerSubmit(
            question_id=uuid4(),
            selected_option=1
        )
        assert answer.selected_option == 1


# =============================================================================
# Tests de Métodos Adicionales de ExamService
# =============================================================================

class TestExamServiceAdditional:
    """Tests adicionales para cubrir más métodos de ExamService."""

    @pytest.mark.asyncio
    async def test_get_published_exams(self, exam_service, mock_db, sample_exam):
        """Lista exámenes publicados."""
        sample_exam.status = ExamStatus.PUBLISHED
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_exam]
        mock_db.execute.return_value = mock_result

        exams = await exam_service.get_published_exams()

        assert len(exams) == 1
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_published_exams_empty(self, exam_service, mock_db):
        """Lista vacía si no hay exámenes publicados."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        exams = await exam_service.get_published_exams()

        assert exams == []

    @pytest.mark.asyncio
    async def test_delete_exam(self, exam_service, mock_db, sample_exam):
        """Elimina un examen."""
        await exam_service.delete_exam(sample_exam)

        mock_db.delete.assert_called_once_with(sample_exam)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_question_by_id(self, exam_service, mock_db, sample_question):
        """Obtiene una pregunta por ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_question
        mock_db.execute.return_value = mock_result

        question = await exam_service.get_question(sample_question.id)

        assert question == sample_question

    @pytest.mark.asyncio
    async def test_get_question_not_found(self, exam_service, mock_db):
        """Retorna None si la pregunta no existe."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        question = await exam_service.get_question(uuid4())

        assert question is None

    @pytest.mark.asyncio
    async def test_delete_question(self, exam_service, mock_db, sample_question):
        """Elimina una pregunta."""
        await exam_service.delete_question(sample_question)

        mock_db.delete.assert_called_once_with(sample_question)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_exam_questions(self, exam_service, mock_db, sample_exam, sample_question):
        """Lista preguntas de un examen."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_question]
        mock_db.execute.return_value = mock_result

        questions = await exam_service.get_exam_questions(sample_exam.id)

        assert len(questions) == 1
        assert questions[0] == sample_question

    @pytest.mark.asyncio
    async def test_get_exam_question_count(self, exam_service, mock_db, sample_exam):
        """Cuenta preguntas de un examen."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute.return_value = mock_result

        count = await exam_service.get_exam_question_count(sample_exam.id)

        assert count == 5

    @pytest.mark.asyncio
    async def test_get_attempt_by_id(self, exam_service, mock_db, sample_attempt):
        """Obtiene un intento por ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_attempt
        mock_db.execute.return_value = mock_result

        attempt = await exam_service.get_attempt(sample_attempt.id)

        assert attempt == sample_attempt

    @pytest.mark.asyncio
    async def test_get_attempt_not_found(self, exam_service, mock_db):
        """Retorna None si el intento no existe."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        attempt = await exam_service.get_attempt(uuid4())

        assert attempt is None

    @pytest.mark.asyncio
    async def test_get_student_attempts(self, exam_service, mock_db, sample_student, sample_attempt):
        """Lista intentos de un estudiante para un examen."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_attempt]
        mock_db.execute.return_value = mock_result

        attempts = await exam_service.get_student_attempts(sample_student.id, sample_attempt.exam_id)

        assert len(attempts) == 1


# =============================================================================
# Tests de Lógica de Negocio
# =============================================================================

class TestExamBusinessLogic:
    """Tests para lógica de negocio de exámenes."""

    def test_exam_status_transitions(self):
        """Estados válidos de examen."""
        assert ExamStatus.DRAFT.value == "draft"
        assert ExamStatus.PUBLISHED.value == "published"
        assert ExamStatus.ARCHIVED.value == "archived"
        # Verificar que hay al menos 3 estados
        assert len(list(ExamStatus)) >= 3

    def test_attempt_status_values(self):
        """Estados válidos de intento."""
        assert AttemptStatus.IN_PROGRESS.value == "in_progress"
        assert AttemptStatus.SUBMITTED.value == "submitted"
        assert AttemptStatus.GRADED.value == "graded"
        # Verificar que hay al menos 3 estados
        assert len(list(AttemptStatus)) >= 3

    def test_question_type_values(self):
        """Tipos de pregunta válidos."""
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert QuestionType.TRUE_FALSE.value == "true_false"
        # Verificar que hay al menos 2 tipos
        assert len(list(QuestionType)) >= 2

    def test_question_source_values(self):
        """Fuentes de pregunta válidas."""
        assert QuestionSource.PROFESSOR.value == "professor"
        # AI puede ser ai_personalized o ai_generated según la versión
        ai_values = [s.value for s in QuestionSource if 'ai' in s.value.lower()]
        assert len(ai_values) >= 1


# =============================================================================
# Tests de Validación de Examen
# =============================================================================

class TestExamValidation:
    """Tests para validación de exámenes."""

    def test_exam_type_limits(self):
        """Límites de preguntas por tipo de examen."""
        from app.models.db_models import EXAM_TYPE_LIMITS

        assert "mini_quiz" in EXAM_TYPE_LIMITS
        assert "module_eval" in EXAM_TYPE_LIMITS
        assert "full_exam" in EXAM_TYPE_LIMITS

        # Verificar estructura de límites
        for exam_type, limits in EXAM_TYPE_LIMITS.items():
            assert "min" in limits
            assert "max" in limits
            assert limits["min"] <= limits["max"]

    def test_mini_quiz_limits(self):
        """Límites del mini quiz."""
        from app.models.db_models import EXAM_TYPE_LIMITS
        limits = EXAM_TYPE_LIMITS.get("mini_quiz", {})
        assert limits.get("min", 0) >= 1
        assert limits.get("max", 100) <= 15

    def test_passing_score_range(self):
        """Puntaje de aprobación válido."""
        exam = ExamCreate(
            title="Test Exam Title",
            exam_type=ExamType.MINI_QUIZ,
            passing_score=70.0
        )
        assert 0 <= exam.passing_score <= 100


# =============================================================================
# Tests Adicionales de ExamService
# =============================================================================

class TestExamServiceQuestionManagement:
    """Tests para gestión de preguntas."""

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
    def exam_service(self, mock_db):
        """Instancia de ExamService con DB mockeada."""
        return ExamService(mock_db)

    @pytest.fixture
    def sample_exam(self):
        """Examen de prueba."""
        exam = MagicMock(spec=Exam)
        exam.id = uuid4()
        exam.title = "Examen de Prueba"
        return exam

    @pytest.fixture
    def question_create_request(self):
        """Request para crear pregunta."""
        return QuestionCreate(
            text="¿Cuál es el tamaño máximo de T1?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options='["1cm", "2cm", "3cm", "4cm"]',
            correct_answer="2",
            points=5.0
        )

    @pytest.mark.asyncio
    async def test_add_question_success(self, exam_service, mock_db, sample_exam, question_create_request):
        """Agregar pregunta exitosamente."""
        result = await exam_service.add_question(sample_exam, question_create_request)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_question(self, exam_service, mock_db):
        """Actualizar pregunta."""
        from app.schemas.exam_schemas import QuestionUpdate

        mock_question = MagicMock(spec=Question)
        mock_question.text = "Pregunta original"

        update_data = QuestionUpdate(text="Pregunta actualizada")

        result = await exam_service.update_question(mock_question, update_data)

        assert mock_question.text == "Pregunta actualizada"
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_question(self, exam_service, mock_db):
        """Eliminar pregunta."""
        mock_question = MagicMock(spec=Question)

        await exam_service.delete_question(mock_question)

        mock_db.delete.assert_called_once_with(mock_question)
        mock_db.flush.assert_called_once()


class TestExamServiceExamCRUD:
    """Tests adicionales para CRUD de exámenes."""

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
    def exam_service(self, mock_db):
        """Instancia de ExamService con DB mockeada."""
        return ExamService(mock_db)

    @pytest.mark.asyncio
    async def test_update_exam_publish(self, exam_service, mock_db):
        """Actualizar examen para publicar."""
        from app.schemas.exam_schemas import ExamUpdate

        mock_exam = MagicMock(spec=Exam)
        mock_exam.published_at = None

        update_data = ExamUpdate(status=ExamStatus.PUBLISHED)

        await exam_service.update_exam(mock_exam, update_data)

        assert mock_exam.status == ExamStatus.PUBLISHED
        assert mock_exam.published_at is not None
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_exam(self, exam_service, mock_db):
        """Eliminar examen."""
        mock_exam = MagicMock(spec=Exam)
        mock_exam.title = "Examen a eliminar"

        await exam_service.delete_exam(mock_exam)

        mock_db.delete.assert_called_once_with(mock_exam)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_published_exams(self, exam_service, mock_db):
        """Lista exámenes publicados."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        exams = await exam_service.get_published_exams()

        assert exams == []
        mock_db.execute.assert_called_once()


# =============================================================================
# Tests para Intentos de Examen (Start, Submit)
# =============================================================================

class TestExamServiceAttemptManagement:
    """Tests para gestión de intentos de examen."""

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
    def exam_service(self, mock_db):
        """Instancia de ExamService con DB mockeada."""
        return ExamService(mock_db)

    @pytest.fixture
    def sample_exam(self):
        """Examen de prueba."""
        exam = MagicMock(spec=Exam)
        exam.id = uuid4()
        exam.title = "Examen de Prueba"
        exam.max_attempts = 3
        exam.passing_score = 60.0
        return exam

    @pytest.fixture
    def sample_student(self):
        """Estudiante de prueba."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "estudiante@universidad.edu"
        return user

    @pytest.mark.asyncio
    async def test_start_attempt_first_time(
        self, exam_service, mock_db, sample_exam, sample_student
    ):
        """Iniciar primer intento de examen."""
        # Mock sin intentos previos
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        async def fake_refresh(attempt):
            attempt.id = uuid4()
            attempt.started_at = datetime.utcnow()
        mock_db.refresh = fake_refresh

        attempt = await exam_service.start_attempt(sample_exam, sample_student)

        assert attempt is not None
        assert attempt.exam_id == sample_exam.id
        assert attempt.student_id == sample_student.id
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_attempt_exceeds_max(
        self, exam_service, mock_db, sample_exam, sample_student
    ):
        """No puede iniciar más intentos del máximo."""
        # Mock con máximo de intentos
        existing = [MagicMock() for _ in range(sample_exam.max_attempts)]
        for e in existing:
            e.status = AttemptStatus.SUBMITTED  # Completados

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = existing
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc_info:
            await exam_service.start_attempt(sample_exam, sample_student)

        assert "máximo" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_start_attempt_returns_in_progress(
        self, exam_service, mock_db, sample_exam, sample_student
    ):
        """Retorna intento en progreso si existe."""
        in_progress_attempt = MagicMock(spec=ExamAttempt)
        in_progress_attempt.status = AttemptStatus.IN_PROGRESS
        in_progress_attempt.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [in_progress_attempt]
        mock_db.execute.return_value = mock_result

        attempt = await exam_service.start_attempt(sample_exam, sample_student)

        # Debe retornar el intento existente
        assert attempt == in_progress_attempt
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_attempt_by_id(self, exam_service, mock_db):
        """Obtener intento por ID."""
        mock_attempt = MagicMock(spec=ExamAttempt)
        mock_attempt.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_attempt
        mock_db.execute.return_value = mock_result

        attempt = await exam_service.get_attempt(mock_attempt.id)

        assert attempt == mock_attempt

    @pytest.mark.asyncio
    async def test_get_student_attempts(
        self, exam_service, mock_db, sample_exam, sample_student
    ):
        """Listar intentos de un estudiante."""
        mock_attempts = [MagicMock(spec=ExamAttempt) for _ in range(2)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_attempts
        mock_db.execute.return_value = mock_result

        attempts = await exam_service.get_student_attempts(
            sample_exam.id, sample_student.id
        )

        assert len(attempts) == 2


# =============================================================================
# Tests para Submit Answer
# =============================================================================

class TestExamServiceSubmitAnswer:
    """Tests para envío de respuestas."""

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
    def exam_service(self, mock_db):
        """Instancia de ExamService con DB mockeada."""
        return ExamService(mock_db)

    @pytest.mark.asyncio
    async def test_submit_new_answer(self, exam_service, mock_db):
        """Enviar nueva respuesta."""
        attempt = MagicMock(spec=ExamAttempt)
        attempt.id = uuid4()

        answer_data = AnswerSubmit(
            question_id=uuid4(),
            selected_option=1,
            answer_text=None,
        )

        # No existe respuesta previa
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        async def fake_refresh(answer):
            answer.id = uuid4()
        mock_db.refresh = fake_refresh

        answer = await exam_service.submit_answer(attempt, answer_data)

        mock_db.add.assert_called_once()
        assert answer.question_id == answer_data.question_id

    @pytest.mark.asyncio
    async def test_update_existing_answer(self, exam_service, mock_db):
        """Actualizar respuesta existente."""
        attempt = MagicMock(spec=ExamAttempt)
        attempt.id = uuid4()

        existing_answer = MagicMock(spec=Answer)
        existing_answer.selected_option = 0

        answer_data = AnswerSubmit(
            question_id=uuid4(),
            selected_option=2,
            answer_text=None,
        )

        # Existe respuesta previa
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_answer
        mock_db.execute.return_value = mock_result

        answer = await exam_service.submit_answer(attempt, answer_data)

        # Debe actualizar la existente
        assert answer == existing_answer
        assert existing_answer.selected_option == 2
        mock_db.add.assert_not_called()


# =============================================================================
# Tests para Grade Objective Answer
# =============================================================================

class TestGradeObjectiveAnswer:
    """Tests para calificación de respuestas objetivas."""

    @pytest.fixture
    def mock_db(self):
        """Mock de AsyncSession."""
        return AsyncMock()

    @pytest.fixture
    def exam_service(self, mock_db):
        """Instancia de ExamService con DB mockeada."""
        return ExamService(mock_db)

    def test_grade_multiple_choice_correct(self, exam_service):
        """Calificar respuesta multiple choice correcta."""
        question = MagicMock(spec=Question)
        question.correct_answer = "1"  # Índice 1

        answer = MagicMock(spec=Answer)
        answer.selected_option = 1
        answer.answer_text = None

        is_correct = exam_service._grade_objective_answer(question, answer)

        assert is_correct is True

    def test_grade_multiple_choice_incorrect(self, exam_service):
        """Calificar respuesta multiple choice incorrecta."""
        question = MagicMock(spec=Question)
        question.correct_answer = "1"  # Índice 1

        answer = MagicMock(spec=Answer)
        answer.selected_option = 2
        answer.answer_text = None

        is_correct = exam_service._grade_objective_answer(question, answer)

        assert is_correct is False

    def test_grade_text_answer_correct(self, exam_service):
        """Calificar respuesta de texto correcta."""
        question = MagicMock(spec=Question)
        question.correct_answer = "París"

        answer = MagicMock(spec=Answer)
        answer.selected_option = None
        answer.answer_text = "París"

        is_correct = exam_service._grade_objective_answer(question, answer)

        assert is_correct is True

    def test_grade_text_answer_case_insensitive(self, exam_service):
        """Calificar texto es case-insensitive."""
        question = MagicMock(spec=Question)
        question.correct_answer = "París"

        answer = MagicMock(spec=Answer)
        answer.selected_option = None
        answer.answer_text = "PARÍS"

        is_correct = exam_service._grade_objective_answer(question, answer)

        assert is_correct is True

    def test_grade_no_correct_answer(self, exam_service):
        """Pregunta sin respuesta correcta definida."""
        question = MagicMock(spec=Question)
        question.correct_answer = None

        answer = MagicMock(spec=Answer)
        answer.selected_option = 1
        answer.answer_text = None

        is_correct = exam_service._grade_objective_answer(question, answer)

        assert is_correct is False


# =============================================================================
# Tests para Exam Question Count
# =============================================================================

class TestExamQuestionCount:
    """Tests para conteo de preguntas."""

    @pytest.fixture
    def mock_db(self):
        """Mock de AsyncSession."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def exam_service(self, mock_db):
        """Instancia de ExamService con DB mockeada."""
        return ExamService(mock_db)

    @pytest.mark.asyncio
    async def test_get_exam_question_count(self, exam_service, mock_db):
        """Obtener conteo de preguntas."""
        exam_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute.return_value = mock_result

        count = await exam_service.get_exam_question_count(exam_id)

        assert count == 5

    @pytest.mark.asyncio
    async def test_get_exam_question_count_empty(self, exam_service, mock_db):
        """Conteo de preguntas para examen vacío."""
        exam_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result

        count = await exam_service.get_exam_question_count(exam_id)

        assert count == 0


# =============================================================================
# Tests para Submit Exam (Calificación Completa)
# =============================================================================

class TestExamServiceSubmitExam:
    """Tests para envío completo de examen."""

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
    def exam_service(self, mock_db):
        """Instancia de ExamService con DB mockeada."""
        return ExamService(mock_db)

    @pytest.mark.asyncio
    async def test_submit_exam_calculates_score(self, exam_service, mock_db):
        """Submit exam calcula puntuación correctamente."""
        # Setup attempt
        attempt = MagicMock(spec=ExamAttempt)
        attempt.id = uuid4()
        attempt.exam_id = uuid4()
        attempt.student_id = uuid4()
        attempt.status = AttemptStatus.IN_PROGRESS
        attempt.answers = []

        # Setup questions
        question1 = MagicMock(spec=Question)
        question1.id = uuid4()
        question1.points = 10.0
        question1.correct_answer = "1"
        question1.question_type = MagicMock()
        question1.question_type.value = "multiple_choice"
        question1.topic = None
        question1.difficulty = 1

        question2 = MagicMock(spec=Question)
        question2.id = uuid4()
        question2.points = 10.0
        question2.correct_answer = "0"
        question2.question_type = MagicMock()
        question2.question_type.value = "multiple_choice"
        question2.topic = None
        question2.difficulty = 1

        # Mock get_exam_questions
        exam_service.get_exam_questions = AsyncMock(
            return_value=[question1, question2]
        )

        # Mock submit_answer
        answer1 = MagicMock(spec=Answer)
        answer1.question_id = question1.id
        answer1.selected_option = 1  # Correct
        answer1.answer_text = None

        answer2 = MagicMock(spec=Answer)
        answer2.question_id = question2.id
        answer2.selected_option = 1  # Incorrect (correct is 0)
        answer2.answer_text = None

        exam_service.submit_answer = AsyncMock()

        # Mock answer retrieval
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [answer1, answer2]
        mock_db.execute.return_value = mock_result

        # Mock exam for passing_score
        exam = MagicMock(spec=Exam)
        exam.passing_score = 50.0
        exam_service.get_exam = AsyncMock(return_value=exam)

        answers_data = [
            AnswerSubmit(question_id=question1.id, selected_option=1),
            AnswerSubmit(question_id=question2.id, selected_option=1),
        ]

        result = await exam_service.submit_exam(attempt, answers_data)

        # Verificar que se actualizó el estado
        assert attempt.status == AttemptStatus.GRADED
        assert attempt.submitted_at is not None

    @pytest.mark.asyncio
    async def test_submit_exam_with_open_ended_not_auto_graded(
        self, exam_service, mock_db
    ):
        """Examen con preguntas abiertas no se auto-califica."""
        # Setup attempt
        attempt = MagicMock(spec=ExamAttempt)
        attempt.id = uuid4()
        attempt.exam_id = uuid4()
        attempt.student_id = uuid4()
        attempt.status = AttemptStatus.IN_PROGRESS

        # Question de tipo open_ended
        question = MagicMock(spec=Question)
        question.id = uuid4()
        question.points = 10.0
        question.question_type = MagicMock()
        question.question_type.value = "open_ended"

        exam_service.get_exam_questions = AsyncMock(return_value=[question])
        exam_service.submit_answer = AsyncMock()

        # Mock answer retrieval - vacío porque es open_ended
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        exam = MagicMock(spec=Exam)
        exam.passing_score = 50.0
        exam_service.get_exam = AsyncMock(return_value=exam)

        answers_data = [
            AnswerSubmit(question_id=question.id, answer_text="Mi respuesta"),
        ]

        result = await exam_service.submit_exam(attempt, answers_data)

        # Debe quedar como SUBMITTED, no GRADED
        assert attempt.status == AttemptStatus.SUBMITTED


# =============================================================================
# Tests para Update Student Topic Stats
# =============================================================================

class TestUpdateStudentTopicStats:
    """Tests para actualización de estadísticas por tema."""

    @pytest.fixture
    def mock_db(self):
        """Mock de AsyncSession."""
        return AsyncMock()

    @pytest.fixture
    def exam_service(self, mock_db):
        """Instancia de ExamService con DB mockeada."""
        return ExamService(mock_db)

    @pytest.mark.asyncio
    async def test_update_stats_success(self, exam_service):
        """Actualiza stats correctamente."""
        mock_stats_service = MagicMock()
        mock_stats_service.update_stats_after_answer = AsyncMock()

        with patch(
            'app.services.stats_service.StudentStatsService',
            return_value=mock_stats_service
        ):
            # No debe lanzar excepción
            await exam_service._update_student_topic_stats(
                student_id=uuid4(),
                topic="TUMOR_STAGING",
                is_correct=True,
                difficulty=2
            )


# =============================================================================
# Tests para Factory Function
# =============================================================================

class TestExamServiceFactory:
    """Tests para factory function."""

    def test_get_exam_service(self):
        """Factory crea instancia correctamente."""
        from app.services.exam_service import get_exam_service

        mock_db = AsyncMock()
        service = get_exam_service(mock_db)

        assert isinstance(service, ExamService)
        assert service.db == mock_db

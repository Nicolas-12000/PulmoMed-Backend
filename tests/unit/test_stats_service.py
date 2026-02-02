"""
Tests para StudentStatsService
Suite completa de tests para tracking de estadísticas de estudiantes.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta

from app.services.stats_service import StudentStatsService
from app.models.db_models import MedicalTopic, TopicPerformance


# =============================================================================
# Tests para StudentStatsService
# =============================================================================

class TestStudentStatsServiceCreation:
    """Tests para creación del servicio."""

    def test_create_service(self):
        """Crear servicio de estadísticas."""
        mock_db = AsyncMock()
        service = StudentStatsService(db=mock_db)
        assert service.db is mock_db


class TestTopicPerformanceCRUD:
    """Tests para operaciones CRUD de TopicPerformance."""

    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de base de datos."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Servicio con mock DB."""
        return StudentStatsService(db=mock_db)

    @pytest.mark.asyncio
    async def test_get_or_create_new_topic_stats(self, service, mock_db):
        """Crear stats para nuevo topic."""
        student_id = uuid4()
        topic = MedicalTopic.TUMOR_STAGING

        # Mock: no existe stats
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        _stats = await service.get_or_create_topic_stats(student_id, topic)

        # Debe crear nuevo
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_topic_stats(self, service, mock_db):
        """Obtener stats existentes."""
        student_id = uuid4()
        topic = MedicalTopic.DIAGNOSIS

        existing_stats = MagicMock(spec=TopicPerformance)
        existing_stats.topic = topic
        existing_stats.mastery_score = 75.0

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_stats
        mock_db.execute = AsyncMock(return_value=mock_result)

        stats = await service.get_or_create_topic_stats(student_id, topic)

        assert stats is existing_stats
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_all_student_stats(self, service, mock_db):
        """Obtener todas las stats de un estudiante."""
        student_id = uuid4()

        mock_stats = [
            MagicMock(spec=TopicPerformance, topic=MedicalTopic.TUMOR_STAGING),
            MagicMock(spec=TopicPerformance, topic=MedicalTopic.DIAGNOSIS),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_stats
        mock_db.execute = AsyncMock(return_value=mock_result)

        stats = await service.get_all_student_stats(student_id)

        assert len(stats) == 2


class TestStatsSummary:
    """Tests para resumen de estadísticas."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return StudentStatsService(db=mock_db)

    @pytest.fixture
    def sample_stats(self):
        """Stats de ejemplo."""
        stats = []
        for i, topic in enumerate(list(MedicalTopic)[:5]):
            stat = MagicMock(spec=TopicPerformance)
            stat.topic = topic
            stat.mastery_score = 50.0 + i * 10  # 50, 60, 70, 80, 90
            stat.accuracy_rate = 60.0 + i * 5
            stat.total_questions = 10 + i
            stat.correct_answers = 6 + i
            stat.current_streak = i
            stat.best_streak = i + 2
            stat.performance_level = "intermediate"
            stat.is_strength = stat.mastery_score >= 75
            stat.needs_review = stat.mastery_score < 50
            stat.last_seen = datetime.utcnow() - timedelta(days=i)
            stat.trend = "stable"
            stats.append(stat)
        return stats

    @pytest.mark.asyncio
    async def test_get_student_stats_summary(self, service, mock_db, sample_stats):
        """Obtener resumen de estadísticas."""
        student_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_stats
        mock_db.execute = AsyncMock(return_value=mock_result)

        service.get_all_student_stats = AsyncMock(return_value=sample_stats)

        summary = await service.get_student_stats_summary(student_id)

        assert "overall_score" in summary
        assert "total_questions_answered" in summary
        assert "topics" in summary
        assert len(summary["topics"]) == len(sample_stats)

    @pytest.mark.asyncio
    async def test_summary_calculates_accuracy(self, service, mock_db, sample_stats):
        """Summary calcula precisión correctamente."""
        student_id = uuid4()
        service.get_all_student_stats = AsyncMock(return_value=sample_stats)

        summary = await service.get_student_stats_summary(student_id)

        total_questions = sum(s.total_questions for s in sample_stats)
        total_correct = sum(s.correct_answers for s in sample_stats)
        expected_accuracy = round((total_correct / total_questions * 100), 1)

        assert summary["accuracy_rate"] == expected_accuracy


class TestStatsUpdate:
    """Tests para actualización de estadísticas."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return StudentStatsService(db=mock_db)

    @pytest.fixture
    def existing_stats(self):
        """Stats existentes."""
        stats = MagicMock(spec=TopicPerformance)
        stats.mastery_score = 50.0
        stats.total_questions = 10
        stats.correct_answers = 5
        stats.incorrect_answers = 5
        stats.current_streak = 2
        stats.best_streak = 5
        stats.last_correct = datetime.utcnow() - timedelta(hours=1)
        stats.last_incorrect = datetime.utcnow() - timedelta(days=1)
        stats.last_seen = datetime.utcnow() - timedelta(hours=1)
        stats.is_strength = False
        stats.needs_review = False
        stats.trend = "stable"
        return stats

    @pytest.mark.asyncio
    async def test_update_stats_correct_answer(self, service, mock_db, existing_stats):
        """Actualizar stats con respuesta correcta."""
        student_id = uuid4()

        service.get_or_create_topic_stats = AsyncMock(return_value=existing_stats)

        updated = await service.update_stats_after_answer(
            student_id=student_id,
            topic_str="tumor_staging",
            is_correct=True,
            difficulty=3
        )

        assert updated is not None
        assert existing_stats.total_questions == 11
        assert existing_stats.correct_answers == 6
        assert existing_stats.current_streak == 3

    @pytest.mark.asyncio
    async def test_update_stats_incorrect_answer(self, service, mock_db, existing_stats):
        """Actualizar stats con respuesta incorrecta."""
        student_id = uuid4()

        service.get_or_create_topic_stats = AsyncMock(return_value=existing_stats)

        updated = await service.update_stats_after_answer(
            student_id=student_id,
            topic_str="tumor_staging",
            is_correct=False,
            difficulty=3
        )

        assert updated is not None
        assert existing_stats.total_questions == 11
        assert existing_stats.incorrect_answers == 6
        assert existing_stats.current_streak == 0  # Streak reseteado

    @pytest.mark.asyncio
    async def test_update_stats_updates_best_streak(self, service, mock_db, existing_stats):
        """Best streak se actualiza cuando streak actual lo supera."""
        student_id = uuid4()
        existing_stats.current_streak = 5  # Igual al best

        service.get_or_create_topic_stats = AsyncMock(return_value=existing_stats)

        await service.update_stats_after_answer(
            student_id=student_id,
            topic_str="tumor_staging",
            is_correct=True,
            difficulty=3
        )

        assert existing_stats.current_streak == 6
        assert existing_stats.best_streak == 6

    @pytest.mark.asyncio
    async def test_update_stats_invalid_topic(self, service, mock_db):
        """Topic inválido retorna None."""
        student_id = uuid4()

        result = await service.update_stats_after_answer(
            student_id=student_id,
            topic_str="invalid_topic_xyz",
            is_correct=True,
            difficulty=3
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_stats_none_topic(self, service, mock_db):
        """Topic None retorna None."""
        student_id = uuid4()

        result = await service.update_stats_after_answer(
            student_id=student_id,
            topic_str=None,
            is_correct=True,
            difficulty=3
        )

        assert result is None


class TestMasteryCalculation:
    """Tests para cálculo de mastery score."""

    @pytest.fixture
    def service(self):
        mock_db = AsyncMock()
        return StudentStatsService(db=mock_db)

    def test_mastery_increases_on_correct(self, service):
        """Mastery aumenta con respuesta correcta."""
        new_score = service._calculate_new_mastery(
            current_score=50.0,
            is_correct=True,
            difficulty=3,
            streak=1
        )

        assert new_score > 50.0

    def test_mastery_decreases_on_incorrect(self, service):
        """Mastery disminuye con respuesta incorrecta."""
        new_score = service._calculate_new_mastery(
            current_score=50.0,
            is_correct=False,
            difficulty=3,
            streak=0
        )

        assert new_score < 50.0

    def test_mastery_capped_at_100(self, service):
        """Mastery no excede 100."""
        new_score = service._calculate_new_mastery(
            current_score=99.0,
            is_correct=True,
            difficulty=5,
            streak=10
        )

        assert new_score <= 100.0

    def test_mastery_minimum_at_0(self, service):
        """Mastery no baja de 0."""
        new_score = service._calculate_new_mastery(
            current_score=5.0,
            is_correct=False,
            difficulty=5,
            streak=0
        )

        assert new_score >= 0.0

    def test_high_difficulty_bigger_reward(self, service):
        """Dificultad alta da mayor recompensa."""
        score_easy = service._calculate_new_mastery(
            current_score=50.0,
            is_correct=True,
            difficulty=1,
            streak=0
        )

        score_hard = service._calculate_new_mastery(
            current_score=50.0,
            is_correct=True,
            difficulty=5,
            streak=0
        )

        # Mayor dificultad = mayor aumento
        assert score_hard > score_easy

    def test_streak_bonus(self, service):
        """Streak largo da bonus."""
        score_no_streak = service._calculate_new_mastery(
            current_score=50.0,
            is_correct=True,
            difficulty=3,
            streak=0
        )

        score_with_streak = service._calculate_new_mastery(
            current_score=50.0,
            is_correct=True,
            difficulty=3,
            streak=5
        )

        # Streak da bonus
        assert score_with_streak >= score_no_streak


class TestPersonalizedQuestionTargets:
    """Tests para selección de topics personalizados."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return StudentStatsService(db=mock_db)

    @pytest.fixture
    def varied_stats(self):
        """Stats variadas para probar selección."""
        stats = []

        # Debilidad
        weak = MagicMock(spec=TopicPerformance)
        weak.topic = MedicalTopic.TUMOR_STAGING
        weak.mastery_score = 30.0
        weak.total_questions = 5
        weak.is_strength = False
        weak.needs_review = True
        weak.last_seen = datetime.utcnow() - timedelta(days=1)
        stats.append(weak)

        # Fortaleza
        strong = MagicMock(spec=TopicPerformance)
        strong.topic = MedicalTopic.DIAGNOSIS
        strong.mastery_score = 85.0
        strong.total_questions = 20
        strong.is_strength = True
        strong.needs_review = False
        strong.last_seen = datetime.utcnow() - timedelta(days=7)
        stats.append(strong)

        # Intermedio
        mid = MagicMock(spec=TopicPerformance)
        mid.topic = MedicalTopic.TREATMENT_CHEMO
        mid.mastery_score = 55.0
        mid.total_questions = 10
        mid.is_strength = False
        mid.needs_review = False
        mid.last_seen = datetime.utcnow() - timedelta(days=3)
        stats.append(mid)

        return stats

    @pytest.mark.asyncio
    async def test_get_personalized_targets_returns_correct_count(
        self, service, mock_db, varied_stats
    ):
        """Obtiene el número correcto de targets."""
        student_id = uuid4()
        service.get_all_student_stats = AsyncMock(return_value=varied_stats)

        targets = await service.get_personalized_question_targets(
            student_id=student_id,
            count=4
        )

        # Puede retornar hasta count targets
        assert len(targets) <= 4

    @pytest.mark.asyncio
    async def test_targets_include_topic_reason_difficulty(
        self, service, mock_db, varied_stats
    ):
        """Targets incluyen topic, razón y dificultad."""
        student_id = uuid4()
        service.get_all_student_stats = AsyncMock(return_value=varied_stats)

        targets = await service.get_personalized_question_targets(
            student_id=student_id,
            count=2
        )

        for target in targets:
            assert len(target) == 3  # (topic, reason, difficulty)
            topic, reason, difficulty = target
            assert isinstance(topic, MedicalTopic)
            assert isinstance(reason, str)
            assert isinstance(difficulty, int)
            assert 1 <= difficulty <= 5


# =============================================================================
# Tests de integración
# =============================================================================

class TestStatsServiceIntegration:
    """Tests de integración del servicio de stats."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_full_stats_flow(self, mock_db):
        """Flujo completo: crear, actualizar, consultar."""
        service = StudentStatsService(db=mock_db)
        student_id = uuid4()

        # Mock stats
        stats = MagicMock(spec=TopicPerformance)
        stats.topic = MedicalTopic.TUMOR_STAGING
        stats.mastery_score = 50.0
        stats.total_questions = 0
        stats.correct_answers = 0
        stats.incorrect_answers = 0
        stats.current_streak = 0
        stats.best_streak = 0
        stats.last_correct = None
        stats.last_incorrect = None
        stats.last_seen = None
        stats.is_strength = False
        stats.needs_review = False
        stats.trend = "stable"

        service.get_or_create_topic_stats = AsyncMock(return_value=stats)

        # Simular varias respuestas
        for i in range(5):
            await service.update_stats_after_answer(
                student_id=student_id,
                topic_str="tumor_staging",
                is_correct=(i % 2 == 0),  # Alternar correcto/incorrecto
                difficulty=3
            )

        assert stats.total_questions == 5
        assert stats.correct_answers == 3  # Días 0, 2, 4
        assert stats.incorrect_answers == 2  # Días 1, 3

    @pytest.mark.asyncio
    async def test_all_topics_can_be_tracked(self, mock_db):
        """Todos los topics pueden ser tracked."""
        service = StudentStatsService(db=mock_db)
        student_id = uuid4()

        for topic in MedicalTopic:
            stats = MagicMock(spec=TopicPerformance)
            stats.topic = topic
            stats.mastery_score = 50.0
            stats.total_questions = 0
            stats.correct_answers = 0
            stats.incorrect_answers = 0
            stats.current_streak = 0
            stats.best_streak = 0
            stats.last_correct = None
            stats.last_incorrect = None
            stats.last_seen = None
            stats.is_strength = False
            stats.needs_review = False
            stats.trend = "stable"

            service.get_or_create_topic_stats = AsyncMock(return_value=stats)

            result = await service.update_stats_after_answer(
                student_id=student_id,
                topic_str=topic.value,
                is_correct=True,
                difficulty=3
            )

            assert result is not None

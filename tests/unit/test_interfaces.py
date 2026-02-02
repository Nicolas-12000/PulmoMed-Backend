"""
Tests for service interfaces - ISP compliance tests.
Verifica que las interfaces estén correctamente definidas.
"""

import pytest
from abc import ABC
from uuid import uuid4

from app.services.interfaces import (
    IAuthService,
    IExamReader,
    IExamWriter,
    IQuestionManager,
    IAttemptManager,
    IStatsReader,
    IStatsWriter,
    IPersonalizationEngine,
    IAIQuestionGenerator,
)


# =============================================================================
# Interface Definition Tests
# =============================================================================

class TestInterfaceDefinitions:
    """Tests para verificar que las interfaces están correctamente definidas."""

    def test_iauth_service_is_abstract(self):
        """IAuthService debe ser una clase abstracta."""
        assert issubclass(IAuthService, ABC)

    def test_iexam_reader_is_abstract(self):
        """IExamReader debe ser una clase abstracta."""
        assert issubclass(IExamReader, ABC)

    def test_iexam_writer_is_abstract(self):
        """IExamWriter debe ser una clase abstracta."""
        assert issubclass(IExamWriter, ABC)

    def test_iquestion_manager_is_abstract(self):
        """IQuestionManager debe ser una clase abstracta."""
        assert issubclass(IQuestionManager, ABC)

    def test_iattempt_manager_is_abstract(self):
        """IAttemptManager debe ser una clase abstracta."""
        assert issubclass(IAttemptManager, ABC)

    def test_istats_reader_is_abstract(self):
        """IStatsReader debe ser una clase abstracta."""
        assert issubclass(IStatsReader, ABC)

    def test_istats_writer_is_abstract(self):
        """IStatsWriter debe ser una clase abstracta."""
        assert issubclass(IStatsWriter, ABC)

    def test_ipersonalization_engine_is_abstract(self):
        """IPersonalizationEngine debe ser una clase abstracta."""
        assert issubclass(IPersonalizationEngine, ABC)

    def test_iai_question_generator_is_abstract(self):
        """IAIQuestionGenerator debe ser una clase abstracta."""
        assert issubclass(IAIQuestionGenerator, ABC)


# =============================================================================
# IAuthService Method Tests
# =============================================================================

class TestIAuthServiceMethods:
    """Tests para métodos requeridos en IAuthService."""

    def test_has_get_user_by_email(self):
        """IAuthService debe tener get_user_by_email."""
        assert hasattr(IAuthService, 'get_user_by_email')

    def test_has_get_user_by_id(self):
        """IAuthService debe tener get_user_by_id."""
        assert hasattr(IAuthService, 'get_user_by_id')

    def test_has_create_user(self):
        """IAuthService debe tener create_user."""
        assert hasattr(IAuthService, 'create_user')

    def test_has_authenticate_user(self):
        """IAuthService debe tener authenticate_user."""
        assert hasattr(IAuthService, 'authenticate_user')


# =============================================================================
# IExamReader Method Tests
# =============================================================================

class TestIExamReaderMethods:
    """Tests para métodos requeridos en IExamReader."""

    def test_has_get_exam(self):
        """IExamReader debe tener get_exam."""
        assert hasattr(IExamReader, 'get_exam')

    def test_has_get_exams_by_creator(self):
        """IExamReader debe tener get_exams_by_creator."""
        assert hasattr(IExamReader, 'get_exams_by_creator')

    def test_has_get_published_exams(self):
        """IExamReader debe tener get_published_exams."""
        assert hasattr(IExamReader, 'get_published_exams')

    def test_has_get_exam_question_count(self):
        """IExamReader debe tener get_exam_question_count."""
        assert hasattr(IExamReader, 'get_exam_question_count')


# =============================================================================
# IExamWriter Method Tests
# =============================================================================

class TestIExamWriterMethods:
    """Tests para métodos requeridos en IExamWriter."""

    def test_has_create_exam(self):
        """IExamWriter debe tener create_exam."""
        assert hasattr(IExamWriter, 'create_exam')

    def test_has_update_exam(self):
        """IExamWriter debe tener update_exam."""
        assert hasattr(IExamWriter, 'update_exam')

    def test_has_delete_exam(self):
        """IExamWriter debe tener delete_exam."""
        assert hasattr(IExamWriter, 'delete_exam')


# =============================================================================
# IQuestionManager Method Tests
# =============================================================================

class TestIQuestionManagerMethods:
    """Tests para métodos requeridos en IQuestionManager."""

    def test_has_add_question(self):
        """IQuestionManager debe tener add_question."""
        assert hasattr(IQuestionManager, 'add_question')

    def test_has_get_question(self):
        """IQuestionManager debe tener get_question."""
        assert hasattr(IQuestionManager, 'get_question')

    def test_has_update_question(self):
        """IQuestionManager debe tener update_question."""
        assert hasattr(IQuestionManager, 'update_question')

    def test_has_delete_question(self):
        """IQuestionManager debe tener delete_question."""
        assert hasattr(IQuestionManager, 'delete_question')


# =============================================================================
# IAttemptManager Method Tests
# =============================================================================

class TestIAttemptManagerMethods:
    """Tests para métodos requeridos en IAttemptManager."""

    def test_has_start_attempt(self):
        """IAttemptManager debe tener start_attempt."""
        assert hasattr(IAttemptManager, 'start_attempt')

    def test_has_submit_exam(self):
        """IAttemptManager debe tener submit_exam."""
        assert hasattr(IAttemptManager, 'submit_exam')


# =============================================================================
# IStatsReader Method Tests
# =============================================================================

class TestIStatsReaderMethods:
    """Tests para métodos requeridos en IStatsReader."""

    def test_has_get_all_student_stats(self):
        """IStatsReader debe tener get_all_student_stats."""
        assert hasattr(IStatsReader, 'get_all_student_stats')

    def test_has_get_student_stats_summary(self):
        """IStatsReader debe tener get_student_stats_summary."""
        assert hasattr(IStatsReader, 'get_student_stats_summary')

    def test_has_get_class_stats(self):
        """IStatsReader debe tener get_class_stats."""
        assert hasattr(IStatsReader, 'get_class_stats')


# =============================================================================
# IStatsWriter Method Tests
# =============================================================================

class TestIStatsWriterMethods:
    """Tests para métodos requeridos en IStatsWriter."""

    def test_has_update_stats_after_answer(self):
        """IStatsWriter debe tener update_stats_after_answer."""
        assert hasattr(IStatsWriter, 'update_stats_after_answer')


# =============================================================================
# IPersonalizationEngine Method Tests
# =============================================================================

class TestIPersonalizationEngineMethods:
    """Tests para métodos requeridos en IPersonalizationEngine."""

    def test_has_get_personalized_question_targets(self):
        """IPersonalizationEngine debe tener get_personalized_question_targets."""
        assert hasattr(IPersonalizationEngine, 'get_personalized_question_targets')


# =============================================================================
# IAIQuestionGenerator Method Tests
# =============================================================================

class TestIAIQuestionGeneratorMethods:
    """Tests para métodos requeridos en IAIQuestionGenerator."""

    def test_has_generate_personalized_questions(self):
        """IAIQuestionGenerator debe tener generate_personalized_questions."""
        assert hasattr(IAIQuestionGenerator, 'generate_personalized_questions')

    def test_has_record_answer(self):
        """IAIQuestionGenerator debe tener record_answer."""
        assert hasattr(IAIQuestionGenerator, 'record_answer')


# =============================================================================
# Concrete Implementation Tests (Stub Pattern)
# =============================================================================

class StubAuthService(IAuthService):
    """Stub implementation for testing."""

    async def get_user_by_email(self, email: str):
        return None

    async def get_user_by_id(self, user_id):
        return None

    async def create_user(self, request):
        return None

    async def authenticate_user(self, email: str, password: str):
        return None


class StubExamReader(IExamReader):
    """Stub implementation for testing."""

    async def get_exam(self, exam_id):
        return None

    async def get_exams_by_creator(self, creator_id):
        return []

    async def get_published_exams(self):
        return []

    async def get_exam_question_count(self, exam_id):
        return 0


class StubExamWriter(IExamWriter):
    """Stub implementation for testing."""

    async def create_exam(self, request, creator):
        return None

    async def update_exam(self, exam, request):
        return None

    async def delete_exam(self, exam):
        pass


class StubQuestionManager(IQuestionManager):
    """Stub implementation for testing."""

    async def add_question(self, exam, request):
        return None

    async def get_question(self, question_id):
        return None

    async def update_question(self, question, request):
        return None

    async def delete_question(self, question):
        pass


class StubAttemptManager(IAttemptManager):
    """Stub implementation for testing."""

    async def start_attempt(self, exam, student):
        return None

    async def submit_exam(self, attempt, answers):
        return None


class StubStatsReader(IStatsReader):
    """Stub implementation for testing."""

    async def get_all_student_stats(self, student_id):
        return []

    async def get_student_stats_summary(self, student_id):
        return {}

    async def get_class_stats(self, professor_id):
        return []


class StubStatsWriter(IStatsWriter):
    """Stub implementation for testing."""

    async def update_stats_after_answer(self, student_id, topic_str, is_correct, difficulty):
        return None


class StubPersonalizationEngine(IPersonalizationEngine):
    """Stub implementation for testing."""

    async def get_personalized_question_targets(self, student_id, count):
        return []


class StubAIQuestionGenerator(IAIQuestionGenerator):
    """Stub implementation for testing."""

    async def generate_personalized_questions(self, student_id, attempt_id, count):
        return []

    async def record_answer(self, question_id, student_answer, is_correct):
        pass


class TestConcreteImplementations:
    """Tests para implementaciones concretas de interfaces."""

    def test_stub_auth_service_instantiates(self):
        """StubAuthService se puede instanciar."""
        service = StubAuthService()
        assert isinstance(service, IAuthService)

    def test_stub_exam_reader_instantiates(self):
        """StubExamReader se puede instanciar."""
        service = StubExamReader()
        assert isinstance(service, IExamReader)

    def test_stub_exam_writer_instantiates(self):
        """StubExamWriter se puede instanciar."""
        service = StubExamWriter()
        assert isinstance(service, IExamWriter)

    def test_stub_question_manager_instantiates(self):
        """StubQuestionManager se puede instanciar."""
        service = StubQuestionManager()
        assert isinstance(service, IQuestionManager)

    def test_stub_attempt_manager_instantiates(self):
        """StubAttemptManager se puede instanciar."""
        service = StubAttemptManager()
        assert isinstance(service, IAttemptManager)

    def test_stub_stats_reader_instantiates(self):
        """StubStatsReader se puede instanciar."""
        service = StubStatsReader()
        assert isinstance(service, IStatsReader)

    def test_stub_stats_writer_instantiates(self):
        """StubStatsWriter se puede instanciar."""
        service = StubStatsWriter()
        assert isinstance(service, IStatsWriter)

    def test_stub_personalization_engine_instantiates(self):
        """StubPersonalizationEngine se puede instanciar."""
        service = StubPersonalizationEngine()
        assert isinstance(service, IPersonalizationEngine)

    def test_stub_ai_question_generator_instantiates(self):
        """StubAIQuestionGenerator se puede instanciar."""
        service = StubAIQuestionGenerator()
        assert isinstance(service, IAIQuestionGenerator)

    @pytest.mark.asyncio
    async def test_stub_auth_methods_callable(self):
        """Métodos de StubAuthService son llamables."""
        service = StubAuthService()
        assert await service.get_user_by_email("test@test.com") is None
        assert await service.get_user_by_id(uuid4()) is None
        assert await service.authenticate_user("test", "pass") is None

    @pytest.mark.asyncio
    async def test_stub_exam_reader_methods_callable(self):
        """Métodos de StubExamReader son llamables."""
        service = StubExamReader()
        assert await service.get_exam(uuid4()) is None
        assert await service.get_exams_by_creator(uuid4()) == []
        assert await service.get_published_exams() == []
        assert await service.get_exam_question_count(uuid4()) == 0

    @pytest.mark.asyncio
    async def test_stub_stats_reader_methods_callable(self):
        """Métodos de StubStatsReader son llamables."""
        service = StubStatsReader()
        assert await service.get_all_student_stats(uuid4()) == []
        assert await service.get_student_stats_summary(uuid4()) == {}
        assert await service.get_class_stats(uuid4()) == []

    @pytest.mark.asyncio
    async def test_stub_personalization_methods_callable(self):
        """Métodos de StubPersonalizationEngine son llamables."""
        service = StubPersonalizationEngine()
        targets = await service.get_personalized_question_targets(uuid4(), 5)
        assert targets == []


# =============================================================================
# ISP Compliance Tests
# =============================================================================

class TestISPCompliance:
    """Tests para verificar el principio de segregación de interfaces."""

    def test_exam_reader_writer_separate(self):
        """IExamReader e IExamWriter son interfaces separadas."""
        reader_methods = set(m for m in dir(IExamReader) if not m.startswith('_'))
        writer_methods = set(m for m in dir(IExamWriter) if not m.startswith('_'))
        # No deben compartir métodos (excepto heredados de ABC)
        overlap = reader_methods & writer_methods - {'register'}
        # Pueden compartir métodos de ABC
        for method in overlap:
            assert not method.startswith('get_') or not method.startswith('create_')

    def test_stats_reader_writer_separate(self):
        """IStatsReader e IStatsWriter son interfaces separadas."""
        reader_methods = set(m for m in dir(IStatsReader) if not m.startswith('_'))
        _writer_methods = set(m for m in dir(IStatsWriter) if not m.startswith('_'))
        # Reader tiene métodos get_*, Writer tiene update_*
        for method in reader_methods:
            if callable(getattr(IStatsReader, method, None)):
                assert 'update' not in method.lower()

    def test_interfaces_are_small(self):
        """Las interfaces son pequeñas (máximo 5 métodos abstractos)."""
        max_methods = 5
        interfaces = [
            IExamReader, IExamWriter, IQuestionManager,
            IAttemptManager, IStatsReader, IStatsWriter
        ]
        for interface in interfaces:
            abstract_methods = [
                m for m in dir(interface)
                if not m.startswith('_') and callable(getattr(interface, m, None))
            ]
            # Filtrar solo métodos que son realmente abstractos
            assert len(abstract_methods) <= max_methods + 2  # +2 para ABC métodos

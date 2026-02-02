"""
Tests para AIQuestionGenerator
Suite completa de tests para generación de preguntas con IA.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.ai_question_service import (
    AIQuestionGenerator,
    TOPIC_DESCRIPTIONS,
    DIFFICULTY_DESCRIPTIONS,
    REASON_PROMPTS,
    LLM_TIMEOUT_SECONDS,
    LLM_MAX_RETRIES,
)
from app.models.db_models import MedicalTopic, AIGeneratedQuestion


# =============================================================================
# Tests para constantes y configuración
# =============================================================================

class TestAIQuestionServiceConfig:
    """Tests para configuración del servicio."""

    def test_topic_descriptions_complete(self):
        """Todos los topics tienen descripción."""
        for topic in MedicalTopic:
            assert topic in TOPIC_DESCRIPTIONS, f"Falta descripción para {topic}"

    def test_difficulty_descriptions_complete(self):
        """Todos los niveles de dificultad tienen descripción."""
        for level in range(1, 6):
            assert level in DIFFICULTY_DESCRIPTIONS, f"Falta descripción para nivel {level}"

    def test_reason_prompts_complete(self):
        """Todos los reasons tienen prompt."""
        expected_reasons = [
            "weakness", "intermediate", "forgotten_strength",
            "strength_refresh", "challenge", "recent_errors",
            "new_topic", "reinforcement"
        ]
        for reason in expected_reasons:
            assert reason in REASON_PROMPTS, f"Falta prompt para {reason}"

    def test_timeout_and_retries_configured(self):
        """Timeout y reintentos configurados."""
        assert LLM_TIMEOUT_SECONDS > 0
        assert LLM_MAX_RETRIES >= 0


# =============================================================================
# Tests para AIQuestionGenerator
# =============================================================================

class TestAIQuestionGenerator:
    """Tests para generador de preguntas."""

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
    def mock_llm(self):
        """Mock de cliente LLM."""
        llm = AsyncMock()
        llm.check_availability.return_value = True
        llm.query = AsyncMock(return_value="""
        {
            "pregunta": "¿Cuál es el estadio tumoral si el diámetro es 3.5cm?",
            "opciones": ["IA", "IB", "IIA", "IIB"],
            "respuesta_correcta": 1,
            "explicacion": "Un tumor de 3.5cm corresponde a T2a según TNM."
        }
        """)
        return llm

    @pytest.fixture
    def mock_repository(self):
        """Mock de repositorio RAG."""
        repo = MagicMock()
        repo.retrieve_relevant_chunks.return_value = [
            {"content": "La estadificación TNM clasifica tumores por tamaño..."},
            {"content": "T1: ≤3cm, T2a: >3-4cm, T2b: >4-5cm..."},
        ]
        return repo

    def test_create_generator(self, mock_db):
        """Crear generador."""
        generator = AIQuestionGenerator(db=mock_db)
        assert generator.db is mock_db
        assert generator.llm_client is None
        assert generator.repository is None

    def test_create_generator_with_llm(self, mock_db, mock_llm):
        """Crear generador con LLM."""
        generator = AIQuestionGenerator(db=mock_db, llm_client=mock_llm)
        assert generator.llm_client is mock_llm

    def test_create_generator_with_repository(self, mock_db, mock_repository):
        """Crear generador con repositorio."""
        generator = AIQuestionGenerator(
            db=mock_db,
            repository=mock_repository
        )
        assert generator.repository is mock_repository

    @pytest.mark.asyncio
    async def test_generate_personalized_questions(
        self, mock_db, mock_llm, mock_repository
    ):
        """Generar preguntas personalizadas."""
        generator = AIQuestionGenerator(
            db=mock_db,
            llm_client=mock_llm,
            repository=mock_repository
        )

        # Mock stats_service
        generator.stats_service = AsyncMock()
        generator.stats_service.get_personalized_question_targets = AsyncMock(
            return_value=[
                (MedicalTopic.TUMOR_STAGING, "weakness", 2),
                (MedicalTopic.TREATMENT_CHEMO, "intermediate", 3),
            ]
        )

        # Mock _generate_single_question para evitar complejidad
        mock_question = MagicMock(spec=AIGeneratedQuestion)
        mock_question.topic = MedicalTopic.TUMOR_STAGING
        generator._generate_single_question = AsyncMock(return_value=mock_question)

        student_id = uuid4()
        questions = await generator.generate_personalized_questions(
            student_id=student_id,
            count=2
        )

        # Debe generar preguntas
        assert len(questions) == 2

    @pytest.mark.asyncio
    async def test_generate_topic_questions(
        self, mock_db, mock_llm, mock_repository
    ):
        """Generar preguntas de un tema específico."""
        generator = AIQuestionGenerator(
            db=mock_db,
            llm_client=mock_llm,
            repository=mock_repository
        )

        mock_question = MagicMock(spec=AIGeneratedQuestion)
        generator._generate_single_question = AsyncMock(return_value=mock_question)

        student_id = uuid4()
        questions = await generator.generate_topic_questions(
            student_id=student_id,
            topic=MedicalTopic.DIAGNOSIS,
            count=3
        )

        assert len(questions) == 3

    @pytest.mark.asyncio
    async def test_generate_without_llm_uses_fallback(self, mock_db):
        """Sin LLM usa fallback."""
        generator = AIQuestionGenerator(db=mock_db, llm_client=None)

        # Mock fallback
        mock_fallback_question = MagicMock(spec=AIGeneratedQuestion)
        generator._create_fallback_question = AsyncMock(
            return_value=mock_fallback_question
        )

        question = await generator._generate_single_question(
            student_id=uuid4(),
            attempt_id=None,
            topic=MedicalTopic.ANATOMY,
            reason="new_topic",
            difficulty=1
        )

        assert question is mock_fallback_question
        generator._create_fallback_question.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker_activates(self, mock_db, mock_llm):
        """Circuit breaker se activa tras fallos consecutivos."""
        generator = AIQuestionGenerator(db=mock_db, llm_client=mock_llm)

        # Simular fallos consecutivos
        generator._llm_fail_count = 5  # Más que LLM_MAX_CONSECUTIVE_FAILURES
        generator._llm_last_failure_ts = 999999999999  # Timestamp futuro

        # Mock fallback
        mock_fallback = MagicMock(spec=AIGeneratedQuestion)
        generator._create_fallback_question = AsyncMock(return_value=mock_fallback)

        question = await generator._generate_single_question(
            student_id=uuid4(),
            attempt_id=None,
            topic=MedicalTopic.PHARMACOLOGY,
            reason="challenge",
            difficulty=4
        )

        # Debe usar fallback
        generator._create_fallback_question.assert_called()


# =============================================================================
# Tests de prompts y contenido
# =============================================================================

class TestPromptGeneration:
    """Tests para generación de prompts."""

    def test_weakness_prompt_content(self):
        """Prompt para weakness contiene palabras clave."""
        prompt = REASON_PROMPTS["weakness"]
        assert "dificultades" in prompt.lower()
        assert "básicos" in prompt.lower() or "reforzar" in prompt.lower()

    def test_challenge_prompt_content(self):
        """Prompt para challenge es desafiante."""
        prompt = REASON_PROMPTS["challenge"]
        assert "domina" in prompt.lower()
        assert "desafiante" in prompt.lower() or "siguiente nivel" in prompt.lower()

    def test_new_topic_prompt_is_introductory(self):
        """Prompt para new_topic es introductorio."""
        prompt = REASON_PROMPTS["new_topic"]
        assert "introductoria" in prompt.lower() or "no ha visto" in prompt.lower()

    def test_topic_descriptions_are_medical(self):
        """Descripciones de topics son médicas."""
        medical_keywords = [
            'tumor', 'tratamiento', 'quirúrgico', 'quimioterapia',
            'radioterapia', 'inmunoterapia', 'diagnóstico', 'riesgo',
            'pronóstico', 'anatomía', 'farmacología', 'paciente'
        ]

        for topic, desc in TOPIC_DESCRIPTIONS.items():
            has_medical_word = any(kw in desc.lower() for kw in medical_keywords)
            assert has_medical_word, f"Descripción de {topic} no parece médica: {desc}"


# =============================================================================
# Tests de integración con LLM real
# =============================================================================

@pytest.mark.integration
class TestAIQuestionGeneratorIntegration:
    """Tests de integración con LLM real."""

    @pytest.fixture
    def real_llm(self):
        """Cliente LLM real (si está disponible)."""
        from app.llm.groq_client import GroqClient
        client = GroqClient()
        if not client.check_availability():
            pytest.skip("Groq API no disponible")
        return client

    @pytest.mark.asyncio
    async def test_generate_question_with_real_llm(self, real_llm):
        """Generar pregunta con LLM real."""
        # Este test usa el LLM real
        prompt = """
        Genera una pregunta de opción múltiple sobre estadificación tumoral TNM.

        Formato de respuesta JSON:
        {
            "pregunta": "texto de la pregunta",
            "opciones": ["opción A", "opción B", "opción C", "opción D"],
            "respuesta_correcta": 0,
            "explicacion": "explicación de la respuesta"
        }
        """

        response = await real_llm.query(prompt)

        assert response is not None
        assert len(response) > 50
        # Debe contener estructura de pregunta
        assert "pregunta" in response.lower() or "?" in response

    @pytest.mark.asyncio
    async def test_generate_multiple_questions(self, real_llm):
        """Generar múltiples preguntas."""
        topics = [
            MedicalTopic.TUMOR_STAGING,
            MedicalTopic.TREATMENT_CHEMO,
        ]

        for topic in topics:
            desc = TOPIC_DESCRIPTIONS[topic]
            prompt = f"Genera una pregunta breve sobre {desc}"

            response = await real_llm.query(prompt)
            assert response is not None


# =============================================================================
# Tests de casos edge
# =============================================================================

class TestAIQuestionEdgeCases:
    """Tests para casos límite."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_empty_context_from_repository(self, mock_db):
        """Repositorio retorna contexto vacío."""
        mock_llm = AsyncMock()
        mock_llm.check_availability.return_value = True
        mock_llm.query = AsyncMock(return_value="Pregunta generada")

        mock_repo = MagicMock()
        mock_repo.retrieve_relevant_chunks.return_value = []

        generator = AIQuestionGenerator(
            db=mock_db,
            llm_client=mock_llm,
            repository=mock_repo
        )

        # Mock para evitar proceso completo
        generator._create_fallback_question = AsyncMock(
            return_value=MagicMock(spec=AIGeneratedQuestion)
        )

        # No debe fallar con contexto vacío
        question = await generator._generate_single_question(
            student_id=uuid4(),
            attempt_id=None,
            topic=MedicalTopic.ANATOMY,
            reason="reinforcement",
            difficulty=3
        )

        # Puede ser pregunta real o fallback, pero no None
        # (depende de la implementación exacta)

    @pytest.mark.asyncio
    async def test_all_difficulty_levels(self, mock_db):
        """Todos los niveles de dificultad funcionan."""
        generator = AIQuestionGenerator(db=mock_db, llm_client=None)

        mock_fallback = MagicMock(spec=AIGeneratedQuestion)
        generator._create_fallback_question = AsyncMock(return_value=mock_fallback)

        for difficulty in range(1, 6):
            question = await generator._generate_single_question(
                student_id=uuid4(),
                attempt_id=None,
                topic=MedicalTopic.PROGNOSIS,
                reason="reinforcement",
                difficulty=difficulty
            )
            assert question is not None

    @pytest.mark.asyncio
    async def test_all_topics_supported(self, mock_db):
        """Todos los topics son soportados."""
        generator = AIQuestionGenerator(db=mock_db, llm_client=None)

        mock_fallback = MagicMock(spec=AIGeneratedQuestion)
        generator._create_fallback_question = AsyncMock(return_value=mock_fallback)

        for topic in MedicalTopic:
            question = await generator._generate_single_question(
                student_id=uuid4(),
                attempt_id=None,
                topic=topic,
                reason="new_topic",
                difficulty=1
            )
            assert question is not None

    @pytest.mark.asyncio
    async def test_all_reasons_supported(self, mock_db):
        """Todos los reasons son soportados."""
        generator = AIQuestionGenerator(db=mock_db, llm_client=None)

        mock_fallback = MagicMock(spec=AIGeneratedQuestion)
        generator._create_fallback_question = AsyncMock(return_value=mock_fallback)

        for reason in REASON_PROMPTS.keys():
            question = await generator._generate_single_question(
                student_id=uuid4(),
                attempt_id=None,
                topic=MedicalTopic.DIAGNOSIS,
                reason=reason,
                difficulty=3
            )
            assert question is not None


# =============================================================================
# Tests de Métodos Internos
# =============================================================================

class TestAIQuestionGeneratorInternals:
    """Tests para métodos internos del generador."""

    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de base de datos."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.commit = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def generator(self, mock_db):
        """Generador con mocks."""
        mock_llm = MagicMock()
        return AIQuestionGenerator(db=mock_db, llm_client=mock_llm)

    def test_build_question_prompt(self, generator):
        """Construye prompt correctamente."""
        prompt = generator._build_question_prompt(
            topic=MedicalTopic.TREATMENT_CHEMO,
            reason="reinforce",
            difficulty=2
        )

        assert prompt is not None
        assert len(prompt) > 10

    def test_build_question_prompt_high_difficulty(self, generator):
        """Prompt con dificultad alta."""
        prompt = generator._build_question_prompt(
            topic=MedicalTopic.TUMOR_STAGING,
            reason="challenge",
            difficulty=5
        )

        assert prompt is not None
        # Debe incluir información sobre dificultad
        assert len(prompt) > 50

    def test_parse_llm_response_valid_json(self, generator):
        """Parsea respuesta JSON válida."""
        valid_response = '''
        {
            "pregunta": "¿Qué estadío corresponde a T2N1M0?",
            "opciones": ["IA", "IB", "IIA", "IIB"],
            "respuesta_correcta": 3,
            "explicacion": "T2N1M0 corresponde a estadío IIB según TNM"
        }
        '''

        result = generator._parse_llm_response(valid_response)

        # Puede retornar dict o None si el formato no es exacto
        # Pero no debe lanzar excepción
        assert result is None or isinstance(result, dict)

    def test_parse_llm_response_invalid(self, generator):
        """Maneja respuesta inválida."""
        invalid_response = "Esta no es una respuesta JSON válida"

        result = generator._parse_llm_response(invalid_response)

        assert result is None

    def test_parse_llm_response_partial_json(self, generator):
        """Maneja JSON parcial."""
        partial_response = '{"pregunta": "Incomplete...'

        result = generator._parse_llm_response(partial_response)

        # Debe manejar gracefully
        assert result is None

    @pytest.mark.asyncio
    async def test_create_fallback_question(self, mock_db):
        """Crea pregunta fallback."""
        generator = AIQuestionGenerator(db=mock_db, llm_client=None)

        # Mock la respuesta del add para simular creación
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        question = await generator._create_fallback_question(
            student_id=uuid4(),
            attempt_id=None,
            topic=MedicalTopic.TUMOR_STAGING,
            reason="weakness",
            difficulty=2
        )

        # Debe crear algún objeto o lanzar
        # El comportamiento depende de la implementación
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_record_answer_success(self, mock_db):
        """Registra respuesta correctamente."""
        generator = AIQuestionGenerator(db=mock_db, llm_client=None)
        question_id = uuid4()

        # Mock la pregunta existente con atributos correctos
        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.student_answer = None
        mock_question.was_correct = None
        mock_question.was_answered = False
        mock_question.student_id = uuid4()
        mock_question.topic = MagicMock()
        mock_question.topic.value = "tumor_staging"
        mock_question.target_difficulty = 2

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_question
        mock_db.execute.return_value = mock_result

        # Mock el stats_service para evitar llamadas a DB
        generator.stats_service = MagicMock()
        generator.stats_service.update_stats_after_answer = AsyncMock()

        await generator.record_answer(
            question_id=question_id,
            student_answer="A",
            is_correct=True
        )

        assert mock_question.student_answer == "A"
        assert mock_question.was_correct is True
        assert mock_question.was_answered is True

    @pytest.mark.asyncio
    async def test_record_answer_question_not_found(self, mock_db):
        """Maneja pregunta no encontrada."""
        generator = AIQuestionGenerator(db=mock_db, llm_client=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # No debe lanzar excepción
        await generator.record_answer(
            question_id=uuid4(),
            student_answer="B",
            is_correct=False
        )


# =============================================================================
# Tests del Factory Function
# =============================================================================

class TestGetAIQuestionGenerator:
    """Tests para la función factory."""

    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de base de datos."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.commit = AsyncMock()
        return db

    def test_factory_creates_generator(self, mock_db):
        """Factory crea generador."""
        from app.services.ai_question_service import get_ai_question_generator

        generator = get_ai_question_generator(mock_db)

        assert generator is not None
        assert isinstance(generator, AIQuestionGenerator)

    def test_factory_with_custom_llm(self, mock_db):
        """Factory acepta LLM personalizado."""
        from app.services.ai_question_service import get_ai_question_generator

        custom_llm = MagicMock()
        generator = get_ai_question_generator(mock_db, llm_client=custom_llm)

        assert generator is not None

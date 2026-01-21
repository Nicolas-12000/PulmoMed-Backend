"""
Service Interfaces - Abstract Base Classes
Interfaces para servicios siguiendo Interface Segregation Principle (ISP)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.models.db_models import (
    AIGeneratedQuestion,
    Exam,
    ExamAttempt,
    MedicalTopic,
    Question,
    TopicPerformance,
    User,
)
from app.schemas.auth_schemas import UserRegisterRequest
from app.schemas.exam_schemas import (
    AnswerSubmit,
    ExamCreate,
    ExamUpdate,
    QuestionCreate,
    QuestionUpdate,
)


# =============================================================================
# AUTH SERVICE INTERFACE
# =============================================================================

class IAuthService(ABC):
    """Interface para servicio de autenticación"""

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Busca usuario por email"""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Busca usuario por ID"""
        pass

    @abstractmethod
    async def create_user(self, request: UserRegisterRequest) -> User:
        """Crea un nuevo usuario"""
        pass

    @abstractmethod
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """Autentica usuario por credenciales"""
        pass


# =============================================================================
# EXAM SERVICE INTERFACE
# =============================================================================

class IExamReader(ABC):
    """Interface para lectura de exámenes (Query)"""

    @abstractmethod
    async def get_exam(self, exam_id: UUID) -> Optional[Exam]:
        """Obtiene un examen por ID"""
        pass

    @abstractmethod
    async def get_exams_by_creator(self, creator_id: UUID) -> List[Exam]:
        """Lista exámenes de un creador"""
        pass

    @abstractmethod
    async def get_published_exams(self) -> List[Exam]:
        """Lista exámenes publicados"""
        pass

    @abstractmethod
    async def get_exam_question_count(self, exam_id: UUID) -> int:
        """Cuenta preguntas de un examen"""
        pass


class IExamWriter(ABC):
    """Interface para escritura de exámenes (Command)"""

    @abstractmethod
    async def create_exam(self, request: ExamCreate, creator: User) -> Exam:
        """Crea un examen"""
        pass

    @abstractmethod
    async def update_exam(self, exam: Exam, request: ExamUpdate) -> Exam:
        """Actualiza un examen"""
        pass

    @abstractmethod
    async def delete_exam(self, exam: Exam) -> None:
        """Elimina un examen"""
        pass


class IQuestionManager(ABC):
    """Interface para gestión de preguntas"""

    @abstractmethod
    async def add_question(self, exam: Exam, request: QuestionCreate) -> Question:
        """Agrega pregunta a un examen"""
        pass

    @abstractmethod
    async def get_question(self, question_id: UUID) -> Optional[Question]:
        """Obtiene pregunta por ID"""
        pass

    @abstractmethod
    async def update_question(
        self,
        question: Question,
        request: QuestionUpdate
    ) -> Question:
        """Actualiza una pregunta"""
        pass

    @abstractmethod
    async def delete_question(self, question: Question) -> None:
        """Elimina una pregunta"""
        pass


class IAttemptManager(ABC):
    """Interface para gestión de intentos de examen"""

    @abstractmethod
    async def start_attempt(self, exam: Exam, student: User) -> ExamAttempt:
        """Inicia un intento de examen"""
        pass

    @abstractmethod
    async def submit_exam(
        self,
        attempt: ExamAttempt,
        answers: List[AnswerSubmit]
    ) -> ExamAttempt:
        """Envía un examen con respuestas"""
        pass


# =============================================================================
# STATS SERVICE INTERFACE
# =============================================================================

class IStatsReader(ABC):
    """Interface para lectura de estadísticas"""

    @abstractmethod
    async def get_all_student_stats(
        self,
        student_id: UUID
    ) -> List[TopicPerformance]:
        """Obtiene todas las stats de un estudiante"""
        pass

    @abstractmethod
    async def get_student_stats_summary(self, student_id: UUID) -> Dict:
        """Obtiene resumen de stats"""
        pass

    @abstractmethod
    async def get_class_stats(self, professor_id: UUID) -> List[Dict]:
        """Obtiene stats de la clase"""
        pass


class IStatsWriter(ABC):
    """Interface para escritura de estadísticas"""

    @abstractmethod
    async def update_stats_after_answer(
        self,
        student_id: UUID,
        topic_str: Optional[str],
        is_correct: bool,
        difficulty: int
    ) -> Optional[TopicPerformance]:
        """Actualiza stats después de responder"""
        pass


class IPersonalizationEngine(ABC):
    """Interface para motor de personalización"""

    @abstractmethod
    async def get_personalized_question_targets(
        self,
        student_id: UUID,
        count: int
    ) -> List[Tuple[MedicalTopic, str, int]]:
        """Obtiene targets para preguntas personalizadas"""
        pass


# =============================================================================
# AI QUESTION SERVICE INTERFACE
# =============================================================================

class IAIQuestionGenerator(ABC):
    """Interface para generador de preguntas IA"""

    @abstractmethod
    async def generate_personalized_questions(
        self,
        student_id: UUID,
        attempt_id: Optional[UUID],
        count: int
    ) -> List[AIGeneratedQuestion]:
        """Genera preguntas personalizadas"""
        pass

    @abstractmethod
    async def record_answer(
        self,
        question_id: UUID,
        student_answer: str,
        is_correct: bool
    ) -> None:
        """Registra respuesta a pregunta IA"""
        pass

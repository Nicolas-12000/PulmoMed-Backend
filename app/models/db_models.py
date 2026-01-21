"""
Database Models - SQLAlchemy ORM
Modelos para Users, Exams, Questions, y Answers
"""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, PyEnum):
    """Roles de usuario en el sistema"""
    STUDENT = "student"
    PROFESSOR = "professor"
    ADMIN = "admin"


class EnrollmentStatus(str, PyEnum):
    """Estado de inscripción a un curso"""
    PENDING = "pending"  # Solicitó unirse, pendiente aprobación
    ACTIVE = "active"  # Inscrito y activo
    INACTIVE = "inactive"  # Dado de baja
    COMPLETED = "completed"  # Completó el curso


class QuestionType(str, PyEnum):
    """Tipos de pregunta en exámenes"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    OPEN_ENDED = "open_ended"
    AI_GENERATED = "ai_generated"  # Preguntas generadas por IA profesor


class QuestionSource(str, PyEnum):
    """Origen de la pregunta"""
    PROFESSOR = "professor"  # Creada manualmente por profesor
    AI_PERSONALIZED = "ai_personalized"  # Generada por IA según debilidades


class ExamStatus(str, PyEnum):
    """Estado de un examen"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ExamType(str, PyEnum):
    """
    Tipos de examen con límites de preguntas.
    Diseñados para no ser tediosos y mantener engagement.
    """
    MINI_QUIZ = "mini_quiz"  # 5-10 preguntas, práctica rápida ~5-10 min
    MODULE_EVAL = "module_eval"  # 15-25 preguntas, evaluación de tema ~20-30 min
    FULL_EXAM = "full_exam"  # 30-50 preguntas, examen retador ~45-60 min
    AI_PERSONALIZED = "ai_personalized"  # 4 preguntas IA, repaso personalizado ~5 min


# Límites de preguntas por tipo de examen
EXAM_TYPE_LIMITS = {
    ExamType.MINI_QUIZ: {"min": 5, "max": 10, "time_suggested": 10},
    ExamType.MODULE_EVAL: {"min": 15, "max": 25, "time_suggested": 30},
    ExamType.FULL_EXAM: {"min": 30, "max": 50, "time_suggested": 60},
    ExamType.AI_PERSONALIZED: {"min": 4, "max": 4, "time_suggested": 5},
}


class AttemptStatus(str, PyEnum):
    """Estado de un intento de examen"""
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"


# =============================================================================
# USER MODEL
# =============================================================================

class User(Base):
    """Modelo de usuario (estudiante, profesor, admin)"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_exams = relationship("Exam", back_populates="creator")
    exam_attempts = relationship("ExamAttempt", back_populates="student")
    topic_stats = relationship("TopicPerformance", back_populates="student")

    # Courses (profesor crea cursos, estudiante se inscribe)
    owned_courses = relationship("Course", back_populates="professor")
    enrollments = relationship("CourseEnrollment", back_populates="student")

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"

    @property
    def enrolled_courses(self):
        """Cursos en los que está inscrito el estudiante (activos)"""
        return [e.course for e in self.enrollments if e.status == EnrollmentStatus.ACTIVE]


# =============================================================================
# COURSE MODEL (Clases/Cursos)
# =============================================================================

def generate_enrollment_code() -> str:
    """Genera un código de inscripción de 6 caracteres alfanumérico"""
    import secrets
    import string
    alphabet = string.ascii_uppercase + string.digits
    # Excluir caracteres confusos: 0, O, I, 1, L
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '').replace('L', '')
    return ''.join(secrets.choice(alphabet) for _ in range(6))


class Course(Base):
    """
    Modelo de Curso/Clase.
    Un profesor puede tener múltiples cursos.
    Los estudiantes se inscriben con un código.
    """
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    enrollment_code = Column(String(10), unique=True, nullable=False, default=generate_enrollment_code)

    # Configuración del curso
    is_active = Column(Boolean, default=True)  # Si acepta nuevas inscripciones
    max_students = Column(Integer, nullable=True)  # None = sin límite
    semester = Column(String(50), nullable=True)  # Ej: "2026-1", "Primavera 2026"

    # Foreign Keys
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    professor = relationship("User", back_populates="owned_courses")
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    exams = relationship("Exam", back_populates="course")

    def __repr__(self):
        return f"<Course {self.name} ({self.enrollment_code})>"

    @property
    def active_students(self):
        """Estudiantes activos en el curso"""
        return [e.student for e in self.enrollments if e.status == EnrollmentStatus.ACTIVE]

    @property
    def student_count(self) -> int:
        """Número de estudiantes activos"""
        return len([e for e in self.enrollments if e.status == EnrollmentStatus.ACTIVE])


class CourseEnrollment(Base):
    """
    Tabla intermedia para inscripciones de estudiantes en cursos.
    Permite que un estudiante esté en múltiples cursos y viceversa.
    """
    __tablename__ = "course_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE)

    # Timestamps
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    course = relationship("Course", back_populates="enrollments")
    student = relationship("User", back_populates="enrollments")

    # Unique constraint: un estudiante solo puede inscribirse una vez por curso
    __table_args__ = (
        UniqueConstraint('course_id', 'student_id', name='uq_course_student'),
    )

    def __repr__(self):
        return f"<Enrollment {self.student_id} in {self.course_id} ({self.status.value})>"


# =============================================================================
# EXAM MODELS
# =============================================================================

class Exam(Base):
    """
    Modelo de examen.

    Un examen puede estar asociado a un curso específico (course_id)
    o ser "global" (course_id=None) - solo accesible por el profesor creador.

    Los estudiantes solo pueden ver exámenes de cursos donde están inscritos.
    """
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    exam_type = Column(Enum(ExamType), default=ExamType.MODULE_EVAL, nullable=False)
    status = Column(Enum(ExamStatus), default=ExamStatus.DRAFT)
    time_limit_minutes = Column(Integer, nullable=True)  # None = usar sugerido por tipo
    passing_score = Column(Float, default=60.0)  # Porcentaje mínimo para aprobar
    max_attempts = Column(Integer, default=1)
    shuffle_questions = Column(Boolean, default=False)

    # Foreign Keys
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)  # Puede ser None

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    creator = relationship("User", back_populates="created_exams")
    course = relationship("Course", back_populates="exams")
    questions = relationship(
        "Question",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="Question.order"
    )
    attempts = relationship("ExamAttempt", back_populates="exam")

    def __repr__(self):
        return f"<Exam {self.title} ({self.status.value})>"

    @property
    def is_course_exam(self) -> bool:
        """True si el examen está asociado a un curso"""
        return self.course_id is not None


class Question(Base):
    """Modelo de pregunta de examen"""
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    text = Column(Text, nullable=False)
    points = Column(Float, default=1.0)
    order = Column(Integer, default=0)

    # Para preguntas de opción múltiple/verdadero-falso
    # Las opciones se almacenan como JSON string o en tabla separada
    options = Column(Text, nullable=True)  # JSON: ["opción A", "opción B", ...]
    correct_answer = Column(Text, nullable=True)  # Índice(s) o texto de respuesta correcta

    # Metadata educativa (opcional, para integrar con RAG)
    topic = Column(String(255), nullable=True)  # Ej: "tumor_staging", "treatment"
    difficulty = Column(Integer, default=1)  # 1-5

    # Origen de la pregunta (profesor manual vs IA generada)
    source = Column(Enum(QuestionSource), default=QuestionSource.PROFESSOR)
    # Para preguntas AI: razón de por qué se generó
    ai_generation_reason = Column(String(255), nullable=True)  # "weakness", "forgotten", etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    exam = relationship("Exam", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

    def __repr__(self):
        return f"<Question {self.id} ({self.question_type.value})>"


# =============================================================================
# EXAM ATTEMPT MODELS
# =============================================================================

class ExamAttempt(Base):
    """Modelo de intento de examen por estudiante"""
    __tablename__ = "exam_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(AttemptStatus), default=AttemptStatus.IN_PROGRESS)

    # Resultados
    score = Column(Float, nullable=True)  # Porcentaje obtenido
    total_points = Column(Float, nullable=True)
    earned_points = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    graded_at = Column(DateTime, nullable=True)

    # Relationships
    exam = relationship("Exam", back_populates="attempts")
    student = relationship("User", back_populates="exam_attempts")
    answers = relationship(
        "Answer",
        back_populates="attempt",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ExamAttempt {self.id} ({self.status.value})>"


class Answer(Base):
    """Modelo de respuesta a una pregunta"""
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("exam_attempts.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)

    # Respuesta del estudiante
    answer_text = Column(Text, nullable=True)
    selected_option = Column(Integer, nullable=True)  # Índice para multiple choice

    # Calificación
    is_correct = Column(Boolean, nullable=True)
    points_earned = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)  # Feedback del profesor o automático

    # Timestamps
    answered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    attempt = relationship("ExamAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    def __repr__(self):
        return f"<Answer {self.id} for Q:{self.question_id}>"


# =============================================================================
# STUDENT PERFORMANCE STATS (Como stats de videojuego)
# =============================================================================

class MedicalTopic(str, PyEnum):
    """Temas médicos para tracking de desempeño"""
    TUMOR_STAGING = "tumor_staging"  # Estadificación TNM
    TUMOR_BIOLOGY = "tumor_biology"  # Biología tumoral
    TREATMENT_SURGERY = "treatment_surgery"  # Cirugía
    TREATMENT_CHEMO = "treatment_chemo"  # Quimioterapia
    TREATMENT_RADIO = "treatment_radio"  # Radioterapia
    TREATMENT_IMMUNO = "treatment_immuno"  # Inmunoterapia
    DIAGNOSIS = "diagnosis"  # Diagnóstico
    RISK_FACTORS = "risk_factors"  # Factores de riesgo
    PROGNOSIS = "prognosis"  # Pronóstico
    ANATOMY = "anatomy"  # Anatomía pulmonar
    PHARMACOLOGY = "pharmacology"  # Farmacología
    PATIENT_CARE = "patient_care"  # Cuidado del paciente


class TopicPerformance(Base):
    """
    Estadísticas de desempeño por tema (como stats de videojuego).
    Cada estudiante tiene un registro por cada tema.
    """
    __tablename__ = "topic_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    topic = Column(Enum(MedicalTopic), nullable=False)

    # Stats principales (0-100)
    mastery_score = Column(Float, default=50.0)  # Nivel de dominio actual
    confidence_score = Column(Float, default=50.0)  # Qué tan seguro está

    # Contadores de desempeño
    total_questions = Column(Integer, default=0)  # Total preguntas vistas
    correct_answers = Column(Integer, default=0)  # Respuestas correctas
    incorrect_answers = Column(Integer, default=0)  # Respuestas incorrectas

    # Racha y tendencia
    current_streak = Column(Integer, default=0)  # Racha actual de aciertos
    best_streak = Column(Integer, default=0)  # Mejor racha histórica
    trend = Column(Float, default=0.0)  # Tendencia: positiva mejorando, negativa empeorando

    # Timing para algoritmo de repaso espaciado
    last_seen = Column(DateTime, nullable=True)  # Última vez que vio este tema
    last_correct = Column(DateTime, nullable=True)  # Última respuesta correcta
    last_incorrect = Column(DateTime, nullable=True)  # Última respuesta incorrecta

    # Para identificar puntos débiles vs fuertes
    needs_review = Column(Boolean, default=False)  # Marcado para repaso
    is_strength = Column(Boolean, default=False)  # Es un punto fuerte

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="topic_stats")

    # Unique constraint: un registro por estudiante por tema
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self):
        return f"<TopicPerformance {self.topic.value}: {self.mastery_score:.0f}%>"

    @property
    def accuracy_rate(self) -> float:
        """Porcentaje de aciertos"""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100

    @property
    def performance_level(self) -> str:
        """Nivel de desempeño como string"""
        if self.mastery_score >= 90:
            return "expert"
        elif self.mastery_score >= 75:
            return "advanced"
        elif self.mastery_score >= 60:
            return "intermediate"
        elif self.mastery_score >= 40:
            return "beginner"
        else:
            return "needs_work"


class AIGeneratedQuestion(Base):
    """
    Preguntas generadas por IA para exámenes personalizados.
    Se guardan para reutilizar y para auditoría.
    """
    __tablename__ = "ai_generated_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("exam_attempts.id"), nullable=True)

    # Contenido de la pregunta
    topic = Column(Enum(MedicalTopic), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON array
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)  # Explicación educativa

    # Por qué se generó esta pregunta
    generation_reason = Column(String(50), nullable=False)  # "weakness", "forgotten", "challenge"
    target_difficulty = Column(Integer, default=3)  # 1-5

    # Resultado cuando se respondió
    was_answered = Column(Boolean, default=False)
    was_correct = Column(Boolean, nullable=True)
    student_answer = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AIQuestion {self.topic.value} ({self.generation_reason})>"

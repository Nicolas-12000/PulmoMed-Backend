"""
Pydantic Schemas - Request/Response DTOs
"""

from app.schemas.auth_schemas import (
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.exam_schemas import (
    AnswerResponse,
    AnswerSubmit,
    AttemptResultResponse,
    AttemptStartResponse,
    AttemptSubmitRequest,
    ExamCreate,
    ExamDetailResponse,
    ExamResponse,
    ExamStudentResponse,
    ExamUpdate,
    QuestionCreate,
    QuestionResponse,
    QuestionStudentResponse,
    QuestionUpdate,
)

__all__ = [
    # Auth
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "MessageResponse",
    # Exam
    "ExamCreate",
    "ExamUpdate",
    "ExamResponse",
    "ExamDetailResponse",
    "ExamStudentResponse",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "QuestionStudentResponse",
    "AnswerSubmit",
    "AnswerResponse",
    "AttemptStartResponse",
    "AttemptSubmitRequest",
    "AttemptResultResponse",
]

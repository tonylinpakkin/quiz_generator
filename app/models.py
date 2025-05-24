"""
Pydantic models for Quiz Generator application
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: FileType
    file_size: int
    status: ProcessingStatus
    message: str

class TextExtractionResult(BaseModel):
    file_id: str
    text_content: str
    word_count: int
    extraction_time: float

class QuizQuestion(BaseModel):
    id: str
    question: str
    question_type: QuestionType
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: Optional[str] = "medium"

class Quiz(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    source_file_id: str
    questions: List[QuizQuestion]
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

class QuizGenerationRequest(BaseModel):
    file_id: str
    num_questions: int = Field(default=5, ge=1, le=50)
    question_types: List[QuestionType] = [QuestionType.MULTIPLE_CHOICE]
    difficulty_level: str = "medium"
    focus_topics: Optional[List[str]] = None
    language: str = "english"

class QuizGenerationResponse(BaseModel):
    quiz_id: str
    status: ProcessingStatus
    message: str
    quiz: Optional[Quiz] = None

class QuizUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    questions: Optional[List[QuizQuestion]] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

class FileInfo(BaseModel):
    file_id: str
    filename: str
    file_type: FileType
    file_size: int
    upload_time: datetime
    text_extracted: bool
    word_count: Optional[int] = None

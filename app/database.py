"""
Database operations for Quiz Generator
In-memory storage for MVP with PostgreSQL preparation
"""
import os
from typing import Dict, List, Optional
from datetime import datetime
import json
import uuid

from app.models import Quiz, QuizQuestion, FileInfo, TextExtractionResult

class InMemoryDatabase:
    """In-memory database implementation for MVP"""
    
    def __init__(self):
        self.files: Dict[str, FileInfo] = {}
        self.extracted_texts: Dict[str, TextExtractionResult] = {}
        self.quizzes: Dict[str, Quiz] = {}
        self.file_contents: Dict[str, bytes] = {}

    def store_file(self, file_id: str, filename: str, file_type: str, 
                   file_size: int, content: bytes) -> FileInfo:
        """Store uploaded file information and content"""
        file_info = FileInfo(
            file_id=file_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            upload_time=datetime.now(),
            text_extracted=False
        )
        self.files[file_id] = file_info
        self.file_contents[file_id] = content
        return file_info

    def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """Get file information by ID"""
        return self.files.get(file_id)

    def get_file_content(self, file_id: str) -> Optional[bytes]:
        """Get file content by ID"""
        return self.file_contents.get(file_id)

    def store_extracted_text(self, result: TextExtractionResult) -> None:
        """Store extracted text result"""
        self.extracted_texts[result.file_id] = result
        if result.file_id in self.files:
            self.files[result.file_id].text_extracted = True
            self.files[result.file_id].word_count = result.word_count

    def get_extracted_text(self, file_id: str) -> Optional[TextExtractionResult]:
        """Get extracted text by file ID"""
        return self.extracted_texts.get(file_id)

    def store_quiz(self, quiz: Quiz) -> Quiz:
        """Store quiz in database"""
        self.quizzes[quiz.id] = quiz
        return quiz

    def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID"""
        return self.quizzes.get(quiz_id)

    def update_quiz(self, quiz_id: str, updates: dict) -> Optional[Quiz]:
        """Update quiz with new data"""
        if quiz_id not in self.quizzes:
            return None
        
        quiz = self.quizzes[quiz_id]
        quiz_dict = quiz.dict()
        quiz_dict.update(updates)
        quiz_dict['updated_at'] = datetime.now()
        
        updated_quiz = Quiz(**quiz_dict)
        self.quizzes[quiz_id] = updated_quiz
        return updated_quiz

    def list_quizzes(self, file_id: Optional[str] = None) -> List[Quiz]:
        """List all quizzes, optionally filtered by file ID"""
        quizzes = list(self.quizzes.values())
        if file_id:
            quizzes = [q for q in quizzes if q.source_file_id == file_id]
        return sorted(quizzes, key=lambda x: x.created_at, reverse=True)

    def delete_quiz(self, quiz_id: str) -> bool:
        """Delete quiz by ID"""
        if quiz_id in self.quizzes:
            del self.quizzes[quiz_id]
            return True
        return False

    def list_files(self) -> List[FileInfo]:
        """List all uploaded files"""
        return sorted(self.files.values(), key=lambda x: x.upload_time, reverse=True)

# Global database instance
db = InMemoryDatabase()

def init_db():
    """Initialize database - placeholder for PostgreSQL setup"""
    # For PostgreSQL implementation, you would:
    # 1. Create connection pool
    # 2. Run migrations
    # 3. Set up tables
    
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("postgresql"):
        print(f"PostgreSQL database configured: {database_url}")
        # TODO: Implement PostgreSQL connection
    else:
        print("Using in-memory database for MVP")
    
    return db

def get_database():
    """Get database instance"""
    return db

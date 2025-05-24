"""
Quiz generation service that orchestrates text extraction and LLM generation
"""
import uuid
from datetime import datetime
from typing import List, Optional

from app.models import (
    Quiz, QuizQuestion, QuizGenerationRequest, 
    TextExtractionResult, ProcessingStatus, QuestionType
)
from app.database import get_database
from app.file_parser import FileParser, FileParsingError
from app.llm_client import get_llm_client, LLMClientError

class QuizGenerationError(Exception):
    """Custom exception for quiz generation errors"""
    pass

class QuizGeneratorService:
    """Service for generating quizzes from uploaded files"""
    
    def __init__(self):
        self.db = get_database()
        self.llm_client = get_llm_client()
    
    async def extract_text_from_file(self, file_id: str) -> TextExtractionResult:
        """Extract text from uploaded file"""
        
        # Get file info and content
        file_info = self.db.get_file_info(file_id)
        if not file_info:
            raise QuizGenerationError(f"File not found: {file_id}")
        
        file_content = self.db.get_file_content(file_id)
        if not file_content:
            raise QuizGenerationError(f"File content not found: {file_id}")
        
        try:
            start_time = datetime.now()
            
            # Extract text using file parser
            text_content, word_count = FileParser.parse_file(
                file_info.filename, file_content
            )
            
            extraction_time = (datetime.now() - start_time).total_seconds()
            
            # Create extraction result
            result = TextExtractionResult(
                file_id=file_id,
                text_content=text_content,
                word_count=word_count,
                extraction_time=extraction_time
            )
            
            # Store extraction result
            self.db.store_extracted_text(result)
            
            return result
            
        except FileParsingError as e:
            raise QuizGenerationError(f"Text extraction failed: {str(e)}")
    
    async def generate_quiz_from_text(self, request: QuizGenerationRequest) -> Quiz:
        """Generate quiz from extracted text"""
        
        # Get extracted text
        extracted_text = self.db.get_extracted_text(request.file_id)
        if not extracted_text:
            # Try to extract text if not already done
            extracted_text = await self.extract_text_from_file(request.file_id)
        
        text_content = extracted_text.text_content.strip()
        if not text_content:
            raise QuizGenerationError("No text content available for quiz generation")
            
        # Validate actual content vs metadata
        lines = text_content.split('\n')
        real_content_lines = [line for line in lines 
                            if line.strip() and not line.strip().startswith(('/', '%'))]
        
        if not real_content_lines:
            raise QuizGenerationError("No readable content found in document, only metadata was extracted")
            
        try:
            # Generate questions using LLM with validated content
            clean_text_content = '\n'.join(real_content_lines)
            questions = await self.llm_client.generate_quiz(
                text_content=clean_text_content,
                num_questions=request.num_questions,
                question_types=request.question_types,
                difficulty_level=request.difficulty_level,
                focus_topics=request.focus_topics,
                language=request.language
            )
            
            if not questions:
                raise QuizGenerationError("No questions were generated")
            
            # Get file info for quiz metadata
            file_info = self.db.get_file_info(request.file_id)
            
            # Create quiz
            quiz = Quiz(
                id=str(uuid.uuid4()),
                title=f"Quiz from {file_info.filename if file_info else 'uploaded file'}",
                description=f"Generated quiz with {len(questions)} questions",
                source_file_id=request.file_id,
                questions=questions,
                created_at=datetime.now(),
                metadata={
                    "generation_request": request.dict(),
                    "source_word_count": extracted_text.word_count,
                    "extraction_time": extracted_text.extraction_time
                }
            )
            
            # Store quiz
            stored_quiz = self.db.store_quiz(quiz)
            
            return stored_quiz
            
        except LLMClientError as e:
            raise QuizGenerationError(f"Quiz generation failed: {str(e)}")
    
    async def generate_quiz_from_file(self, request: QuizGenerationRequest) -> Quiz:
        """Complete workflow: extract text and generate quiz"""
        
        try:
            # Check if text is already extracted
            extracted_text = self.db.get_extracted_text(request.file_id)
            if not extracted_text:
                extracted_text = await self.extract_text_from_file(request.file_id)
            
            # Generate quiz
            quiz = await self.generate_quiz_from_text(request)
            
            return quiz
            
        except Exception as e:
            if isinstance(e, QuizGenerationError):
                raise
            raise QuizGenerationError(f"Unexpected error during quiz generation: {str(e)}")
    
    def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID"""
        return self.db.get_quiz(quiz_id)
    
    def update_quiz(self, quiz_id: str, updates: dict) -> Optional[Quiz]:
        """Update quiz with new data"""
        return self.db.update_quiz(quiz_id, updates)
    
    def list_quizzes(self, file_id: Optional[str] = None) -> List[Quiz]:
        """List quizzes, optionally filtered by file ID"""
        return self.db.list_quizzes(file_id)
    
    def delete_quiz(self, quiz_id: str) -> bool:
        """Delete quiz by ID"""
        return self.db.delete_quiz(quiz_id)
    
    def get_file_info(self, file_id: str):
        """Get file information"""
        return self.db.get_file_info(file_id)
    
    def list_files(self):
        """List all uploaded files"""
        return self.db.list_files()

# Global quiz generator service
quiz_generator = QuizGeneratorService()

def get_quiz_generator() -> QuizGeneratorService:
    """Get quiz generator service instance"""
    return quiz_generator

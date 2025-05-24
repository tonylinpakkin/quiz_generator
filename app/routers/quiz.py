"""
Quiz management endpoints for Quiz Generator
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models import (
    Quiz, QuizGenerationRequest, QuizGenerationResponse, 
    QuizUpdateRequest, ProcessingStatus
)
from app.quiz_generator import get_quiz_generator, QuizGenerationError

router = APIRouter()

@router.post("/generate-quiz", response_model=QuizGenerationResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate a quiz from uploaded file"""
    
    try:
        quiz_generator = get_quiz_generator()
        
        # Validate file exists
        file_info = quiz_generator.get_file_info(request.file_id)
        if not file_info:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        # Generate quiz
        quiz = await quiz_generator.generate_quiz_from_file(request)
        
        return QuizGenerationResponse(
            quiz_id=quiz.id,
            status=ProcessingStatus.COMPLETED,
            message="Quiz generated successfully",
            quiz=quiz
        )
        
    except QuizGenerationError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@router.get("/quizzes", response_model=List[Quiz])
async def list_quizzes(file_id: Optional[str] = None):
    """List all quizzes, optionally filtered by file ID"""
    
    try:
        quiz_generator = get_quiz_generator()
        quizzes = quiz_generator.list_quizzes(file_id=file_id)
        return quizzes
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve quizzes: {str(e)}"
        )

@router.get("/quizzes/{quiz_id}", response_model=Quiz)
async def get_quiz(quiz_id: str):
    """Get a specific quiz by ID"""
    
    try:
        quiz_generator = get_quiz_generator()
        quiz = quiz_generator.get_quiz(quiz_id)
        
        if not quiz:
            raise HTTPException(
                status_code=404,
                detail="Quiz not found"
            )
        
        return quiz
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve quiz: {str(e)}"
        )

@router.put("/quizzes/{quiz_id}", response_model=Quiz)
async def update_quiz(quiz_id: str, request: QuizUpdateRequest):
    """Update a quiz"""
    
    try:
        quiz_generator = get_quiz_generator()
        
        # Check if quiz exists
        existing_quiz = quiz_generator.get_quiz(quiz_id)
        if not existing_quiz:
            raise HTTPException(
                status_code=404,
                detail="Quiz not found"
            )
        
        # Prepare updates
        updates = {}
        if request.title is not None:
            updates['title'] = request.title
        if request.description is not None:
            updates['description'] = request.description
        if request.questions is not None:
            updates['questions'] = [q.dict() for q in request.questions]
        
        if not updates:
            raise HTTPException(
                status_code=400,
                detail="No updates provided"
            )
        
        # Update quiz
        updated_quiz = quiz_generator.update_quiz(quiz_id, updates)
        
        return updated_quiz
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update quiz: {str(e)}"
        )

@router.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str):
    """Delete a quiz"""
    
    try:
        quiz_generator = get_quiz_generator()
        
        # Check if quiz exists
        existing_quiz = quiz_generator.get_quiz(quiz_id)
        if not existing_quiz:
            raise HTTPException(
                status_code=404,
                detail="Quiz not found"
            )
        
        # Delete quiz
        success = quiz_generator.delete_quiz(quiz_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete quiz"
            )
        
        return {"message": f"Quiz {quiz_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete quiz: {str(e)}"
        )

@router.post("/quizzes/{quiz_id}/duplicate", response_model=Quiz)
async def duplicate_quiz(quiz_id: str):
    """Create a duplicate of an existing quiz"""
    
    try:
        quiz_generator = get_quiz_generator()
        
        # Get original quiz
        original_quiz = quiz_generator.get_quiz(quiz_id)
        if not original_quiz:
            raise HTTPException(
                status_code=404,
                detail="Quiz not found"
            )
        
        # Create duplicate
        import uuid
        from datetime import datetime
        
        duplicate_data = original_quiz.dict()
        duplicate_data['id'] = str(uuid.uuid4())
        duplicate_data['title'] = f"Copy of {original_quiz.title}"
        duplicate_data['created_at'] = datetime.now()
        duplicate_data['updated_at'] = None
        
        # Regenerate question IDs
        for question in duplicate_data['questions']:
            question['id'] = f"q_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        from app.models import Quiz
        duplicate_quiz = Quiz(**duplicate_data)
        
        # Store duplicate
        stored_quiz = quiz_generator.db.store_quiz(duplicate_quiz)
        
        return stored_quiz
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to duplicate quiz: {str(e)}"
        )

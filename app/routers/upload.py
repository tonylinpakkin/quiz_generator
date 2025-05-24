"""
File upload endpoints for Quiz Generator
"""
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models import UploadResponse, ProcessingStatus, FileInfo, ErrorResponse
from app.database import get_database
from app.file_parser import validate_file_type, get_file_type
from app.quiz_generator import get_quiz_generator

router = APIRouter()

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a study material file"""
    
    try:
        # Validate file type
        if not validate_file_type(file.filename):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload PDF, DOCX, or TXT files."
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB."
            )
        
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded."
            )
        
        # Generate file ID and store file
        file_id = str(uuid.uuid4())
        file_type = get_file_type(file.filename)
        
        db = get_database()
        file_info = db.store_file(
            file_id=file_id,
            filename=file.filename,
            file_type=file_type,
            file_size=len(content),
            content=content
        )
        
        # Schedule background text extraction
        quiz_generator = get_quiz_generator()
        background_tasks.add_task(extract_text_background, file_id, quiz_generator)
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_type=file_type,
            file_size=len(content),
            status=ProcessingStatus.PENDING,
            message="File uploaded successfully. Text extraction in progress."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

async def extract_text_background(file_id: str, quiz_generator):
    """Background task for text extraction"""
    try:
        await quiz_generator.extract_text_from_file(file_id)
        print(f"Text extraction completed for file: {file_id}")
    except Exception as e:
        print(f"Text extraction failed for file {file_id}: {e}")

@router.get("/files", response_model=List[FileInfo])
async def list_files():
    """List all uploaded files"""
    try:
        db = get_database()
        files = db.list_files()
        return files
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve files: {str(e)}"
        )

@router.get("/files/{file_id}", response_model=FileInfo)
async def get_file_info(file_id: str):
    """Get information about a specific file"""
    try:
        db = get_database()
        file_info = db.get_file_info(file_id)
        
        if not file_info:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve file info: {str(e)}"
        )

@router.get("/files/{file_id}/text")
async def get_extracted_text(file_id: str):
    """Get extracted text from a file"""
    try:
        db = get_database()
        
        # Check if file exists
        file_info = db.get_file_info(file_id)
        if not file_info:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        # Get extracted text
        extracted_text = db.get_extracted_text(file_id)
        if not extracted_text:
            # Try to extract if not already done
            quiz_generator = get_quiz_generator()
            try:
                extracted_text = await quiz_generator.extract_text_from_file(file_id)
            except Exception as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"Text extraction failed: {str(e)}"
                )
        
        return {
            "file_id": file_id,
            "text_content": extracted_text.text_content,
            "word_count": extracted_text.word_count,
            "extraction_time": extracted_text.extraction_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve extracted text: {str(e)}"
        )

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file and its associated data"""
    try:
        db = get_database()
        
        # Check if file exists
        file_info = db.get_file_info(file_id)
        if not file_info:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        # Delete associated quizzes
        quiz_generator = get_quiz_generator()
        quizzes = quiz_generator.list_quizzes(file_id=file_id)
        for quiz in quizzes:
            quiz_generator.delete_quiz(quiz.id)
        
        # Delete file data
        if file_id in db.files:
            del db.files[file_id]
        if file_id in db.file_contents:
            del db.file_contents[file_id]
        if file_id in db.extracted_texts:
            del db.extracted_texts[file_id]
        
        return {"message": f"File {file_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )

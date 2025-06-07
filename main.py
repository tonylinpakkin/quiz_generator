"""
FastAPI main application entry point for Quiz Generator
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from app.routers import upload, quiz
from app.database import init_db

# Initialize FastAPI app
app = FastAPI(
    title="Quiz Generator API",
    description="Generate quizzes from uploaded study materials using local LLM",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(quiz.router, prefix="/api", tags=["quiz"])

# Serve static files from public directory if it exists
if os.path.exists("public"):
    app.mount("/static", StaticFiles(directory="public"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the React frontend"""
    # Try to serve from public directory first, fallback to simple HTML
    if os.path.exists("public/index.html"):
        return FileResponse("public/index.html")
    else:
        # Return a simple HTML page for development
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quiz Generator API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                h1 { color: #333; }
                h2 { color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧠 Quiz Generator API</h1>
                <p>Backend is running successfully!</p>
                
                <h2>Available Endpoints:</h2>
                <div class="endpoint">
                    <strong>GET /health</strong> - Health check
                </div>
                <div class="endpoint">
                    <strong>POST /api/upload</strong> - Upload files
                </div>
                <div class="endpoint">
                    <strong>GET /api/files</strong> - List uploaded files
                </div>
                <div class="endpoint">
                    <strong>POST /api/generate-quiz</strong> - Generate quiz from file
                </div>
                <div class="endpoint">
                    <strong>GET /api/quizzes</strong> - List all quizzes
                </div>
                <div class="endpoint">
                    <strong>GET /docs</strong> - API Documentation (Swagger)
                </div>
                
                <p><a href="/docs">📚 View API Documentation</a></p>
            </div>
        </body>
        </html>
        """

@app.get("/quiz-viewer.html")
async def serve_quiz_viewer():
    """Serve the quiz viewer page"""
    if os.path.exists("public/quiz-viewer.html"):
        return FileResponse("public/quiz-viewer.html")
    else:
        raise HTTPException(status_code=404, detail="Quiz viewer not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Quiz Generator API is running"}

@app.get("/api/llm-status")
async def llm_status():
    """Check LLM integration status"""
    from app.llm_client import get_llm_client
    from app.huggingface_client import get_huggingface_client
    from app.gemini_client import get_gemini_client
    
    client = get_llm_client()
    
    if client.mock_mode:
        return {
            "mode": "mock",
            "status": "ready",
            "message": "Running in mock mode - generates sample questions",
            "provider": "mock",
            "model": "Mock Generator"
        }
    
    # Check Gemini as fallback
    if client.use_gemini:
        try:
            gemini_client = get_gemini_client()
            if gemini_client.api_token:
                await gemini_client._check_gemini_health()
                return {
                    "mode": "real",
                    "status": "ready", 
                    "message": f"Gemini is available with model {gemini_client.model_name}",
                    "provider": "gemini",
                    "model": gemini_client.model_name
                }
            else:
                return {
                    "mode": "real",
                    "status": "error",
                    "message": "Gemini API key not provided",
                    "provider": "gemini",
                    "model": gemini_client.model_name
                }
        except Exception as gemini_error:
            pass  # Try Hugging Face as fallback
    
    # Check Hugging Face as fallback
    if client.use_huggingface:
        try:
            hf_client = get_huggingface_client()
            if hf_client.api_token:
                await hf_client._check_hf_health()
                return {
                    "mode": "real",
                    "status": "ready", 
                    "message": f"Hugging Face is available with model {hf_client.model_name}",
                    "provider": "huggingface",
                    "model": hf_client.model_name
                }
            else:
                return {
                    "mode": "real",
                    "status": "error",
                    "message": "Hugging Face API token not provided",
                    "provider": "huggingface",
                    "model": hf_client.model_name
                }
        except Exception as hf_error:
            pass  # Try Ollama as fallback
    
    # Check Ollama as fallback
    try:
        await client._check_ollama_health()
        return {
            "mode": "real",
            "status": "ready", 
            "message": f"Ollama is available with model {client.model_name}",
            "provider": "ollama",
            "model": client.model_name
        }
    except Exception as e:
        return {
            "mode": "real",
            "status": "error",
            "message": f"No AI services available. Gemini: token needed, Hugging Face: issues, Ollama: {str(e)}",
            "provider": "none",
            "model": "none"
        }

# Add API endpoints for client-side storage
from pydantic import BaseModel
from typing import List, Optional

class DirectQuizRequest(BaseModel):
    text_content: str
    num_questions: int = 5
    question_types: List[str] = ["multiple_choice"]
    difficulty_level: str = "medium"
    language: str = "english"
    ai_service: str = "auto"  # auto or gemini

@app.post("/api/generate-quiz-direct")
async def generate_quiz_direct(request: DirectQuizRequest):
    """Generate quiz directly from text content (for client-side storage)"""
    try:
        from app.quiz_generator import get_quiz_generator
        from app.models import QuestionType
        
        # Convert string question types to enum
        question_type_map = {
            "multiple_choice": QuestionType.MULTIPLE_CHOICE,
            "true_false": QuestionType.TRUE_FALSE,
            "short_answer": QuestionType.SHORT_ANSWER
        }
        
        question_types = [question_type_map.get(qt, QuestionType.MULTIPLE_CHOICE) for qt in request.question_types]
        
        # Select AI service based on user preference
        if request.ai_service == "gemini":
            from app.gemini_client import get_gemini_client
            ai_client = get_gemini_client()
        else:  # auto mode
            quiz_generator = get_quiz_generator()
            ai_client = quiz_generator.llm_client
        
        # Generate questions using selected AI service
        questions = await ai_client.generate_quiz(
            text_content=request.text_content,
            num_questions=request.num_questions,
            question_types=question_types,
            difficulty_level=request.difficulty_level,
            language=request.language
        )
        
        # Create a quiz structure that matches frontend expectations
        import uuid
        from datetime import datetime
        
        quiz_id = str(uuid.uuid4())
        quiz = {
            "id": quiz_id,
            "title": f"Quiz - {request.num_questions} Questions",
            "description": f"Generated quiz with {request.num_questions} questions",
            "questions": [q.dict() for q in questions],
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "difficulty": request.difficulty_level,
                "language": request.language,
                "question_types": request.question_types
            }
        }
        
        return {"quiz": quiz}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Changed to port 5000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

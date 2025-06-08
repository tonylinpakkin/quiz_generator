import io
import uuid
import pytest
import fitz

from app.quiz_generator import QuizGeneratorService, QuizGenerationError
from app.database import InMemoryDatabase
from app.models import QuizGenerationRequest, QuestionType


def create_metadata_pdf():
    doc = fitz.open()
    page = doc.new_page()
    metadata_lines = [
        "Title: Example",
        "Author: Example",
        "Creator: Example",
        "Producer: Example",
        "CreationDate: 2024",
    ]
    page.insert_text((72, 720), "\n".join(metadata_lines))
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_quiz_not_generated_from_pdf_metadata():
    pdf_content = create_metadata_pdf()
    file_id = str(uuid.uuid4())

    db = InMemoryDatabase()
    db.store_file(
        file_id=file_id,
        filename="metadata.pdf",
        file_type="pdf",
        file_size=len(pdf_content),
        content=pdf_content,
    )

    service = QuizGeneratorService()
    service.db = db

    request = QuizGenerationRequest(
        file_id=file_id,
        num_questions=3,
        question_types=[QuestionType.MULTIPLE_CHOICE],
    )

    with pytest.raises(QuizGenerationError):
        await service.generate_quiz_from_file(request)

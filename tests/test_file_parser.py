import io
import pytest
import fitz
from app.file_parser import FileParser, FileParsingError


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


def test_pdf_with_only_metadata_raises_error():
    pdf_content = create_metadata_pdf()
    with pytest.raises(FileParsingError):
        FileParser.extract_text_from_pdf(pdf_content)

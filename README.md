# Quiz Generator

A local web application for generating quizzes from uploaded study materials using FastAPI backend and React frontend, designed for self-hosted LLM integration.

## Features

- **File Upload**: Support for PDF, DOCX, and TXT files
- **Text Extraction**: Automatic text extraction from uploaded documents
- **Quiz Generation**: AI-powered quiz generation using local LLM
- **Quiz Management**: View, edit, and organize your quizzes
- **Interactive Quiz Taking**: Study mode and test mode with progress tracking
- **Local LLM Ready**: Prepared for Ollama integration

## Tech Stack

### Backend
- **FastAPI**: Python web framework for the API
- **PyMuPDF**: PDF text extraction
- **python-docx**: DOCX file processing
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server

### Frontend
- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API calls

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd quiz-generator

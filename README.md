# Quiz Generator

A local web application that lets you generate quizzes from your study material. The backend is powered by FastAPI while the frontend is built with React.

## Features

- **File Upload**: Supports PDF, DOCX and TXT files
- **Text Extraction**: Automatically extracts text from uploaded documents
- **Quiz Generation**: AI powered quiz generation using a local LLM
- **Quiz Management**: View, edit and organize quizzes
- **Interactive Quiz Taking**: Study and test modes with progress tracking

## Tech Stack

### Backend
- **FastAPI** for the API layer
- **PyMuPDF** and **python-docx** for document parsing
- **Pydantic** for data validation
- **Uvicorn** as the ASGI server

### Frontend
- **React 18** with TypeScript
- **Vite** for building the frontend
- **Tailwind CSS** for styling

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/tonylinpakkin/quiz_generator
cd quiz_generator
```

### 2. Run the setup script

The project ships with a helper script that installs Python and Node dependencies, builds the frontend and prepares the environment:

```bash
chmod +x setup.sh
./setup.sh
```

After the script finishes, review the generated `.env` file and set `LLM_MOCK_MODE=false` when you are ready to use a real LLM.

## Launching the application

1. Activate the Python virtual environment and start the backend:

   ```bash
   source venv/bin/activate
   python main.py
   ```

2. In another terminal, start the React development server:

   ```bash
   npm run dev
   ```

3. Open <http://localhost:5000> in your browser.

The backend listens on port 5000 by default. You can change the port by setting the `PORT` environment variable before starting `main.py`.

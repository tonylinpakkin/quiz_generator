"""
Google Gemini LLM client for quiz generation
Uses Google Gemini API for real AI-powered quiz generation
"""

from typing import List, Optional, Dict, Any
import json
import re
import uuid
import httpx
import asyncio
import os
from app.models import QuizQuestion, QuestionType

class GeminiClientError(Exception):
    """Custom exception for Gemini client errors"""
    pass

class GeminiClient:
    """Client for interfacing with Google Gemini API"""

    def __init__(self):
        self.api_token = os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))
        self.max_retries = 2
        self.chunk_size = 4000

    async def generate_quiz(self, text_content: str, num_questions: int = 5, 
                          question_types: Optional[List[QuestionType]] = None,
                          difficulty_level: str = "medium",
                          focus_topics: Optional[List[str]] = None,
                          language: str = "english") -> List[QuizQuestion]:
        """Generate quiz questions from text content"""

        if not self.api_token:
            raise GeminiClientError("Gemini API key is required")

        if question_types is None:
            question_types = [QuestionType.MULTIPLE_CHOICE]
        if focus_topics is None:
            focus_topics = []

        # Split long content into chunks
        content_chunks = [text_content[i:i + self.chunk_size] 
                        for i in range(0, len(text_content), self.chunk_size)]

        all_questions = []
        questions_per_chunk = num_questions // len(content_chunks)

        for i, chunk in enumerate(content_chunks):
            chunk_questions = questions_per_chunk
            if i == len(content_chunks) - 1:
                # Add remaining questions to last chunk
                chunk_questions += num_questions % len(content_chunks)

            questions = await self._generate_chunk_questions(
                chunk, chunk_questions, question_types, 
                difficulty_level, focus_topics, language
            )
            all_questions.extend(questions)

        return all_questions[:num_questions]

    async def _generate_chunk_questions(self, content: str, num_questions: int,
                                     question_types: List[QuestionType],
                                     difficulty_level: str,
                                     focus_topics: List[str],
                                     language: str) -> List[QuizQuestion]:
        """Generate questions for a content chunk with retries"""

        for attempt in range(self.max_retries):
            try:
                prompt = self._create_quiz_prompt(
                    content, num_questions, question_types,
                    difficulty_level, focus_topics, language
                )

                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "topP": 0.9,
                        "maxOutputTokens": 2048,
                        "stopSequences": ["QUESTION"]
                    }
                }

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.api_url}?key={self.api_token}",
                        json=payload
                    )
                    response.raise_for_status()

                    result = response.json()
                    if not result.get("candidates"):
                        raise GeminiClientError("No response candidates")

                    response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    questions = self._parse_quiz_response(response_text)

                    if questions:
                        return questions

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise GeminiClientError(f"Failed after {self.max_retries} attempts: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return []

    def _create_quiz_prompt(self, text_content: str, num_questions: int,
                          question_types: List[QuestionType],
                          difficulty_level: str,
                          focus_topics: List[str],
                          language: str) -> str:
        """Create an improved structured prompt"""

        type_map = {
            QuestionType.MULTIPLE_CHOICE: "multiple-choice (4 options)",
            QuestionType.TRUE_FALSE: "true/false",
            QuestionType.SHORT_ANSWER: "short-answer"
        }

        types_str = ", ".join(type_map[t] for t in question_types)
        focus_str = f"\nFocus on these topics: {', '.join(focus_topics)}" if focus_topics else ""

        return f"""
        You are **QuizMaster**, a large-language model specialized in assessment
        design. As an expert educator, create {num_questions} {difficulty_level}
        level quiz questions in {language}.
                                
        Your task is to generate high-quality quizzes from the **Source
        Material** I provide.
                                
        Study this material carefully:
            
            {text_content}
            
            CREATE {num_questions} QUESTIONS:
            - Question types: {types_str}
            - Make questions test comprehension
            - Ensure answers come from the text{focus_str}
            
            FORMAT EACH QUESTION EXACTLY LIKE THIS:
            
            QUESTION:
            Type: [question_type]
            Question: [clear, specific question]
            Options: [for multiple-choice: A) B) C) D)]
            Answer: [correct answer]
            Explanation: [brief explanation from text]
            
            START WITH QUESTION 1:
            """

    def _parse_quiz_response(self, response_text: str) -> List[QuizQuestion]:
        """Parse response with improved error handling"""

        questions = []
        blocks = re.split(r'(?:^|\n)QUESTION(?:\s+\d+)?:', response_text)

        for block in (b.strip() for b in blocks if b.strip()):
            try:
                lines = [l.strip() for l in block.split('\n') if l.strip()]
                if len(lines) < 3:
                    continue

                question_data = {}
                current_key = None

                for line in lines:
                    if line.lower().startswith(('type:', 'question:', 'options:', 'answer:', 'explanation:')):
                        current_key = line.split(':', 1)[0].lower()
                        question_data[current_key] = line.split(':', 1)[1].strip()
                    elif current_key:
                        question_data[current_key] = question_data.get(current_key, '') + ' ' + line

                if not {'type', 'question', 'answer'}.issubset(question_data.keys()):
                    continue

                q_type = self._parse_question_type(question_data['type'])
                options = self._parse_options(question_data.get('options', '')) if q_type == QuestionType.MULTIPLE_CHOICE else None

                questions.append(QuizQuestion(
                    id=str(uuid.uuid4()),
                    question=question_data['question'],
                    question_type=q_type,
                    options=options,
                    correct_answer=question_data['answer'],
                    explanation=question_data.get('explanation', 'Based on the provided content.'),
                    difficulty="medium"
                ))

            except Exception as e:
                print(f"Failed to parse question block: {str(e)}")
                continue

        return questions

    def _parse_question_type(self, type_text: str) -> QuestionType:
        """Parse question type from text"""
        type_text = type_text.lower()
        if 'multiple' in type_text or 'choice' in type_text:
            return QuestionType.MULTIPLE_CHOICE
        elif 'true' in type_text or 'false' in type_text:
            return QuestionType.TRUE_FALSE
        return QuestionType.SHORT_ANSWER

    def _parse_options(self, options_text: str) -> List[str]:
        """Parse multiple choice options"""
        if not options_text:
            return ["Option A", "Option B", "Option C", "Option D"]

        options = re.findall(r'[A-D]\)(.*?)(?=[A-D]\)|$)', options_text)
        return [opt.strip() for opt in options] if len(options) == 4 else ["Option A", "Option B", "Option C", "Option D"]

def get_gemini_client() -> GeminiClient:
    """Get Gemini client instance"""
    return GeminiClient()
"""Local LLM client for quiz generation."""

from typing import List, Optional
import json
import re
import uuid
import os
from app.models import QuizQuestion, QuestionType
from app.gemini_client import get_gemini_client


class LLMClientError(Exception):
    """Custom exception for LLM client errors"""
    pass


class LocalLLMClient:
    """Client for interfacing with a local LLM"""

    def __init__(self):
        self.model_name = os.getenv("LLM_MODEL", "llama3.2")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))
        self.mock_mode = os.getenv("LLM_MOCK_MODE", "false").lower() == "true"
        self.use_gemini = os.getenv("USE_GEMINI", "true").lower() == "true"

    async def generate_quiz(self, text_content: str, num_questions: int = 5, 
                          question_types: Optional[List[QuestionType]] = None,
                          difficulty_level: str = "medium",
                          focus_topics: Optional[List[str]] = None,
                          language: str = "english") -> List[QuizQuestion]:
        """Generate quiz questions from text content"""

        # Set defaults for optional parameters
        if question_types is None:
            question_types = [QuestionType.MULTIPLE_CHOICE]
        if focus_topics is None:
            focus_topics = []

        if self.mock_mode:
            print(f"🎯 Using mock mode for quiz generation")
            return self._generate_mock_quiz(text_content, num_questions, question_types)


        # Try Gemini as fallback
        if self.use_gemini:
            try:
                gemini_client = get_gemini_client()
                return await gemini_client.generate_quiz(
                    text_content, num_questions, question_types, difficulty_level, focus_topics
                )
            except Exception as gemini_error:
                print(f"⚠️ Gemini failed: {gemini_error}")
                raise LLMClientError(
                    "All AI services are currently unavailable. Gemini failed to generate questions. Please try again in a few moments."
                )

        raise LLMClientError(
            "All AI services are currently unavailable. Please try again in a few moments."
        )

    def _create_quiz_prompt(self, text_content: str, num_questions: int,
                          question_types: List[QuestionType],
                          difficulty_level: str,
                          focus_topics: List[str]) -> str:
        """Create a structured prompt for quiz generation"""

        # Create type descriptions
        type_descriptions = []
        if QuestionType.MULTIPLE_CHOICE in question_types:
            type_descriptions.append("multiple choice questions with 4 options")
        if QuestionType.TRUE_FALSE in question_types:
            type_descriptions.append("true/false questions")
        if QuestionType.SHORT_ANSWER in question_types:
            type_descriptions.append("short answer questions")

        types_text = " and ".join(type_descriptions)

        # Create focus topics text
        focus_text = ""
        if focus_topics:
            focus_text = f"Focus specifically on these topics: {', '.join(focus_topics)}."

        # Limit text content to avoid token limits
        content_preview = text_content[:4000] if len(text_content) > 4000 else text_content

        prompt = f"""You are an expert educator creating a quiz based on the following study material.

STUDY MATERIAL:
{content_preview}

TASK:
Create exactly {num_questions} quiz questions based on this material.
- Question types: {types_text}
- Difficulty: {difficulty_level}
- {focus_text}

FORMAT:
Use this exact format for each question:

QUESTION 1:
Type: multiple_choice
Question: What is the main concept discussed in the material?
Options: A) Option 1 B) Option 2 C) Option 3 D) Option 4
Answer: A
Explanation: Brief explanation of why this is correct.

QUESTION 2:
Type: true_false
Question: Statement to evaluate as true or false.
Answer: True
Explanation: Brief explanation.

Continue this pattern for all {num_questions} questions.

IMPORTANT:
- Base all questions on the provided material
- Make questions test understanding, not just memorization
- Ensure answers are clearly supported by the text
- Use the exact format shown above"""

        return prompt

    def _parse_quiz_response(self, response_text: str) -> List[QuizQuestion]:
        """Parse LLM response into QuizQuestion objects"""

        questions = []

        # Split by question markers
        question_blocks = re.split(r'QUESTION \d+:', response_text, flags=re.IGNORECASE)
        question_blocks = [block.strip() for block in question_blocks if block.strip()]

        for i, block in enumerate(question_blocks):
            try:
                question = self._parse_single_question(block, i + 1)
                if question:
                    questions.append(question)
            except Exception as e:
                print(f"⚠️ Failed to parse question {i+1}: {e}")
                print(f"Question block content: {block}")
                continue

        # If parsing failed, generate fallback questions
        if not questions:
            print("⚠️ LLM response parsing failed, generating fallback questions")
            return self._generate_fallback_questions(response_text, 3)

        return questions

    def _parse_single_question(self, block: str, question_num: int) -> Optional[QuizQuestion]:
        """Parse a single question block"""

        # Handle different line endings
        lines = [line.strip() for line in re.split(r'\r?\n', block) if line.strip()]

        question_type = None
        question_text = None
        options = []
        answer = None
        explanation = None

        # Debug parsing
        print(f"Parsing question block {question_num}:")
        print(lines)

        for line in lines:
            if line.lower().startswith('type:'):
                type_text = line.split(':', 1)[1].strip().lower()
                if 'multiple_choice' in type_text or 'multiple choice' in type_text:
                    question_type = QuestionType.MULTIPLE_CHOICE
                elif 'true_false' in type_text or 'true/false' in type_text:
                    question_type = QuestionType.TRUE_FALSE
                elif 'short_answer' in type_text or 'short answer' in type_text:
                    question_type = QuestionType.SHORT_ANSWER

            elif line.lower().startswith('question:'):
                question_text = line.split(':', 1)[1].strip()

            elif line.lower().startswith('options:'):
                options_text = line.split(':', 1)[1].strip()
                # Parse options like "A) Option 1 B) Option 2 C) Option 3 D) Option 4"
                option_matches = re.findall(r'[A-D]\)\s*([^A-D]+?)(?=\s*[A-D]\)|$)', options_text)
                options = [opt.strip() for opt in option_matches]

            elif line.lower().startswith('answer:'):
                answer = line.split(':', 1)[1].strip()

            elif line.lower().startswith('explanation:'):
                explanation = line.split(':', 1)[1].strip()

        # Validate required fields
        if not question_text or not answer:
            return None

        # Set default type if not specified
        if not question_type:
            question_type = QuestionType.MULTIPLE_CHOICE if options else QuestionType.SHORT_ANSWER

        # For multiple choice, ensure we have options
        if question_type == QuestionType.MULTIPLE_CHOICE and len(options) < 2:
            options = ["Option A", "Option B", "Option C", "Option D"]

        return QuizQuestion(
            id=str(uuid.uuid4()),
            question=question_text,
            question_type=question_type,
            options=options if question_type == QuestionType.MULTIPLE_CHOICE else None,
            correct_answer=answer,
            explanation=explanation or "Based on the study material provided.",
            difficulty="medium"
        )

    def _generate_fallback_questions(self, response_text: str, num_questions: int) -> List[QuizQuestion]:
        """Generate simple questions when parsing fails"""

        questions = []

        for i in range(min(num_questions, 3)):
            questions.append(QuizQuestion(
                id=str(uuid.uuid4()),
                question=f"Based on the study material, what is a key concept discussed in section {i+1}?",
                question_type=QuestionType.SHORT_ANSWER,
                options=None,
                correct_answer="Based on the text content provided",
                explanation="This question requires understanding the main concepts from the text."
            ))

        return questions

    def _generate_mock_quiz(self, text_content: str, num_questions: int,
                          question_types: List[QuestionType]) -> List[QuizQuestion]:
        """Generate mock quiz for development/testing"""

        questions = []
        content_preview = text_content[:200] + "..." if len(text_content) > 200 else text_content

        for i in range(num_questions):
            question_type = question_types[i % len(question_types)]

            if question_type == QuestionType.MULTIPLE_CHOICE:
                questions.append(QuizQuestion(
                    id=str(uuid.uuid4()),
                    question=f"What is the main topic discussed in the following text: '{content_preview}'?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=[
                        "The primary subject matter",
                        "A secondary topic",
                        "An unrelated concept",
                        "Background information"
                    ],
                    correct_answer="The primary subject matter",
                    explanation="This question tests comprehension of the main theme."
                ))
            elif question_type == QuestionType.TRUE_FALSE:
                questions.append(QuizQuestion(
                    id=str(uuid.uuid4()),
                    question=f"The text discusses relevant information about the subject matter.",
                    question_type=QuestionType.TRUE_FALSE,
                    options=None,
                    correct_answer="True",
                    explanation="Based on the provided content, this statement is accurate."
                ))
            else:  # SHORT_ANSWER
                questions.append(QuizQuestion(
                    id=str(uuid.uuid4()),
                    question=f"Describe the key concepts presented in the study material.",
                    question_type=QuestionType.SHORT_ANSWER,
                    options=None,
                    correct_answer="The material covers important concepts that require understanding and analysis.",
                    explanation="This question assesses comprehension and analytical thinking."
                ))

        return questions


def get_llm_client() -> LocalLLMClient:
    """Get LLM client instance"""
    return LocalLLMClient()

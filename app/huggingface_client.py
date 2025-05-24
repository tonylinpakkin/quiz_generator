"""
Hugging Face LLM client for quiz generation
Uses Hugging Face Inference API for real AI-powered quiz generation
"""

from typing import List, Optional, Dict, Any
import json
import re
import uuid
import httpx
import asyncio
import os
from app.models import QuizQuestion, QuestionType


class HuggingFaceClientError(Exception):
    """Custom exception for Hugging Face client errors"""
    pass


class HuggingFaceClient:
    """Client for interfacing with Hugging Face Inference API"""
    
    def __init__(self):
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
        self.model_name = os.getenv("HF_MODEL", "gpt2")
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))
        self.mock_mode = os.getenv("LLM_MOCK_MODE", "false").lower() == "true"
    
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
        
        if not self.api_token:
            raise HuggingFaceClientError("Hugging Face API token is required but not provided")
        
        # Check if Hugging Face API is available
        try:
            await self._check_hf_health()
            print(f"✅ Hugging Face API is available with model {self.model_name}")
        except Exception as health_error:
            print(f"⚠️ Hugging Face API not available: {health_error}")
            print(f"📝 Falling back to mock mode")
            return self._generate_mock_quiz(text_content, num_questions, question_types)
        
        try:
            return await self._generate_quiz_with_hf(
                text_content, num_questions, question_types, difficulty_level, focus_topics
            )
        except Exception as e:
            print(f"❌ Hugging Face generation failed: {e}")
            print(f"📝 Falling back to mock mode")
            return self._generate_mock_quiz(text_content, num_questions, question_types)
    
    async def _check_hf_health(self) -> None:
        """Check if Hugging Face API is available"""
        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json={"inputs": "Hello, world!"}
                )
                if response.status_code == 401:
                    raise HuggingFaceClientError("Invalid Hugging Face API token")
                elif response.status_code >= 400:
                    raise HuggingFaceClientError(f"API error: {response.status_code}")
                    
        except httpx.ConnectError:
            raise HuggingFaceClientError("Cannot connect to Hugging Face API")
        except httpx.TimeoutException:
            raise HuggingFaceClientError("Hugging Face API timeout")
        except Exception as e:
            raise HuggingFaceClientError(f"Hugging Face API check failed: {str(e)}")

    async def _generate_quiz_with_hf(self, text_content: str, num_questions: int,
                                   question_types: List[QuestionType],
                                   difficulty_level: str,
                                   focus_topics: List[str]) -> List[QuizQuestion]:
        """Generate quiz using Hugging Face Inference API"""
        
        # Create prompt
        prompt = self._create_quiz_prompt(
            text_content, num_questions, question_types, difficulty_level, focus_topics
        )
        
        print(f"🤖 Generating {num_questions} questions with Hugging Face {self.model_name}")
        
        # Prepare request
        headers = {"Authorization": f"Bearer {self.api_token}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    response_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    response_text = result.get("generated_text", "")
                else:
                    raise HuggingFaceClientError("Unexpected response format")
                
                if not response_text:
                    raise HuggingFaceClientError("Empty response from Hugging Face")
                
                print(f"📝 Received response from Hugging Face, parsing questions...")
                return self._parse_quiz_response(response_text)
                
            except httpx.TimeoutException:
                raise HuggingFaceClientError(f"Request timed out after {self.timeout} seconds")
            except httpx.HTTPStatusError as e:
                raise HuggingFaceClientError(f"HTTP error: {e.response.status_code}")
            except Exception as e:
                raise HuggingFaceClientError(f"Failed to generate quiz: {str(e)}")
    
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
        content_preview = text_content[:3000] if len(text_content) > 3000 else text_content
        
        prompt = f"""Create a quiz based on this study material:

STUDY MATERIAL:
{content_preview}

Create exactly {num_questions} {types_text} with {difficulty_level} difficulty. {focus_text}

Format each question exactly like this:

QUESTION 1:
Type: multiple_choice
Question: What is the main concept?
Options: A) Option 1 B) Option 2 C) Option 3 D) Option 4
Answer: A
Explanation: Brief explanation.

QUESTION 2:
Type: true_false
Question: This statement is correct.
Answer: True
Explanation: Brief explanation.

Make questions test understanding of the material provided."""

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
                continue
        
        # If parsing failed, generate fallback questions
        if not questions:
            print("⚠️ Response parsing failed, generating fallback questions")
            return self._generate_fallback_questions(response_text, 3)
        
        return questions
    
    def _parse_single_question(self, block: str, question_num: int) -> Optional[QuizQuestion]:
        """Parse a single question block"""
        
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        question_type = None
        question_text = None
        options = []
        answer = None
        explanation = None
        
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
                question=f"Based on the study material, what is a key concept discussed?",
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


def get_huggingface_client() -> HuggingFaceClient:
    """Get Hugging Face client instance"""
    return HuggingFaceClient()
"""
Groq LLM client for quiz generation
Uses Groq API for ultra-fast AI-powered quiz generation
"""

from typing import List, Optional, Dict, Any
import json
import re
import uuid
import httpx
import asyncio
import os
from app.models import QuizQuestion, QuestionType


class GroqClientError(Exception):
    """Custom exception for Groq client errors"""
    pass


class GroqClient:
    """Client for interfacing with Groq API"""

    def __init__(self):
        self.api_token = os.getenv("GROQ_API_KEY", "")
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))
        self.mock_mode = os.getenv("LLM_MOCK_MODE", "false").lower() == "true"

    async def generate_quiz(
            self,
            text_content: str,
            num_questions: int = 5,
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
            return self._generate_mock_quiz(text_content, num_questions,
                                            question_types)

        if not self.api_token:
            raise GroqClientError("Groq API key is required for quiz generation. Please check your API configuration.")

        # Check if Groq API is available
        try:
            await self._check_groq_health()
            print(f"✅ Groq API is available with model {self.model_name}")
        except Exception as health_error:
            raise GroqClientError(f"Groq API is not available: {health_error}. Please check your internet connection and API key.")

        try:
            return await self._generate_quiz_with_groq(text_content,
                                                       num_questions,
                                                       question_types,
                                                       difficulty_level,
                                                       focus_topics,
                                                       language)
        except Exception as e:
            print(f"❌ Groq generation failed: {e}")
            raise GroqClientError(f"Quiz generation failed: {e}. This could be due to rate limits or API issues. Please try again in a few moments.")

    async def _check_groq_health(self) -> None:
        """Check if Groq API is available"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messages": [{
                    "role": "user",
                    "content": "Hello"
                }],
                "model": self.model_name,
                "max_tokens": 10
            }

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(self.api_url,
                                             headers=headers,
                                             json=payload)

                if response.status_code == 401:
                    raise GroqClientError("Invalid Groq API key")
                elif response.status_code == 403:
                    raise GroqClientError(
                        "Groq API access denied - check your API key permissions"
                    )
                elif response.status_code >= 500:
                    raise GroqClientError(
                        f"Groq API server error: {response.status_code}")

        except httpx.ConnectError:
            raise GroqClientError("Cannot connect to Groq API")
        except httpx.TimeoutException:
            raise GroqClientError("Groq API timeout")
        except Exception as e:
            raise GroqClientError(f"Groq API check failed: {str(e)}")

    async def _generate_quiz_with_groq(
            self, text_content: str, num_questions: int,
            question_types: List[QuestionType], difficulty_level: str,
            focus_topics: List[str], language: str = "english") -> List[QuizQuestion]:
        """Generate quiz using Groq API"""

        # Create prompt
        prompt = self._create_quiz_prompt(text_content, num_questions,
                                          question_types, difficulty_level,
                                          focus_topics, language)

        print(
            f"🚀 Generating {num_questions} questions with Groq {self.model_name}"
        )

        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [{
                "role":
                "system",
                "content":
                """
                You are **QuizMaster**, a large-language model specialized in assessment design.  
                Your task is to generate high-quality quizzes from the **Source Material** I provide.
                """
            }, {
                "role": "user",
                "content": prompt
            }],
            "model":
            self.model_name,
            "max_tokens":
            2000,
            "temperature":
            0.7,
            "top_p":
            0.9
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.api_url,
                                             headers=headers,
                                             json=payload)
                response.raise_for_status()

                result = response.json()

                # Extract text from Groq response
                if "choices" in result and len(result["choices"]) > 0:
                    response_text = result["choices"][0]["message"]["content"]
                else:
                    raise GroqClientError("No choices in response")

                if not response_text:
                    raise GroqClientError("Empty response from Groq")

                print(f"📝 Received response from Groq, parsing questions...")
                return self._parse_quiz_response(response_text)

            except httpx.TimeoutException:
                raise GroqClientError(
                    f"Request timed out after {self.timeout} seconds")
            except httpx.HTTPStatusError as e:
                raise GroqClientError(f"HTTP error: {e.response.status_code}")
            except Exception as e:
                raise GroqClientError(f"Failed to generate quiz: {str(e)}")

    def _create_quiz_prompt(self, text_content: str, num_questions: int,
                            question_types: List[QuestionType],
                            difficulty_level: str,
                            focus_topics: List[str], language: str = "english") -> str:
        """Create a structured prompt for quiz generation"""

        # Create type descriptions
        type_descriptions = []
        if QuestionType.MULTIPLE_CHOICE in question_types:
            type_descriptions.append(
                "multiple choice questions with 4 options")
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
        content_preview = text_content[:10000] if len(
            text_content) > 10000 else text_content

        # Language instruction - detect input language and match it
        language_instruction = f"IMPORTANT: Detect the language of the study material and generate all questions, answers, and explanations in the SAME language as the input content. If the study material is in a specific language, use that exact language for the quiz. If it's in {language}, use {language}. "

        prompt = f"""Create a quiz based on this study material:

STUDY MATERIAL:
{content_preview}

{language_instruction}Create exactly {num_questions} {types_text} with medium difficulty. {focus_text}

IMPORTANT: 
- DETECT THE LANGUAGE of the study material and generate ALL content in that SAME language
- Create realistic, meaningful answer choices based on the study material - NOT placeholders
- Return ONLY valid JSON format with no additional text
- For multiple choice questions, use "mcq" type and include 4 meaningful options
- For true/false questions, use "true_false" type and omit options array
- For short answer questions, use "fill_blank" type and omit options array
- Use Bloom's taxonomy levels: remember, understand, apply, analyze, evaluate, create

Return the response in this exact JSON format:

{{
  "title": "Quiz about [topic from study material]",
  "difficulty": "{difficulty_level}",
  "questions": [
    {{
      "id": 1,
      "type": "mcq",
      "question": "What is the main purpose of the framework discussed?",
      "options": ["Specific meaningful option 1", "Specific meaningful option 2", "Specific meaningful option 3", "Specific meaningful option 4"],
      "answer": "Specific meaningful option 2",
      "explanation": "Brief explanation based on the study material.",
      "bloom_level": "understand"
    }},
    {{
      "id": 2,
      "type": "true_false",
      "question": "The framework supports only single-agent applications.",
      "answer": "false",
      "explanation": "The framework actually supports multi-agent applications.",
      "bloom_level": "remember"
    }}
  ]
}}

Create questions that test real understanding of the study material content."""

        return prompt

    def _parse_quiz_response(self, response_text: str) -> List[QuizQuestion]:
        """Parse JSON response into QuizQuestion objects"""
        try:
            import json
            
            # Clean response text
            response_text = response_text.strip()
            
            # Try to find JSON content if wrapped in text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = response_text[json_start:json_end]
                # Clean up any trailing commas that might cause parsing errors
                json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
            else:
                json_content = response_text
            
            # Parse JSON response
            try:
                quiz_data = json.loads(json_content)
            except json.JSONDecodeError:
                # If parsing fails, try to fix common JSON issues
                json_content = re.sub(r'(?<!\\)"(?=(.*?".*?{.*?}.*?".*?))', r'\"', json_content)
                quiz_data = json.loads(json_content)
            questions = []
            
            for q_data in quiz_data.get('questions', []):
                # Map question types
                question_type_map = {
                    'mcq': QuestionType.MULTIPLE_CHOICE,
                    'true_false': QuestionType.TRUE_FALSE,
                    'fill_blank': QuestionType.SHORT_ANSWER
                }
                
                question_type = question_type_map.get(q_data.get('type'), QuestionType.MULTIPLE_CHOICE)
                
                # Handle different answer formats
                if question_type == QuestionType.MULTIPLE_CHOICE:
                    options = q_data.get('options', [])
                    answer = q_data.get('answer', '')
                    # Convert answer to letter format (A, B, C, D)
                    if answer in options:
                        correct_answer = chr(65 + options.index(answer))  # A, B, C, D
                    else:
                        correct_answer = 'A'  # Default fallback
                elif question_type == QuestionType.TRUE_FALSE:
                    options = ['True', 'False']
                    answer = q_data.get('answer', '').lower()
                    correct_answer = 'A' if answer == 'true' else 'B'
                else:  # SHORT_ANSWER
                    options = None
                    correct_answer = q_data.get('answer', '')
                
                question = QuizQuestion(
                    id=str(uuid.uuid4()),
                    question=q_data.get('question', ''),
                    question_type=question_type,
                    options=options,
                    correct_answer=correct_answer,
                    explanation=q_data.get('explanation', ''),
                    difficulty=q_data.get('bloom_level', 'medium')
                )
                questions.append(question)
            
            print(f"✅ Successfully parsed {len(questions)} questions from JSON response")
            return questions
            
        except Exception as e:
            print(f"❌ JSON parsing error: {str(e)}")
            print("📝 Falling back to text parsing...")
            # Fall back to original text parsing method
            return self._parse_text_response(response_text)
        except Exception as e:
            print(f"❌ Error parsing JSON response: {str(e)}")
            return self._parse_text_response(response_text)
    
    def _parse_text_response(self, response_text: str) -> List[QuizQuestion]:
        """Fallback text parsing method"""
        questions = []

        # Split by question markers
        question_blocks = re.split(r'QUESTION \d+:',
                                   response_text,
                                   flags=re.IGNORECASE)
        question_blocks = [
            block.strip() for block in question_blocks if block.strip()
        ]

        for i, block in enumerate(question_blocks):
            try:
                question = self._parse_single_question(block, i + 1)
                if question:
                    questions.append(question)
            except Exception as e:
                print(f"⚠️ Failed to parse question {i+1}: {e}")
                continue

        # If parsing failed, raise an error instead of using fallback
        if not questions:
            print("❌ Response parsing failed completely")
            raise GroqClientError("The AI response could not be parsed into valid questions. This might be due to formatting issues in the AI response. Please try again.")

        return questions

    def _parse_single_question(self, block: str,
                               question_num: int) -> Optional[QuizQuestion]:
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
                option_matches = re.findall(
                    r'[A-D]\)\s*([^A-D]+?)(?=\s*[A-D]\)|$)', options_text)
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

        return QuizQuestion(id=str(uuid.uuid4()),
                            question=question_text,
                            question_type=question_type,
                            options=options if question_type
                            == QuestionType.MULTIPLE_CHOICE else None,
                            correct_answer=answer,
                            explanation=explanation
                            or "Based on the study material provided.",
                            difficulty="medium")

    def _generate_fallback_questions(self, response_text: str,
                                     num_questions: int) -> List[QuizQuestion]:
        """Generate simple questions when parsing fails"""

        questions = []
        question_types = [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.SHORT_ANSWER]

        for i in range(num_questions):
            question_type = question_types[i % len(question_types)]
            
            if question_type == QuestionType.MULTIPLE_CHOICE:
                questions.append(
                    QuizQuestion(
                        id=str(uuid.uuid4()),
                        question=f"Based on the study material, what is key concept #{i+1} discussed?",
                        question_type=QuestionType.MULTIPLE_CHOICE,
                        options=[
                            "The primary concept",
                            "A secondary concept",
                            "An unrelated concept",
                            "Background information"
                        ],
                        correct_answer="The primary concept",
                        explanation="This question tests comprehension of key concepts."
                    ))
            elif question_type == QuestionType.TRUE_FALSE:
                questions.append(
                    QuizQuestion(
                        id=str(uuid.uuid4()),
                        question=f"Statement #{i+1} from the text requires verification.",
                        question_type=QuestionType.TRUE_FALSE,
                        options=None,
                        correct_answer="True",
                        explanation="Based on the study material provided."
                    ))
            else:  # SHORT_ANSWER
                questions.append(
                    QuizQuestion(
                        id=str(uuid.uuid4()),
                        question=f"Explain key concept #{i+1} from the study material.",
                        question_type=QuestionType.SHORT_ANSWER,
                        options=None,
                        correct_answer="Answer should reflect understanding of the material.",
                        explanation="Tests deeper comprehension of the concepts."
                    ))

        return questions

    def _generate_mock_quiz(
            self, text_content: str, num_questions: int,
            question_types: List[QuestionType]) -> List[QuizQuestion]:
        """Generate mock quiz for development/testing"""

        questions = []
        content_preview = text_content[:200] + "..." if len(
            text_content) > 200 else text_content

        for i in range(num_questions):
            question_type = question_types[i % len(question_types)]

            if question_type == QuestionType.MULTIPLE_CHOICE:
                questions.append(
                    QuizQuestion(
                        id=str(uuid.uuid4()),
                        question=
                        f"What is the main topic discussed in the following text: '{content_preview}'?",
                        question_type=QuestionType.MULTIPLE_CHOICE,
                        options=[
                            "The primary subject matter", "A secondary topic",
                            "An unrelated concept", "Background information"
                        ],
                        correct_answer="The primary subject matter",
                        explanation=
                        "This question tests comprehension of the main theme.")
                )
            elif question_type == QuestionType.TRUE_FALSE:
                questions.append(
                    QuizQuestion(
                        id=str(uuid.uuid4()),
                        question=
                        f"The text discusses relevant information about the subject matter.",
                        question_type=QuestionType.TRUE_FALSE,
                        options=None,
                        correct_answer="True",
                        explanation=
                        "Based on the provided content, this statement is accurate."
                    ))
            else:  # SHORT_ANSWER
                questions.append(
                    QuizQuestion(
                        id=str(uuid.uuid4()),
                        question=
                        f"Describe the key concepts presented in the study material.",
                        question_type=QuestionType.SHORT_ANSWER,
                        options=None,
                        correct_answer=
                        "The material covers important concepts that require understanding and analysis.",
                        explanation=
                        "This question assesses comprehension and analytical thinking."
                    ))

        return questions


def get_groq_client() -> GroqClient:
    """Get Groq client instance"""
    return GroqClient()

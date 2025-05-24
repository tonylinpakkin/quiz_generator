"""
Configuration settings for Quiz Generator
"""

import os
from typing import Optional

class LLMConfig:
    """Configuration for LLM integration"""
    
    def __init__(self):
        self.mock_mode = os.getenv("LLM_MOCK_MODE", "true").lower() == "true"
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model_name = os.getenv("LLM_MODEL", "llama3.2")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))
        
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode"""
        return self.mock_mode
    
    def get_ollama_url(self) -> str:
        """Get Ollama server URL"""
        return self.ollama_url
    
    def get_model_name(self) -> str:
        """Get LLM model name"""
        return self.model_name
    
    def get_timeout(self) -> int:
        """Get request timeout in seconds"""
        return self.timeout

# Global config instance
config = LLMConfig()
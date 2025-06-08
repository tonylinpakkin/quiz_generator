"""
Configuration settings for Quiz Generator
"""

import os

class LLMConfig:
    """Configuration for LLM integration"""
    
    def __init__(self):
        self.mock_mode = os.getenv("LLM_MOCK_MODE", "true").lower() == "true"
        self.model_name = os.getenv("LLM_MODEL", "llama3.2")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))
        
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode"""
        return self.mock_mode
    
    def get_model_name(self) -> str:
        """Get LLM model name"""
        return self.model_name
    
    def get_timeout(self) -> int:
        """Get request timeout in seconds"""
        return self.timeout

# Global config instance
config = LLMConfig()

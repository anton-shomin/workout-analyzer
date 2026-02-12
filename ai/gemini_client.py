"""
Gemini API client for workout analysis.

Uses Google's Gemini model to analyze workout data and provide
structured insights about training sessions.
"""

import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default model configuration
DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiClient:
    """Client for interacting with Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
        """
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY in .env")
        
        self.client = genai.Client(api_key=self.api_key)
    
    def analyze_workout(
        self,
        workout_data: dict,
        calories: int,
        muscle_balance: dict
    ) -> str:
        """
        Analyze a workout using Gemini API.
        
        Args:
            workout_data: Parsed workout data from workout_parser.
            calories: Calculated calories burned.
            muscle_balance: Dictionary of muscle group percentages.
            
        Returns:
            Markdown formatted analysis text.
        """
        from ai.prompts import build_workout_prompt, clean_markdown_response
        prompt = build_workout_prompt(workout_data, calories, muscle_balance)
        
        try:
            response = self.client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
            )
            
            if response.text:
                return clean_markdown_response(response.text)
            else:
                return "Не удалось получить анализ: пустой ответ от API."
                
        except Exception as e:
            # Raise exception to allow fallback handling in main.py
            raise e


def analyze_workout(
    workout_data: dict,
    calories: int,
    muscle_balance: dict
) -> str:
    """
    Analyze a workout using Gemini API.
    
    This is a convenience function that creates a client and makes the request.
    
    Args:
        workout_data: Parsed workout data from workout_parser.
        calories: Calculated calories burned.
        muscle_balance: Dictionary of muscle group percentages.
        
    Returns:
        Markdown formatted analysis text.
    """
    client = GeminiClient()
    return client.analyze_workout(workout_data, calories, muscle_balance)

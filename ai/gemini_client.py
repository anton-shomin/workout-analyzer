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
        muscle_balance: dict,
        actual_duration_minutes: int = 0
    ) -> str:
        """
        Analyze a workout using Gemini API.
        
        Args:
            workout_data: Parsed workout data from workout_parser.
            calories: Calculated calories burned.
            muscle_balance: Dictionary of muscle group percentages.
            actual_duration_minutes: Actual duration of the workout in minutes.
            
        Returns:
            Markdown formatted analysis text.
        """
        from ai.prompts import build_workout_prompt, clean_markdown_response
        prompt = build_workout_prompt(workout_data, calories, muscle_balance, actual_duration_minutes)
        
        # Load system prompt
        try:
            template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Templates', 'system_prompt.txt')
            with open(template_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
        except FileNotFoundError:
            system_prompt = "You are an expert fitness coach specializing in kettlebell training. Provide structured, markdown-formatted analysis."

        try:
            # Configure generation with system instruction
            config = {
                'system_instruction': system_prompt
            }
            
            response = self.client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
                config=config
            )
            
            if response.text:
                return clean_markdown_response(response.text)
            else:
                return "Не удалось получить анализ: пустой ответ от API."
                
        except Exception as e:
            # Raise exception to allow fallback handling in main.py
            raise e




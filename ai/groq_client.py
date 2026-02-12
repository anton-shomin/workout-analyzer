"""
Groq API client for workout analysis.

Uses Groq's Llama models as a fallback for workout analysis.
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default model configuration
DEFAULT_MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient:
    """Client for interacting with Groq API."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the Groq client.
        
        Args:
            api_key: Groq API key. If not provided, reads from GROQ_API_KEY env var.
            model: Model to use. Defaults to DEFAULT_MODEL.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY in .env")
            
        self.model = model or DEFAULT_MODEL
    
    def _make_request(self, messages: list) -> dict:
        """
        Make a request to the Groq API.
        
        Args:
            messages: List of message dictionaries.
            
        Returns:
            API response as dictionary.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
        }
        
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_workout(
        self,
        workout_data: dict,
        calories: int,
        muscle_balance: dict,
        actual_duration_minutes: int = 0
    ) -> str:
        """
        Analyze a workout using Groq API.
        
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

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response_data = self._make_request(messages)
            
            content = response_data['choices'][0]['message']['content']
            
            return clean_markdown_response(content)
            
        except Exception as e:
            return f"Ошибка при анализе тренировки (Groq): {str(e)}"

"""
Perplexity API client for searching exercise data.

Uses the Perplexity Sonar model to find scientific data about exercises
including MET values, calorie calculations, and muscle groups.
"""

import json
import os
from typing import Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar"


class PerplexityClient:
    """Client for interacting with Perplexity API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Perplexity client.
        
        Args:
            api_key: Perplexity API key. If not provided, reads from PERPLEXITY_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key not found. Set PERPLEXITY_API_KEY in .env")
    
    def _make_request(self, payload: dict) -> dict:
        """
        Make a request to the Perplexity API.
        
        Args:
            payload: Request payload with model and messages.
            
        Returns:
            API response as dictionary.
            
        Raises:
            requests.RequestException: If the request fails.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    
    def _build_exercise_prompt(
        self,
        name: str,
        equipment: str,
        components: Optional[list[str]] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Build a prompt for Perplexity to analyze an exercise.
        
        Args:
            name: Name of the exercise.
            equipment: Equipment used.
            components: List of components (for combo exercises).
            description: Optional description of the exercise.
            
        Returns:
            Formatted prompt string.
        """
        prompt = f"""Analyze this kettlebell exercise: "{name}"
Equipment: {equipment}"""
        
        if components:
            prompt += f"\nComponents: {', '.join(components)}"
        
        if description:
            prompt += f"\nDescription: {description}"
        
        prompt += """
        
Provide scientific data:
1. MET value (Metabolic Equivalent of Task) - numerical value
2. Estimated calories per repetition for 70kg person
3. Primary muscle groups worked (from: shoulders, chest, back, core, legs, arms, fullBody)

Return in JSON format:
{
  "met_base": <number>,
  "cal_per_rep": <number>,
  "muscle_groups": [<list>],
  "reasoning": "<brief explanation>"
}
"""
        return prompt
    
    def _parse_response(self, response: dict) -> dict:
        """
        Parse the Perplexity API response.
        
        Args:
            response: Raw API response dictionary.
            
        Returns:
            Parsed data with met_base, cal_per_rep, muscle_groups, reasoning.
        """
        try:
            content = response["choices"][0]["message"]["content"]
            return self._extract_json_data(content)
        except (KeyError, IndexError) as e:
            raise ValueError(f"Failed to parse Perplexity response: {e}")
    
    def _extract_json_data(self, text: str) -> dict:
        """
        Extract JSON data from text response.
        
        Args:
            text: Response text that may contain JSON.
            
        Returns:
            Parsed JSON data.
        """
        # Try to find JSON block in the response
        import re
        
        # Look for JSON in code blocks
        json_match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find any JSON object
            json_match = re.search(r'({.*})', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Return text as-is with default structure
                return {
                    "met_base": None,
                    "cal_per_rep": None,
                    "muscle_groups": [],
                    "reasoning": text
                }
        
        try:
            data = json.loads(json_str)
            return {
                "met_base": data.get("met_base"),
                "cal_per_rep": data.get("cal_per_rep"),
                "muscle_groups": data.get("muscle_groups", []),
                "reasoning": data.get("reasoning", "")
            }
        except json.JSONDecodeError:
            return {
                "met_base": None,
                "cal_per_rep": None,
                "muscle_groups": [],
                "reasoning": text
            }
    
    def search_exercise_data(
        self,
        name: str,
        equipment: str,
        components: Optional[list[str]] = None,
        description: Optional[str] = None
    ) -> dict:
        """
        Search for exercise data using Perplexity API.
        
        Args:
            name: Name of the exercise.
            equipment: Equipment used.
            components: List of components (for combo exercises).
            description: Optional description of the exercise.
            
        Returns:
            Dictionary with:
            - met_base: MET value (float)
            - cal_per_rep: Calories per repetition (float)
            - muscle_groups: List of muscle groups (list[str])
            - reasoning: Brief explanation (str)
        """
        prompt = self._build_exercise_prompt(name, equipment, components, description)
        
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a fitness expert with knowledge of exercise physiology. Provide accurate, scientific data about exercises."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "search_mode": "web",
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        try:
            response = self._make_request(payload)
            return self._parse_response(response)
        except requests.RequestException as e:
            # Return fallback values on API error
            return {
                "met_base": None,
                "cal_per_rep": None,
                "muscle_groups": [],
                "reasoning": f"API error: {str(e)}"
            }


def search_exercise_data(
    name: str,
    equipment: str,
    components: list[str] = None,
    description: str = None
) -> dict:
    """
    Search for exercise data using Perplexity API.
    
    This is a convenience function that creates a client and makes the request.
    
    Args:
        name: Name of the exercise.
        equipment: Equipment used.
        components: List of components (for combo exercises).
        description: Optional description of the exercise.
        
    Returns:
        Dictionary with:
        - met_base: MET value (float)
        - cal_per_rep: Calories per repetition (float)
        - muscle_groups: List of muscle groups (list[str])
        - reasoning: Brief explanation (str)
    """
    client = PerplexityClient()
    return client.search_exercise_data(name, equipment, components, description)

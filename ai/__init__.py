"""
AI integration module for workout analysis.

Provides clients for Perplexity API (exercise data search) and
Gemini API (workout analysis).
"""

from .perplexity_client import PerplexityClient, search_exercise_data
from .gemini_client import GeminiClient, analyze_workout

__all__ = [
    "PerplexityClient",
    "search_exercise_data",
    "GeminiClient",
    "analyze_workout",
]

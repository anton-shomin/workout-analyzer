"""
AI integration module for workout analysis.

Provides clients for Perplexity API (exercise data search) and
Gemini API (workout analysis).
"""

from .perplexity_client import PerplexityClient
from .gemini_client import GeminiClient

__all__ = [
    "PerplexityClient",
    "GeminiClient",
    "analyze_workout",
]

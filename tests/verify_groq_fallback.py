import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules that might not be available or have side effects
sys.modules['utils.helpers'] = MagicMock()
sys.modules['parsers.exercise_parser'] = MagicMock()
sys.modules['parsers.workout_parser'] = MagicMock()
sys.modules['cache.exercise_cache'] = MagicMock()
sys.modules['calculators.calorie_calculator'] = MagicMock()
sys.modules['writers.markdown_writer'] = MagicMock()

# Now import main, but we need to mock the imports inside it too if they are global
# main.py imports these at top level:
# from utils.helpers import load_config, ensure_dir_exists, sanitize_filename
# from parsers.exercise_parser import parse_exercise_file, update_exercise_file, needs_enrichment
# from parsers.workout_parser import parse_workout_file, get_workout_summary
# from cache.exercise_cache import get_exercise_data, get_cache_path
# from calculators.calorie_calculator import calculate_workout_calories, calculate_muscle_balance
# from writers.markdown_writer import write_analysis_to_workout

# Since I mocked sys.modules, import main should work and use mocks
import main

class TestGroqFallback(unittest.TestCase):
    @patch('ai.gemini_client.GeminiClient')
    @patch('ai.groq_client.GroqClient')
    def test_fallback_to_groq(self, mock_groq_class, mock_gemini_class):
        # Setup mocks
        main.parse_workout_file = MagicMock(return_value={
            'exercises': [{'name': 'Swing'}],
            'scheme': {},
            'date': '2023-10-27',
            'weight': 80
        })
        main.get_exercise_data = MagicMock(return_value={'met_base': 10})
        main.calculate_workout_calories = MagicMock(return_value={
            'total_calories': 500,
            'total_reps': 100,
            'estimated_time_minutes': 30
        })
        main.calculate_muscle_balance = MagicMock(return_value={'balance': {}})
        main.write_analysis_to_workout = MagicMock()
        
        # Setup Gemini to fail
        mock_gemini_instance = mock_gemini_class.return_value
        mock_gemini_instance.analyze_workout.side_effect = Exception("Gemini is down")
        
        # Setup Groq to succeed
        mock_groq_instance = mock_groq_class.return_value
        mock_groq_instance.analyze_workout.return_value = "Groq analysis result"
        
        # Config mock
        config = {
            'obsidian': {
                'vault_path': '/tmp',
                'workouts_folder': 'workouts',
                'exercises_folder': 'exercises',
                'cache_folder': 'cache'
            },
            'user': {'default_weight': 80},
            'calculation': {'base_weight': 80},
            'ai': {'groq_model': 'test-model'}
        }
        
        # Create dummy file listing to bypass file existence check
        with patch('os.listdir', return_value=['2023-10-27.md']), \
             patch('os.path.exists', return_value=True):
            
            # Run function
            main.analyze_workout('2023-10-27', config)
            
            # Verify Gemini was called
            mock_gemini_instance.analyze_workout.assert_called_once()
            
            # Verify Groq was called
            mock_groq_instance.analyze_workout.assert_called_once()
            
            # Verify result was written (we check if write_analysis_to_workout was called with Groq result)
            args, _ = main.write_analysis_to_workout.call_args
            # Args: workout_path, analysis_data, ai_analysis_text, user_weight
            self.assertEqual(args[2], "Groq analysis result")
            print("\n✅ Verification passed: Fallback to Groq worked as expected.")

if __name__ == '__main__':
    unittest.main()

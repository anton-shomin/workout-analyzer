#!/usr/bin/env python3
"""
Workout Analyzer - Main Orchestrator

CLI tool for analyzing Obsidian workout markdown files.
Provides workout analysis, exercise enrichment, and metrics calculation.

Usage:
    python main.py --update-exercises
    python main.py --update-exercise "Exercise Name"
    python main.py --analyze-workout 2026-02-11
    python main.py --analyze-latest
    python main.py --reanalyze-all
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils.helpers import load_config, ensure_dir_exists, sanitize_filename
from parsers.exercise_parser import parse_exercise_file, update_exercise_file, needs_enrichment
from parsers.workout_parser import parse_workout_file, get_workout_summary
from cache.exercise_cache import get_exercise_data, get_cache_path
from calculators.calorie_calculator import calculate_workout_calories, calculate_muscle_balance
from writers.markdown_writer import write_analysis_to_workout


def update_all_exercises(config: Dict) -> None:
    """
    Update all exercises in the Exercises folder that need enrichment.
    
    Args:
        config: Configuration dictionary.
    """
    vault_path = config['obsidian']['vault_path']
    exercises_folder = config['obsidian']['exercises_folder']
    cache_folder = config['obsidian']['cache_folder']
    
    full_exercises_path = os.path.join(vault_path, exercises_folder)
    
    if not os.path.exists(full_exercises_path):
        print(f"❌ Exercises folder not found: {full_exercises_path}")
        return
    
    # Ensure cache directory exists
    ensure_dir_exists(os.path.join(vault_path, cache_folder))
    
    # Find all exercise files
    exercise_files = [
        os.path.join(full_exercises_path, f) 
        for f in os.listdir(full_exercises_path) 
        if f.endswith('.md')
    ]
    
    print(f"🔍 Found {len(exercise_files)} exercise files")
    
    updated_count = 0
    skipped_count = 0
    
    for filepath in exercise_files:
        try:
            exercise_data = parse_exercise_file(filepath)
            exercise_name = exercise_data.get('name', os.path.basename(filepath))
            
            if not needs_enrichment(exercise_data):
                print(f"⏭️  Skipping: {exercise_name} (already enriched)")
                skipped_count += 1
                continue
            
            print(f"📝 Enriching: {exercise_name}")
            
            # Get enriched data from Perplexity via cache
            enriched_data = get_exercise_data(
                name=exercise_name,
                equipment=exercise_data.get('equipment', ''),
                vault_path=vault_path,
                cache_dir=os.path.join(vault_path, cache_folder),
                exercises_folder=full_exercises_path
            )
            
            # Update the exercise file
            update_exercise_file(filepath, {
                'met_base': enriched_data.get('met_base'),
                'cal_per_rep': enriched_data.get('cal_per_rep'),
                'muscle_groups': enriched_data.get('muscle_groups', [])
            })
            
            updated_count += 1
            print(f"✅ Updated: {exercise_name}")
            
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Updated: {updated_count}")
    print(f"   Skipped (already enriched): {skipped_count}")
    print(f"   Total: {len(exercise_files)}")


def update_single_exercise(name: str, config: Dict) -> None:
    """
    Update a single exercise by name.
    
    Args:
        name: Exercise name to update.
        config: Configuration dictionary.
    """
    vault_path = config['obsidian']['vault_path']
    exercises_folder = config['obsidian']['exercises_folder']
    cache_folder = config['obsidian']['cache_folder']
    
    full_exercises_path = os.path.join(vault_path, exercises_folder)
    
    # Try to find the exercise file
    exercise_path = None
    for filename in os.listdir(full_exercises_path):
        if filename.endswith('.md'):
            filepath = os.path.join(full_exercises_path, filename)
            try:
                exercise_data = parse_exercise_file(filepath)
                if exercise_data.get('name', '').lower() == name.lower():
                    exercise_path = filepath
                    break
            except Exception:
                continue
    
    if not exercise_path:
        print(f"❌ Exercise not found: {name}")
        return
    
    try:
        exercise_data = parse_exercise_file(exercise_path)
        print(f"📝 Enriching: {name}")
        
        enriched_data = get_exercise_data(
            name=name,
            equipment=exercise_data.get('equipment', ''),
            vault_path=vault_path,
            cache_dir=os.path.join(vault_path, cache_folder),
            exercises_folder=full_exercises_path
        )
        
        update_exercise_file(exercise_path, {
            'met_base': enriched_data.get('met_base'),
            'cal_per_rep': enriched_data.get('cal_per_rep'),
            'muscle_groups': enriched_data.get('muscle_groups', [])
        })
        
        print(f"✅ Updated: {name}")
        
    except Exception as e:
        print(f"❌ Error updating exercise {name}: {e}")


def analyze_workout(date: str, config: Dict) -> None:
    """
    Analyze a workout by date.
    
    Args:
        date: Workout date in YYYY-MM-DD format.
        config: Configuration dictionary.
    """
    vault_path = config['obsidian']['vault_path']
    workouts_folder = config['obsidian']['workouts_folder']
    exercises_folder = config['obsidian']['exercises_folder']
    cache_folder = config['obsidian']['cache_folder']
    
    full_workouts_path = os.path.join(vault_path, workouts_folder)
    full_exercises_path = os.path.join(vault_path, exercises_folder)
    
    # Find workout file by date
    workout_path = None
    for filename in os.listdir(full_workouts_path):
        if filename.endswith('.md') and date in filename:
            workout_path = os.path.join(full_workouts_path, filename)
            break
    
    if not workout_path:
        print(f"❌ Workout not found for date: {date}")
        return
    
    try:
        print(f"📊 Analyzing workout: {date}")
        
        # Parse workout file
        workout_data = parse_workout_file(workout_path)
        print(f"   Found {len(workout_data.get('exercises', []))} exercises")
        
        # Get data for each exercise
        exercises_data = []
        for exercise in workout_data.get('exercises', []):
            ex_name = exercise.get('name', '')
            ex_equipment = exercise.get('equipment', '')
            
            data = get_exercise_data(
                name=ex_name,
                equipment=ex_equipment,
                vault_path=vault_path,
                cache_dir=os.path.join(vault_path, cache_folder),
                exercises_folder=full_exercises_path
            )
            exercises_data.append(data)
            print(f"   - {ex_name}: {data.get('source', 'unknown')}")
        
        # Calculate calories
        user_weight = workout_data.get('weight', config['user']['default_weight'])
        base_weight = config['calculation']['base_weight']
        
        calories_result = calculate_workout_calories(
            workout_data, exercises_data, user_weight, base_weight
        )
        
        # Calculate muscle balance
        muscle_balance = calculate_muscle_balance(exercises_data, workout_data.get('scheme', {}))
        
        # Get AI analysis from Gemini with fallback to Groq
        try:
            from ai.gemini_client import GeminiClient
            gemini_client = GeminiClient()
            gemini_analysis = gemini_client.analyze_workout(
                workout_data, 
                int(calories_result['total_calories']),
                {k: v.get('percentage', 0) for k, v in muscle_balance.get('balance', {}).items()},
                int(calories_result['estimated_time_minutes'])
            )
        except Exception as e:
            print(f"⚠️  Gemini API error: {e}")
            print("🔄 Switching to Groq API...")
            try:
                from ai.groq_client import GroqClient
                groq_model = config.get('ai', {}).get('groq_model', 'llama-3.3-70b-versatile')
                groq_client = GroqClient(model=groq_model)
                gemini_analysis = groq_client.analyze_workout(
                    workout_data,
                    int(calories_result['total_calories']),
                    {k: v.get('percentage', 0) for k, v in muscle_balance.get('balance', {}).items()},
                    int(calories_result['estimated_time_minutes'])
                )
            except Exception as groq_e:
                print(f"⚠️  Groq API error: {groq_e}")
                gemini_analysis = "Не удалось получить анализ от AI (Gemini и Groq недоступны)."
        
        # Prepare analysis for writer
        analysis = {
            'total_reps': calories_result['total_reps'],
            'total_calories': calories_result['total_calories'],
            'estimated_time_minutes': calories_result['estimated_time_minutes'],
            'average_met': sum(d.get('met_base', 0) for d in exercises_data) / max(len(exercises_data), 1),
            'muscle_groups_balance': {k: v.get('percentage', 0) for k, v in muscle_balance.get('balance', {}).items()}
        }
        
        # Write analysis to file
        write_analysis_to_workout(workout_path, analysis, gemini_analysis, user_weight)
        
        print(f"\n✅ Analysis complete!")
        print(f"   Total reps: {calories_result['total_reps']}")
        print(f"   Calories: ~{calories_result['total_calories']:.0f} kcal")
        print(f"   Time: ~{calories_result['estimated_time_minutes']:.0f} minutes")
        print(f"   Primary muscle: {muscle_balance.get('primary_muscle', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error analyzing workout: {e}")
        import traceback
        traceback.print_exc()


def analyze_latest_workout(config: Dict) -> None:
    """
    Find and analyze the latest workout.
    
    Args:
        config: Configuration dictionary.
    """
    vault_path = config['obsidian']['vault_path']
    workouts_folder = config['obsidian']['workouts_folder']
    
    full_workouts_path = os.path.join(vault_path, workouts_folder)
    
    if not os.path.exists(full_workouts_path):
        print(f"❌ Workouts folder not found: {full_workouts_path}")
        return
    
    # Find all workout files and sort by date in filename
    workout_files = [
        os.path.join(full_workouts_path, f) 
        for f in os.listdir(full_workouts_path) 
        if f.endswith('.md')
    ]
    
    if not workout_files:
        print("❌ No workout files found")
        return
    
    # Sort by filename (date)
    workout_files.sort(key=lambda x: os.path.basename(x))
    
    # Get the latest
    latest_workout = workout_files[-1]
    latest_date = os.path.basename(latest_workout).replace('.md', '')
    
    print(f"📅 Found latest workout: {latest_date}")
    analyze_workout(latest_date, config)


def reanalyze_all_workouts(config: Dict) -> None:
    """
    Reanalyze all workouts in the Workouts folder.
    
    Args:
        config: Configuration dictionary.
    """
    vault_path = config['obsidian']['vault_path']
    workouts_folder = config['obsidian']['workouts_folder']
    
    full_workouts_path = os.path.join(vault_path, workouts_folder)
    
    if not os.path.exists(full_workouts_path):
        print(f"❌ Workouts folder not found: {full_workouts_path}")
        return
    
    workout_files = [
        os.path.join(full_workouts_path, f) 
        for f in os.listdir(full_workouts_path) 
        if f.endswith('.md')
    ]
    
    # Sort by filename (date)
    workout_files.sort(key=lambda x: os.path.basename(x))
    
    print(f"🔄 Reanalyzing {len(workout_files)} workouts...\n")
    
    analyzed = 0
    errors = 0
    
    for workout_path in workout_files:
        date = os.path.basename(workout_path).replace('.md', '')
        
        # Extract date from filename for analysis
        date_match = date
        if '-' in date:
            try:
                # Validate it's a proper date
                datetime.strptime(date, '%Y-%m-%d')
                date_match = date
            except ValueError:
                date_match = date
        
        try:
            analyze_workout(date_match, config)
            analyzed += 1
            print()
        except Exception as e:
            print(f"❌ Error analyzing {date}: {e}")
            errors += 1
    
    print(f"\n📊 Summary:")
    print(f"   Analyzed: {analyzed}")
    print(f"   Errors: {errors}")
    print(f"   Total: {len(workout_files)}")


def show_status(config: Dict) -> None:
    """
    Show status of the workout analyzer setup.
    
    Args:
        config: Configuration dictionary.
    """
    print("📋 Workout Analyzer Status")
    print("=" * 40)
    
    vault_path = config['obsidian']['vault_path']
    exercises_folder = config['obsidian']['exercises_folder']
    workouts_folder = config['obsidian']['workouts_folder']
    cache_folder = config['obsidian']['cache_folder']
    
    # Check paths
    print("\n📁 Paths:")
    print(f"   Vault: {vault_path}")
    print(f"   Exercises: {os.path.join(vault_path, exercises_folder)}")
    print(f"   Workouts: {os.path.join(vault_path, workouts_folder)}")
    print(f"   Cache: {os.path.join(vault_path, cache_folder)}")
    
    # Count files
    full_exercises_path = os.path.join(vault_path, exercises_folder)
    full_workouts_path = os.path.join(vault_path, workouts_folder)
    full_cache_path = os.path.join(vault_path, cache_folder)
    
    exercise_count = 0
    if os.path.exists(full_exercises_path):
        exercise_count = len([f for f in os.listdir(full_exercises_path) if f.endswith('.md')])
    
    workout_count = 0
    if os.path.exists(full_workouts_path):
        workout_count = len([f for f in os.listdir(full_workouts_path) if f.endswith('.md')])
    
    cache_count = 0
    if os.path.exists(full_cache_path):
        cache_count = len([f for f in os.listdir(full_cache_path) if f.endswith('.json')])
    
    print("\n📊 Statistics:")
    print(f"   Exercises: {exercise_count}")
    print(f"   Workouts: {workout_count}")
    print(f"   Cached exercises: {cache_count}")
    
    # Check API keys
    from dotenv import load_dotenv
    load_dotenv()
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    perplexity_key = os.getenv('PERPLEXITY_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    print("\n🔑 API Keys:")
    print(f"   Gemini: {'✅ Set' if gemini_key else '❌ Not set'}")
    print(f"   Perplexity: {'✅ Set' if perplexity_key else '❌ Not set'}")
    print(f"   Groq: {'✅ Set' if groq_key else '❌ Not set'}")
    
    print("\n" + "=" * 40)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Obsidian Workout Analyzer - Analyze and enrich workout data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --update-exercises
  python main.py --update-exercise "Становая тяга"
  python main.py --analyze-workout 2026-02-11
  python main.py --analyze-latest
  python main.py --reanalyze-all
  python main.py --status
        """
    )
    
    parser.add_argument(
        '--update-exercises',
        action='store_true',
        help='Update all exercises with empty fields'
    )

    parser.add_argument(
        '--enrich',
        action='store_true',
        help='Alias for --update-exercises (enrich exercise data)'
    )
    
    parser.add_argument(
        '--update-exercise',
        type=str,
        metavar='NAME',
        help='Update a specific exercise by name'
    )
    
    parser.add_argument(
        '--analyze-workout',
        type=str,
        metavar='DATE',
        help='Analyze a workout by date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--analyze-latest',
        action='store_true',
        help='Analyze the latest workout'
    )
    
    parser.add_argument(
        '--reanalyze-all',
        action='store_true',
        help='Reanalyze all workouts'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Show help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    # Load configuration
    config_path = args.config
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return 1
    
    try:
        config = load_config(config_path)
        print(f"✅ Config loaded from {config_path}")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return 1
    
    # Execute requested action
    if args.update_exercises or args.enrich:
        print("\n🔄 Updating all exercises...\n")
        update_all_exercises(config)
    
    elif args.update_exercise:
        print(f"\n🔄 Updating exercise: {args.update_exercise}\n")
        update_single_exercise(args.update_exercise, config)
    
    elif args.analyze_workout:
        print(f"\n📊 Analyzing workout: {args.analyze_workout}\n")
        analyze_workout(args.analyze_workout, config)
    
    elif args.analyze_latest:
        print("\n📊 Analyzing latest workout...\n")
        analyze_latest_workout(config)
    
    elif args.reanalyze_all:
        print("\n🔄 Reanalyzing all workouts...\n")
        reanalyze_all_workouts(config)
    
    elif args.status:
        show_status(config)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

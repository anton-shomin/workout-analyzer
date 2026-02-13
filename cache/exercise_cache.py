"""
Exercise cache module for workout analyzer.

Provides caching functionality for exercise data with priority:
1. Local exercise files (Exercises/ folder)
2. Cache files (.cache/exercises/)
3. Perplexity API
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from utils.helpers import sanitize_filename, ensure_dir_exists
from parsers.exercise_parser import parse_exercise_file, needs_enrichment
from ai.perplexity_client import PerplexityClient


def get_cache_path(name: str, cache_dir: str) -> str:
    """
    Generate a cache file path from exercise name.
    
    Args:
        name: Exercise name.
        cache_dir: Directory for cache files.
        
    Returns:
        Full path to the cache file.
    """
    safe_name = sanitize_filename(name)
    return os.path.join(cache_dir, f"{safe_name}.json")


def load_from_cache(cache_file: str) -> Optional[dict]:
    """
    Load exercise data from a JSON cache file.
    
    Args:
        cache_file: Path to the cache file.
        
    Returns:
        Exercise data dictionary or None if not found/invalid.
    """
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = ['name', 'equipment', 'met_base', 'cal_per_rep', 'muscle_groups']
        if not all(field in data for field in required_fields):
            return None
        
        data['source'] = data.get('source', 'cache')
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading cache file {cache_file}: {e}")
        return None


def save_to_cache(cache_file: str, data: dict) -> bool:
    """
    Save exercise data to a JSON cache file.
    
    Args:
        cache_file: Path to the cache file.
        data: Exercise data dictionary.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Ensure directory exists
        ensure_dir_exists(os.path.dirname(cache_file))
        
        # Add timestamp
        cache_data = {
            **data,
            'source': data.get('source', 'perplexity'),
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        return True
    except IOError as e:
        print(f"Error saving cache file {cache_file}: {e}")
        return False


def find_local_exercise(name: str, equipment: str, exercises_folder: str) -> Optional[str]:
    """
    Find an exercise file in the local Exercises folder.
    
    Args:
        name: Exercise name.
        equipment: Equipment used.
        exercises_folder: Path to the Exercises folder.
        
    Returns:
        Path to the exercise file or None if not found.
    """
    if not os.path.exists(exercises_folder):
        return None
    
    # Search for matching file
    for filename in os.listdir(exercises_folder):
        if not filename.endswith('.md'):
            continue
        
        filepath = os.path.join(exercises_folder, filename)
        try:
            exercise_data = parse_exercise_file(filepath)

            # Match by frontmatter 'name' field
            ex_name = exercise_data.get('name', '')

            # Fallback: derive name from filename
            if not ex_name:
                ex_name = (
                    os.path.splitext(filename)[0]
                    .replace('_', ' ')
                )

            # Check if name matches (case-insensitive)
            if ex_name.lower() == name.lower():
                # Optionally check equipment match
                if equipment and exercise_data.get('equipment'):
                    if (equipment.lower()
                            not in exercise_data['equipment'].lower()):
                        continue

                return filepath
        except Exception:
            continue

    return None


def get_exercise_data(
    name: str,
    equipment: str,
    vault_path: str,
    cache_dir: str,
    exercises_folder: str = None,
    force_refresh: bool = False
) -> dict:
    """
    Get exercise data with caching priority:
    1. Local exercise files (if exercises_folder provided)
    2. Cache files
    3. Perplexity API
    
    Args:
        name: Exercise name.
        equipment: Equipment used.
        vault_path: Path to Obsidian vault.
        cache_dir: Directory for cache files.
        exercises_folder: Optional folder with local exercise files.
        force_refresh: If True, skip cache and fetch fresh data.
        
    Returns:
        Dictionary containing:
        - name: str
        - equipment: str
        - met_base: float
        - cal_per_rep: float
        - muscle_groups: list[str]
        - source: str ("local", "cache", "perplexity")
    """
    # 1. Check local exercise files first (highest priority)
    if exercises_folder and not force_refresh:
        local_path = find_local_exercise(name, equipment, exercises_folder)
        if local_path:
            try:
                exercise_data = parse_exercise_file(local_path)
                
                # Check if local file has enriched data
                if not needs_enrichment(exercise_data):
                    return {
                        'name': exercise_data['name'],
                        'equipment': exercise_data['equipment'],
                        'met_base': exercise_data['met_base'],
                        'cal_per_rep': exercise_data['cal_per_rep'],
                        'muscle_groups': exercise_data['muscle_groups'],
                        'source': 'local',
                        'description': exercise_data.get('description', '')
                    }
            except Exception as e:
                print(f"Error reading local exercise {local_path}: {e}")
    
    # 2. Check cache files
    if not force_refresh:
        cache_file = get_cache_path(name, cache_dir)
        cached_data = load_from_cache(cache_file)
        if cached_data:
            # Verify equipment match if specified
            if equipment and cached_data.get('equipment'):
                if equipment.lower() in cached_data['equipment'].lower() or \
                   cached_data['equipment'].lower() in equipment.lower():
                    return cached_data
            else:
                return cached_data
    
    # 3. Fetch from Perplexity API
    try:
        client = PerplexityClient()
        api_data = client.search_exercise_data(name, equipment)
        
        result = {
            'name': name,
            'equipment': equipment,
            'met_base': api_data.get('met_base'),
            'cal_per_rep': api_data.get('cal_per_rep'),
            'muscle_groups': api_data.get('muscle_groups', []),
            'source': 'perplexity',
            'reasoning': api_data.get('reasoning', '')
        }
        
        # Apply defaults if API returned None values
        if result['met_base'] is None:
            result['met_base'] = 8.0  # Default MET for kettlebell exercises
        
        # Save to cache
        cache_file = get_cache_path(name, cache_dir)
        save_to_cache(cache_file, result)
        
        return result
        
    except Exception as e:
        print(f"Error fetching from Perplexity API: {e}")
        
        # Return fallback data
        return {
            'name': name,
            'equipment': equipment,
            'met_base': 8.0,  # Default MET
            'cal_per_rep': 0.0,
            'muscle_groups': [],
            'source': 'fallback',
            'reasoning': f"API error: {str(e)}"
        }


def clear_cache(cache_dir: str, older_than_days: int = None) -> int:
    """
    Clear cache files.
    
    Args:
        cache_dir: Directory containing cache files.
        older_than_days: If specified, only clear files older than this many days.
        
    Returns:
        Number of files deleted.
    """
    if not os.path.exists(cache_dir):
        return 0
    
    deleted_count = 0
    cutoff_time = None
    
    if older_than_days:
        cutoff_time = datetime.now(timezone.utc).timestamp() - (older_than_days * 86400)
    
    for filename in os.listdir(cache_dir):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(cache_dir, filename)
        
        if cutoff_time:
            file_time = os.path.getmtime(filepath)
            if file_time < cutoff_time:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except OSError:
                    continue
        else:
            try:
                os.remove(filepath)
                deleted_count += 1
            except OSError:
                continue
    
    return deleted_count


def get_cache_stats(cache_dir: str) -> dict:
    """
    Get statistics about the cache.
    
    Args:
        cache_dir: Directory containing cache files.
        
    Returns:
        Dictionary with cache statistics.
    """
    if not os.path.exists(cache_dir):
        return {'total_files': 0, 'total_size_bytes': 0, 'oldest_file': None, 'newest_file': None}
    
    files = []
    total_size = 0
    
    for filename in os.listdir(cache_dir):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(cache_dir, filename)
        try:
            file_stats = os.stat(filepath)
            files.append({
                'name': filename,
                'size': file_stats.st_size,
                'mtime': datetime.fromtimestamp(file_stats.st_mtime, tz=timezone.utc).isoformat()
            })
            total_size += file_stats.st_size
        except OSError:
            continue
    
    if not files:
        return {'total_files': 0, 'total_size_bytes': 0, 'oldest_file': None, 'newest_file': None}
    
    files_sorted = sorted(files, key=lambda x: x['mtime'])
    
    return {
        'total_files': len(files),
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / 1024 / 1024, 2),
        'oldest_file': files_sorted[0]['mtime'],
        'newest_file': files_sorted[-1]['mtime']
    }

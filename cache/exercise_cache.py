"""
Exercise cache with ROBUST name matching
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from utils.helpers import sanitize_filename, ensure_dir_exists
from parsers.exercise_parser import parse_exercise_file, needs_enrichment
from ai.perplexity_client import PerplexityClient


def normalize_exercise_name(name: str) -> str:
    """
    ROBUST name normalization for matching.

    Examples:
        "Злой поток" → "злой поток"
        "злой_поток" → "злой поток"
        "Злой-Поток" → "злой поток"
        "ЗЛОЙ_ПОТОК" → "злой поток"
    """
    name = name.lower().strip()
    # Replace underscores and hyphens with spaces
    name = name.replace('_', ' ').replace('-', ' ')
    # Remove extra spaces
    name = ' '.join(name.split())
    return name


def find_local_exercise(name: str, equipment: str, exercises_folder: str) -> Optional[str]:
    """
    Find exercise file with ROBUST name matching.

    IMPROVED: Uses normalize_exercise_name() for bulletproof matching.
    """
    if not os.path.exists(exercises_folder):
        return None

    # Normalize search name
    search_name = normalize_exercise_name(name)

    print(f"   🔍 Searching for: '{name}' (normalized: '{search_name}')")

    # Try 1: Exact filename match (fast path)
    safe_filename = sanitize_filename(name) + '.md'
    direct_path = os.path.join(exercises_folder, safe_filename)
    if os.path.exists(direct_path):
        print(f"   ✅ Found by filename: {safe_filename}")
        return direct_path

    # Try 2: Search all files and compare frontmatter names
    for filename in os.listdir(exercises_folder):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(exercises_folder, filename)
        try:
            exercise_data = parse_exercise_file(filepath)

            # Get name from frontmatter
            ex_name = exercise_data.get('name', '')

            # Fallback: derive from filename
            if not ex_name:
                ex_name = os.path.splitext(filename)[0].replace('_', ' ')

            # Normalize and compare
            ex_name_normalized = normalize_exercise_name(ex_name)

            if ex_name_normalized == search_name:
                print(f"   ✅ Found by frontmatter: {filename}")
                print(
                    f"      Frontmatter name: '{ex_name}' → normalized: '{ex_name_normalized}'")
                return filepath

        except Exception as e:
            print(f"   ⚠️  Error reading {filename}: {e}")
            continue

    print(f"   ❌ Not found in {exercises_folder}")
    return None


def get_cache_path(name: str, cache_dir: str) -> str:
    """Generate cache file path."""
    safe_name = sanitize_filename(name)
    return os.path.join(cache_dir, f"{safe_name}.json")


def load_from_cache(cache_file: str) -> Optional[dict]:
    """Load from cache (unchanged)."""
    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        required_fields = ['name', 'equipment',
                           'met_base', 'cal_per_rep', 'muscle_groups']
        if not all(field in data for field in required_fields):
            return None

        data['source'] = data.get('source', 'cache')
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading cache file {cache_file}: {e}")
        return None


def save_to_cache(cache_file: str, data: dict) -> bool:
    """Save to cache (unchanged)."""
    try:
        ensure_dir_exists(os.path.dirname(cache_file))

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


def get_exercise_data(
    name: str,
    equipment: str,
    vault_path: str,
    cache_dir: str,
    exercises_folder: str = None,
    force_refresh: bool = False
) -> dict:
    """
    Get exercise data with ROBUST local file search.

    Priority:
    1. Local exercise files (with ROBUST name matching)
    2. Cache files
    3. Perplexity API
    """
    print(f"\n📝 Getting data for: {name}")

    # 1. Check local exercise files FIRST
    if exercises_folder and not force_refresh:
        local_path = find_local_exercise(name, equipment, exercises_folder)
        if local_path:
            try:
                exercise_data = parse_exercise_file(local_path)

                # Check if enriched
                if not needs_enrichment(exercise_data):
                    print(f"   ✅ Using LOCAL file (fully enriched)")
                    return {
                        'name': exercise_data['name'],
                        'equipment': exercise_data['equipment'],
                        'met_base': exercise_data['met_base'],
                        'cal_per_rep': exercise_data['cal_per_rep'],
                        'muscle_groups': exercise_data['muscle_groups'],
                        'components': exercise_data.get('components', []),
                        'complexity_multiplier': exercise_data.get('complexity_multiplier', 1),
                        'source': 'local',
                        'description': exercise_data.get('description', '')
                    }
                else:
                    print(f"   ⚠️  Found LOCAL file but needs enrichment")
            except Exception as e:
                print(f"   ❌ Error reading local file: {e}")

    # 2. Check cache
    if not force_refresh:
        cache_file = get_cache_path(name, cache_dir)
        cached_data = load_from_cache(cache_file)
        if cached_data:
            print(f"   ✅ Using CACHE")
            return cached_data

    # 3. Fetch from Perplexity
    print(f"   🌐 Fetching from PERPLEXITY API...")
    try:
        client = PerplexityClient()
        api_data = client.search_exercise_data(name, equipment)

        result = {
            'name': name,
            'equipment': equipment,
            'met_base': api_data.get('met_base'),
            'cal_per_rep': api_data.get('cal_per_rep'),
            'muscle_groups': api_data.get('muscle_groups', []),
            'components': [],
            'complexity_multiplier': 1,
            'source': 'perplexity',
            'reasoning': api_data.get('reasoning', '')
        }

        if result['met_base'] is None:
            result['met_base'] = 8.0

        # Save to cache
        cache_file = get_cache_path(name, cache_dir)
        save_to_cache(cache_file, result)

        print(
            f"   ✅ Got from Perplexity: MET={result['met_base']}, cal/rep={result['cal_per_rep']}")
        return result

    except Exception as e:
        print(f"   ❌ Perplexity error: {e}")

        # Fallback
        return {
            'name': name,
            'equipment': equipment,
            'met_base': 8.0,
            'cal_per_rep': 2.0,
            'muscle_groups': ['fullBody'],
            'components': [],
            'complexity_multiplier': 1,
            'source': 'fallback',
            'reasoning': f"API error: {str(e)}"
        }


def clear_cache(cache_dir: str, older_than_days: int = None) -> int:
    """Clear cache (unchanged)."""
    if not os.path.exists(cache_dir):
        return 0

    deleted_count = 0
    cutoff_time = None

    if older_than_days:
        cutoff_time = datetime.now(
            timezone.utc).timestamp() - (older_than_days * 86400)

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
    """Get cache stats (unchanged)."""
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

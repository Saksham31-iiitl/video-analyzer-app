"""
Simple file-based caching for analysis results.
Avoids re-processing the same video when iterating on reel settings.
"""

import hashlib
import json
import os
import logging
from typing import Any, Optional, Callable

from config import settings

logger = logging.getLogger("reel-generator.cache")


def get_cache_key(file_path: str, suffix: str = "") -> str:
    """
    Generate a cache key from file content hash + size.
    Reads only the first 8 KB for speed on large videos.
    """
    hasher = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            hasher.update(f.read(8192))
        file_size = os.path.getsize(file_path)
        return f"{hasher.hexdigest()}_{file_size}{('_' + suffix) if suffix else ''}"
    except Exception:
        return None


def get_cached(file_path: str, suffix: str = "") -> Optional[Any]:
    """Retrieve a cached result for a file, or None if not cached."""
    key = get_cache_key(file_path, suffix)
    if key is None:
        return None

    cache_path = os.path.join(settings.CACHE_DIR, f"{key}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                logger.debug(f"Cache hit: {key}")
                return json.load(f)
        except Exception:
            return None
    return None


def set_cached(file_path: str, data: Any, suffix: str = ""):
    """Store a result in the cache."""
    key = get_cache_key(file_path, suffix)
    if key is None:
        return

    os.makedirs(settings.CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(settings.CACHE_DIR, f"{key}.json")
    try:
        with open(cache_path, "w") as f:
            json.dump(data, f)
        logger.debug(f"Cached: {key}")
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")


def cached_analysis(file_path: str, analysis_fn: Callable, suffix: str = "") -> Any:
    """
    Run analysis_fn on a file, using cache if available.

    Args:
        file_path:    The file to analyse.
        analysis_fn:  Function that takes file_path and returns JSON-serialisable data.
        suffix:       Cache key suffix (e.g., "scenes", "scores").

    Returns:
        The analysis result (from cache or freshly computed).
    """
    cached = get_cached(file_path, suffix)
    if cached is not None:
        return cached

    result = analysis_fn(file_path)
    set_cached(file_path, result, suffix)
    return result


def clear_cache():
    """Remove all cached files."""
    cache_dir = settings.CACHE_DIR
    if os.path.isdir(cache_dir):
        for f in os.listdir(cache_dir):
            os.remove(os.path.join(cache_dir, f))
        logger.info("Cache cleared")

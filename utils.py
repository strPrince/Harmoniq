"""
Utility functions (caching, deduplication, etc.).
"""
from functools import lru_cache

@lru_cache(maxsize=128)
def map_genre(mood):
    # Map mood to genre
    return "pop"

def deduplicate_tracks(tracks):
    # Remove duplicate tracks based on title and artist combination
    seen = set()
    unique = []
    for track in tracks:
        # Create a unique identifier from title and artist
        track_key = f"{track.get('title', '')}-{track.get('artist', '')}"
        if track_key not in seen:
            unique.append(track)
            seen.add(track_key)
    return unique

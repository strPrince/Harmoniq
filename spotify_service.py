"""
Spotify API logic and helper functions.
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
import random

class SpotifyService:
    def __init__(self, client_id, client_secret):
        self.logger = logging.getLogger(__name__)
        if client_id and client_secret:
            try:
                auth_manager = SpotifyClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret
                )
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
                self.logger.info("Spotify client initialized successfully (service)")
            except Exception as e:
                self.sp = None
                self.logger.error(f"Failed to initialize Spotify client: {e}")
        else:
            self.sp = None
            self.logger.error("Spotify credentials not found.")

    def get_recommendations(self, user_mood_data):
        try:
            valence = float(user_mood_data.get('valence', 0.5))
            energy = float(user_mood_data.get('energy', 0.5))
            danceability = float(user_mood_data.get('danceability', 0.5))
            acousticness = float(user_mood_data.get('acousticness', 0.5))
            instrumentalness = float(user_mood_data.get('instrumentalness', 0.5))
            tempo = int(user_mood_data.get('tempo', 120))
            popularity = int(user_mood_data.get('popularity', 50))

            mood_mapping = {
                'happy': {
                    'genres': ['pop', 'dance', 'disco', 'reggae'],
                    'valence_boost': 0.2, 'energy_boost': 0.1
                },
                'sad': {
                    'genres': ['acoustic', 'blues', 'folk', 'indie'],
                    'valence_boost': -0.3, 'energy_boost': -0.2
                },
                'energetic': {
                    'genres': ['rock', 'electronic', 'punk', 'metal'],
                    'valence_boost': 0.1, 'energy_boost': 0.3
                },
                'calm': {
                    'genres': ['ambient', 'chill', 'classical'],
                    'valence_boost': 0.0, 'energy_boost': -0.3
                },
                'angry': {
                    'genres': ['metal', 'punk', 'rock'],
                    'valence_boost': -0.1, 'energy_boost': 0.3
                }
            }

            mood = user_mood_data.get('mood', 'happy')
            mood_config = mood_mapping.get(mood, mood_mapping['happy'])

            adjusted_valence = max(0.0, min(1.0, valence + mood_config.get('valence_boost', 0)))
            adjusted_energy = max(0.0, min(1.0, energy + mood_config.get('energy_boost', 0)))

            valence_range = {
                'min_valence': max(0.0, adjusted_valence - 0.2),
                'max_valence': min(1.0, adjusted_valence + 0.2),
                'target_valence': adjusted_valence
            }
            energy_range = {
                'min_energy': max(0.0, adjusted_energy - 0.2),
                'max_energy': min(1.0, adjusted_energy + 0.2),
                'target_energy': adjusted_energy
            }
            danceability_range = {
                'min_danceability': max(0.0, danceability - 0.2),
                'max_danceability': min(1.0, danceability + 0.2),
                'target_danceability': danceability
            }
            acousticness_range = {
                'min_acousticness': max(0.0, acousticness - 0.2),
                'max_acousticness': min(1.0, acousticness + 0.2),
                'target_acousticness': acousticness
            }
            instrumentalness_range = {
                'min_instrumentalness': max(0.0, instrumentalness - 0.2),
                'max_instrumentalness': min(1.0, instrumentalness + 0.2),
                'target_instrumentalness': instrumentalness
            }
            popularity_range = {
                'min_popularity': max(0, popularity - 20),
                'max_popularity': min(100, popularity + 20),
                'target_popularity': popularity
            }

            selected_genres = random.sample(mood_config['genres'], min(2, len(mood_config['genres'])))

            recommended_songs = []
            seen_ids = set()

            if self.sp:
                # Try a simplified recommendations call first
                try:
                    # Use only basic parameters to avoid 404 errors
                    recommendations = self.sp.recommendations(
                        seed_genres=selected_genres[:1],  # Use only 1 genre to be safe
                        limit=10,
                        target_valence=adjusted_valence,
                        target_energy=adjusted_energy,
                        target_popularity=popularity
                    )
                    tracks = recommendations.get('tracks', [])
                    if tracks:
                        self.logger.info(f"Spotify Recommendations API returned {len(tracks)} tracks")
                        for track in tracks:
                            track_id = track.get('id')
                            if not track_id:
                                self.logger.warning(f"Track missing 'id': {track}")
                                continue
                            if track_id not in seen_ids:
                                seen_ids.add(track_id)
                                song = {
                                    "title": track.get('name', 'Unknown'),
                                    "artist": track['artists'][0]['name'] if track.get('artists') else 'Unknown',
                                    "spotify_url": track.get('external_urls', {}).get('spotify', '#'),
                                    "album_image": track.get('album', {}).get('images', [{}])[0].get('url', ''),
                                    "popularity": track.get('popularity', 0),
                                    "duration_ms": track.get('duration_ms', 0)
                                }
                                recommended_songs.append(song)
                    else:
                        self.logger.error(f"Spotify Recommendations API returned no tracks. Full response: {recommendations}")
                except Exception as e:
                    self.logger.error(f"Spotify Recommendations API error: {e}")
                    # Continue to search fallback instead of returning error immediately

                # Always use search as primary method since recommendations API is unreliable
                try:
                    search_queries = [
                        f"{mood} music",
                        f"{mood} songs",
                        mood,
                        selected_genres[0] if selected_genres else "pop"
                    ]
                    
                    if user_mood_data.get('context'):
                        search_queries.append(f"{user_mood_data.get('context')} music")
                    if user_mood_data.get('goal'):
                        search_queries.append(f"music for {user_mood_data.get('goal')}")
                    if user_mood_data.get('preferences'):
                        search_queries.append(user_mood_data.get('preferences'))
                    
                    # Remove duplicates and shuffle
                    search_queries = list(set(search_queries))
                    random.shuffle(search_queries)
                    search_queries = search_queries[:5]  # Limit searches
                    
                    self.logger.info(f"Using search queries: {search_queries}")
                    
                    for query in search_queries:
                        try:
                            results = self.sp.search(q=query, type='track', limit=15, market='US')
                            if results and 'tracks' in results and 'items' in results['tracks']:
                                tracks = results['tracks']['items']
                                self.logger.info(f"Search query '{query}' returned {len(tracks)} tracks")
                                
                                for track in tracks:
                                    if not track or not isinstance(track, dict):
                                        continue
                                    track_id = track.get('id')
                                    if not track_id:
                                        continue
                                    if track_id not in seen_ids and len(recommended_songs) < 15:
                                        seen_ids.add(track_id)
                                        artists = track.get('artists', [])
                                        artist_name = artists[0].get('name', 'Unknown') if artists else 'Unknown'
                                        
                                        album = track.get('album', {})
                                        images = album.get('images', [])
                                        album_image = images[0].get('url', '') if images else ''
                                        
                                        song = {
                                            "title": track.get('name', 'Unknown'),
                                            "artist": artist_name,
                                            "spotify_url": track.get('external_urls', {}).get('spotify', '#'),
                                            "album_image": album_image,
                                            "popularity": track.get('popularity', 0),
                                            "duration_ms": track.get('duration_ms', 0)
                                        }
                                        recommended_songs.append(song)
                            else:
                                self.logger.warning(f"Search query '{query}' returned no valid results")
                        except Exception as search_err:
                            self.logger.error(f"Search query '{query}' failed: {search_err}")
                            continue
                    
                    self.logger.info(f"Search collected {len(recommended_songs)} total songs")
                except Exception as search_error:
                    self.logger.error(f"Search enhancement failed: {search_error}")
                    return [], f"Search failed: {search_error}"

            random.shuffle(recommended_songs)
            return recommended_songs, None
        except Exception as e:
            self.logger.error(f"Error in get_recommendations: {e}")
            return [], str(e)

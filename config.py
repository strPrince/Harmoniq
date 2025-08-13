"""
Configuration management for Spotify credentials and environment settings.
"""

import os

class Config:
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "your_client_id")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "your_client_secret")
    VALID_GENRES = [
        "pop", "rock", "hip hop", "jazz", "classical", "electronic", "country", "blues", "reggae", "metal"
    ]
    # Add more config as needed

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

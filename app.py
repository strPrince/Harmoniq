from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
from config import Config
from spotify_service import SpotifyService
from validators import validate_request_json
from utils import deduplicate_tracks
from error_handlers import error_response
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Spotify service
spotify_service = SpotifyService(Config.SPOTIFY_CLIENT_ID, Config.SPOTIFY_CLIENT_SECRET)

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/debug-user-data', methods=['POST'])
def debug_user_data():
    """Debug endpoint to see exactly what data we're receiving"""
    user_data = request.json
    print("="*60)
    print("DEBUG: Raw user data received:")
    print(f"Data: {user_data}")
    print("="*60)
    return jsonify({"received_data": user_data}), 200

# @app.route('/test-spotify', methods=['GET'])
# def test_spotify():
#     """Test endpoint to check Spotify connection"""
#     if not sp:
#         return jsonify({"error": "Spotify client not initialized"}), 500
    
#     try:
#         # Try a simple search instead of recommendations
#         results = sp.search(q='track:happy', type='track', limit=5)
#         tracks = []
#         for track in results['tracks']['items']:
#             tracks.append({
#                 "name": track['name'],
#                 "artist": track['artists'][0]['name']
#             })
        
#         return jsonify({
#             "status": "success",
#             "message": "Spotify connection working",
#             "sample_tracks": tracks
#         }), 200
#     except Exception as e:
#         logger.error(f"Failed to connect to Spotify: {e}")
#         return jsonify({"error": str(e)}), 500

@app.route('/mood-recommendation', methods=['POST'])
@validate_request_json(['mood', 'valence', 'energy'])
def mood_recommendation():
    try:
        user_mood_data = request.get_json()
        recommendations, error = spotify_service.get_recommendations(user_mood_data)
        if error:
            return error_response(error, code=400)
        final_songs = deduplicate_tracks(recommendations)[:10]
        response = {
            "message": "Song recommendations generated!",
            "recommended_songs": final_songs
        }
        return jsonify(response), 200
    except ValueError as ve:
        logger.error(f"Value error: {ve}")
        return error_response("Invalid numerical value provided", code=400)
    except Exception as e:
        logger.error(f"A general error occurred in /mood-recommendation: {e}")
        return error_response("An internal server error occurred.", code=500)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
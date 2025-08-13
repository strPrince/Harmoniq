"""
Custom error handling and response formatting.
"""
from flask import jsonify

def error_response(message, code=400, details=None):
    response = {"error": message}
    if details:
        response["details"] = details
    return jsonify(response), code

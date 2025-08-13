"""
Request validation logic and decorators.
"""
from flask import request, jsonify
from functools import wraps

def validate_request_json(required_fields):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing JSON body"}), 400
            missing = [field for field in required_fields if field not in data]
            if missing:
                return jsonify({"error": "Missing fields", "fields": missing}), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator

"""
BetBudAI API Server (Production Flask + Lambda-compatible)
===========================================================
Modular REST API with separate route files for maintainability.
Runs locally on Flask or in Lambda via lambda_function.py wrapper.

Routes:
  /api/picks/today        - GET official picks for today
  /api/picks/yesterday    - GET results from yesterday
  /api/picks/featured     - GET featured meeting analysis
  /api/favs-run           - GET lay-the-fav racing data
  /api/results/today      - GET settled results with ROI
  /api/results/yesterday  - GET previous day results
  /api/auth/*             - Auth endpoints (login, register, verify)
  /api/admin/*            - Admin endpoints (requires auth)
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timezone

# Add backend directory to path for imports
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
_api_dir = os.path.dirname(os.path.abspath(__file__))
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

# Import modular routes
from routes import picks_routes, results_routes, auth_routes, admin_routes

# Configuration
ENV = os.environ.get('ENV', 'development')
API_VERSION = '2.0'
AWS_REGION = os.environ.get('AWS_REGION', 'eu-west-1')


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    from decimal import Decimal
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj


app = Flask(__name__)
CORS(app)

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['ENV'] = ENV


# ── Middleware ────────────────────────────────────────────────────────────────

@app.before_request
def log_request():
    """Log incoming requests."""
    print(f"[API] {request.method} {request.path} - {request.remote_addr}")


@app.after_request
def add_headers(response):
    """Add standard response headers."""
    response.headers['X-API-Version'] = API_VERSION
    response.headers['X-Request-Timestamp'] = datetime.now(timezone.utc).isoformat()
    return response


# ── Health Check ──────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'ok',
        'version': API_VERSION,
        'environment': ENV,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }), 200


# ── Register Routes ───────────────────────────────────────────────────────────

app.register_blueprint(picks_routes.bp)
app.register_blueprint(results_routes.bp)
app.register_blueprint(auth_routes.bp)
app.register_blueprint(admin_routes.bp)


# ── Error Handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Not Found',
        'message': f"The requested resource was not found",
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    print(f"[API ERROR] {error}")
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
    }), 500


# ── Run locally ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = ENV == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

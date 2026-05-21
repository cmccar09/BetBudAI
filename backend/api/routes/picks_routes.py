"""
Picks API Routes — delegates to lambda_function.py for production-identical logic.
All business logic lives in backend/api/lambda_function.py (ported from lambda_api_picks.py).
"""
from flask import Blueprint, jsonify, request, make_response
from datetime import datetime, timezone
import json

bp = Blueprint('picks', __name__, url_prefix='/api/picks')

# ── Lambda function bridge ─────────────────────────────────────────────────
try:
    from ..lambda_function import (
        get_today_picks,
        get_yesterday_picks,
        get_all_picks,
        get_punchestown_tomorrow_picks,
        decimal_to_float,
    )
    LAMBDA_AVAILABLE = True
except ImportError as e:
    LAMBDA_AVAILABLE = False
    print(f'[picks_routes] lambda_function import failed: {e}')

_CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-admin-token',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Content-Type': 'application/json',
}


def _flask_event(method=None, path=None):
    """Build a minimal Lambda-style event from the current Flask request."""
    return {
        'httpMethod': method or request.method,
        'rawPath': path or request.path,
        'path': path or request.path,
        'queryStringParameters': dict(request.args),
        'body': request.get_data(as_text=True) or None,
        'headers': dict(request.headers),
        'requestContext': {
            'http': {'method': method or request.method}
        },
    }


def _lambda_resp(result):
    """Convert a Lambda-style response dict to a Flask response."""
    status  = result.get('statusCode', 200)
    body    = result.get('body', '{}')
    resp_headers = result.get('headers', {})
    r = make_response(body, status)
    for k, v in resp_headers.items():
        r.headers[k] = v
    r.headers.setdefault('Content-Type', 'application/json')
    return r


@bp.route('/today', methods=['GET', 'OPTIONS'])
def picks_today():
    if request.method == 'OPTIONS':
        return make_response('', 200, _CORS_HEADERS)
    if LAMBDA_AVAILABLE:
        return _lambda_resp(get_today_picks(_CORS_HEADERS))
    return jsonify({'success': False, 'error': 'Lambda function not available'}), 500


@bp.route('/yesterday', methods=['GET', 'OPTIONS'])
def picks_yesterday():
    if request.method == 'OPTIONS':
        return make_response('', 200, _CORS_HEADERS)
    if LAMBDA_AVAILABLE:
        return _lambda_resp(get_yesterday_picks(_CORS_HEADERS))
    return jsonify({'success': False, 'error': 'Lambda function not available'}), 500


@bp.route('/featured-meeting', methods=['GET', 'OPTIONS'])
@bp.route('/featured', methods=['GET', 'OPTIONS'])
@bp.route('/punchestown-tomorrow', methods=['GET', 'OPTIONS'])
def picks_featured():
    if request.method == 'OPTIONS':
        return make_response('', 200, _CORS_HEADERS)
    if LAMBDA_AVAILABLE:
        return _lambda_resp(get_punchestown_tomorrow_picks(_CORS_HEADERS, _flask_event()))
    return jsonify({'success': False, 'error': 'Lambda function not available'}), 500


@bp.route('', methods=['GET', 'OPTIONS'])
@bp.route('/', methods=['GET', 'OPTIONS'])
def picks_all():
    if request.method == 'OPTIONS':
        return make_response('', 200, _CORS_HEADERS)
    if LAMBDA_AVAILABLE:
        return _lambda_resp(get_all_picks(_CORS_HEADERS))
    return jsonify({'success': False, 'error': 'Lambda function not available'}), 500

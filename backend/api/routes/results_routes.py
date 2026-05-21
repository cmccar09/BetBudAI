"""
Results API Routes - delegates to lambda_function.py for production logic.
"""
from flask import Blueprint, request, make_response, jsonify
import json

bp = Blueprint('results', __name__, url_prefix='/api/results')

try:
    from ..lambda_function import (
        get_latest_winner,
        get_cumulative_roi,
        export_roi_csv,
        check_yesterday_results,
        check_today_results,
        get_favs_run_lambda,
        get_major_race_analysis,
        run_major_race_analysis,
        apply_learning_lambda,
        auto_record_pending_results,
    )
    LAMBDA_AVAILABLE = True
except ImportError as e:
    LAMBDA_AVAILABLE = False
    print(f'[results_routes] lambda_function import failed: {e}')

_CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-admin-token',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Content-Type': 'application/json',
}


def _event():
    return {
        'httpMethod': request.method,
        'rawPath': request.path,
        'path': request.path,
        'queryStringParameters': dict(request.args),
        'body': request.get_data(as_text=True) or None,
        'headers': dict(request.headers),
        'requestContext': {'http': {'method': request.method}},
    }


def _wrap(result):
    status = result.get('statusCode', 200)
    body = result.get('body', '{}')
    r = make_response(body, status)
    for k, v in result.get('headers', {}).items():
        r.headers[k] = v
    r.headers.setdefault('Content-Type', 'application/json')
    return r


@bp.route('/latest-winner', methods=['GET', 'OPTIONS'])
def latest_winner():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(get_latest_winner(_CORS))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/cumulative-roi', methods=['GET', 'OPTIONS'])
def cumulative_roi():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(get_cumulative_roi(_CORS))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/export-csv', methods=['GET', 'OPTIONS'])
def export_csv():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(export_roi_csv(_CORS))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/yesterday', methods=['GET', 'OPTIONS'])
def results_yesterday():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(check_yesterday_results(_CORS))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/today', methods=['GET', 'OPTIONS'])
@bp.route('', methods=['GET', 'OPTIONS'])
@bp.route('/', methods=['GET', 'OPTIONS'])
def results_today():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(check_today_results(_CORS))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/auto-record', methods=['GET', 'POST', 'OPTIONS'])
def auto_record():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(auto_record_pending_results(_CORS))
    return jsonify({'success': False, 'error': 'unavailable'}), 500

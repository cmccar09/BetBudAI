"""
Admin API Routes - delegates to lambda_function.py.
"""
from flask import Blueprint, request, make_response, jsonify

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

try:
    from ..lambda_function import (
        admin_get_config,
        admin_save_config,
        admin_get_analytics,
        admin_get_agentic_gate,
        admin_save_agentic_gate,
        admin_get_subscribers,
        admin_update_subscriber_role,
        get_favs_run_lambda,
        get_major_race_analysis,
        run_major_race_analysis,
        apply_learning_lambda,
    )
    LAMBDA_AVAILABLE = True
except ImportError as e:
    LAMBDA_AVAILABLE = False
    print(f'[admin_routes] lambda_function import failed: {e}')

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


@bp.route('/config', methods=['GET', 'OPTIONS'])
def config_get():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(admin_get_config(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/config', methods=['POST'])
def config_save():
    if LAMBDA_AVAILABLE: return _wrap(admin_save_config(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/analytics', methods=['GET', 'OPTIONS'])
def analytics_get():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(admin_get_analytics(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/agentic-gate', methods=['GET', 'OPTIONS'])
def agentic_gate_get():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(admin_get_agentic_gate(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/agentic-gate', methods=['POST'])
def agentic_gate_save():
    if LAMBDA_AVAILABLE: return _wrap(admin_save_agentic_gate(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/subscribers', methods=['GET', 'OPTIONS'])
def subscribers():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(admin_get_subscribers(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/subscribers/role', methods=['POST', 'OPTIONS'])
def subscribers_role_update():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(admin_update_subscriber_role(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/favs-run', methods=['GET', 'OPTIONS'])
def favs_run():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(get_favs_run_lambda(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/major-race-analysis', methods=['GET', 'OPTIONS'])
def major_race_analysis_get():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(get_major_race_analysis(_CORS))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/major-race-analysis/run', methods=['POST', 'OPTIONS'])
def major_race_analysis_run():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(run_major_race_analysis(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/learning/apply', methods=['POST', 'OPTIONS'])
def learning_apply():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(apply_learning_lambda(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500

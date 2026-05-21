"""
Auth API Routes - delegates to lambda_function.py.
"""
from flask import Blueprint, request, make_response, jsonify

bp = Blueprint('auth', __name__, url_prefix='/api')

try:
    from ..lambda_function import (
        register_subscriber,
        login_subscriber,
        forgot_password,
        reset_password,
        verify_email_token,
        update_daily_email_preference,
        maybe_send_daily_picks_ready_email,
        create_checkout_session,
        handle_stripe_webhook,
        get_subscription_status,
        create_customer_portal,
        cancel_subscription,
    )
    LAMBDA_AVAILABLE = True
except ImportError as e:
    LAMBDA_AVAILABLE = False
    print(f'[auth_routes] lambda_function import failed: {e}')

_CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-admin-token,stripe-signature',
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


@bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(register_subscriber(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(login_subscriber(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/forgot-password', methods=['POST', 'OPTIONS'])
def forgot_password_route():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(forgot_password(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/reset-password', methods=['POST', 'OPTIONS'])
def reset_password_route():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(reset_password(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/verify-email', methods=['GET', 'OPTIONS'])
def verify_email():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(verify_email_token(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/daily-email-preference', methods=['POST', 'OPTIONS'])
def daily_email_preference():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(update_daily_email_preference(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/daily-picks-ready-email/send', methods=['POST', 'OPTIONS'])
def daily_picks_email():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(maybe_send_daily_picks_ready_email(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/create-checkout-session', methods=['POST', 'OPTIONS'])
def checkout_session():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(create_checkout_session(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/stripe-webhook', methods=['POST', 'OPTIONS'])
def stripe_webhook():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(handle_stripe_webhook(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/subscription-status', methods=['POST', 'OPTIONS'])
def subscription_status():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(get_subscription_status(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/customer-portal', methods=['POST', 'OPTIONS'])
def customer_portal():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(create_customer_portal(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500


@bp.route('/cancel-subscription', methods=['POST', 'OPTIONS'])
def cancel_subscription_route():
    if request.method == 'OPTIONS': return make_response('', 200, _CORS)
    if LAMBDA_AVAILABLE: return _wrap(cancel_subscription(_CORS, _event()))
    return jsonify({'success': False, 'error': 'unavailable'}), 500

"""
Endpoints API pour l'interaction mobile.
"""

from flask import Blueprint, request, jsonify, render_template
import os

mobile_bp = Blueprint('mobile_api', __name__, url_prefix='/mobile/api')

@mobile_bp.route('/status', methods=['GET'])
def mobile_status():
    """Vérifie le status de l'API mobile."""
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'endpoints': [
            '/mobile/api/status',
            '/mobile/api/session/create',
            '/mobile/api/session/<session_id>',
            '/mobile/api/sync/position'
        ]
    })

@mobile_bp.route('/session/create', methods=['POST'])
def create_session_endpoint():
    """Crée une nouvelle session mobile."""
    data = request.json or {}
    user_id = data.get('user_id', 'anonymous')
    device_info = data.get('device_info', {})
    
    # Cette logique sera gérée par le sync_manager dans app.py
    return jsonify({
        'success': True,
        'message': 'Use POST /mobile/create-session instead'
    })

@mobile_bp.route('/session/<session_id>', methods=['GET'])
def get_session_endpoint(session_id):
    """Récupère les informations d'une session."""
    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': 'Session info'
    })

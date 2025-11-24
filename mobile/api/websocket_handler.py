"""
Gestionnaire WebSocket pour les interactions en temps réel.
"""

from flask_socketio import emit, join_room, leave_room
from datetime import datetime

def register_websocket_handlers(socketio):
    """
    Enregistre tous les gestionnaires WebSocket.
    
    Args:
        socketio: Instance Flask-SocketIO
    """
    
    @socketio.on('mobile_connect')
    def handle_mobile_connect(data):
        """Gère la connexion d'un appareil mobile."""
        session_id = data.get('session_id')
        device_type = data.get('device_type', 'unknown')
        
        if session_id:
            join_room(f'mobile_{session_id}')
            emit('mobile_connected', {
                'session_id': session_id,
                'device_type': device_type,
                'timestamp': datetime.now().isoformat()
            })
    
    @socketio.on('mobile_disconnect')
    def handle_mobile_disconnect(data):
        """Gère la déconnexion d'un appareil mobile."""
        session_id = data.get('session_id')
        
        if session_id:
            leave_room(f'mobile_{session_id}')
            emit('mobile_disconnected', {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
    
    @socketio.on('sync_request')
    def handle_sync_request(data):
        """Gère les demandes de synchronisation."""
        session_id = data.get('session_id')
        sync_type = data.get('type', 'audio')
        
        emit('sync_response', {
            'session_id': session_id,
            'type': sync_type,
            'timestamp': datetime.now().isoformat()
        }, room=f'mobile_{session_id}')

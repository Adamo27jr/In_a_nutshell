/**
 * Client WebSocket pour la communication en temps réel
 */

class WebSocketClient {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.socket = null;
        this.handlers = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.connect();
    }
    
    connect() {
        // Connexion Socket.IO
        this.socket = io({
            transports: ['websocket', 'polling']
        });
        
        this.socket.on('connect', () => {
            console.log('✅ WebSocket connecté');
            this.reconnectAttempts = 0;
            
            // Rejoindre la session
            this.socket.emit('join_session', {
                session_id: this.sessionId
            });
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ WebSocket déconnecté');
            this.attemptReconnect();
        });
        
        this.socket.on('session_joined', (data) => {
            console.log('📱 Session rejointe:', data);
        });
        
        this.socket.on('audio_sync', (data) => {
            this.trigger('audio_sync', data);
        });
        
        this.socket.on('quiz_result', (data) => {
            this.trigger('quiz_result', data);
        });
        
        this.socket.on('user_joined', (data) => {
            console.log('👤 Utilisateur rejoint:', data);
        });
        
        this.socket.on('user_left', (data) => {
            console.log('👤 Utilisateur parti:', data);
        });
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
            
            setTimeout(() => {
                this.connect();
            }, 2000 * this.reconnectAttempts);
        } else {
            console.error('❌ Impossible de se reconnecter');
        }
    }
    
    send(data) {
        if (this.socket && this.socket.connected) {
            this.socket.emit(data.type, data);
        } else {
            console.warn('⚠️  WebSocket non connecté');
        }
    }
    
    on(event, handler) {
        this.handlers[event] = handler;
    }
    
    trigger(event, data) {
        if (this.handlers[event]) {
            this.handlers[event](data);
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.emit('leave_session', {
                session_id: this.sessionId
            });
            this.socket.disconnect();
        }
    }
}

// Initialisation globale
document.addEventListener('DOMContentLoaded', () => {
    const sessionId = new URLSearchParams(window.location.search).get('session') || 'default';
    window.wsClient = new WebSocketClient(sessionId);
});

// Déconnexion lors de la fermeture de la page
window.addEventListener('beforeunload', () => {
    if (window.wsClient) {
        window.wsClient.disconnect();
    }
});

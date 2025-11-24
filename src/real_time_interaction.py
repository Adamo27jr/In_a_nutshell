import asyncio
import json
from typing import Dict, Set, Callable, Any
from datetime import datetime

class RealTimeInteractionManager:
    """Gère les interactions en temps réel entre web et mobile."""
    
    def __init__(self):
        """Initialise le gestionnaire d'interactions."""
        self.connections: Dict[str, Set] = {}  # session_id -> set of websocket connections
        self.event_handlers: Dict[str, Callable] = {}
        
    async def register_connection(self, session_id: str, websocket):
        """
        Enregistre une nouvelle connexion WebSocket.
        
        Args:
            session_id: Identifiant de la session
            websocket: Connexion WebSocket
        """
        if session_id not in self.connections:
            self.connections[session_id] = set()
        
        self.connections[session_id].add(websocket)
        
        # Envoyer confirmation
        await websocket.send(json.dumps({
            'type': 'connection_established',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }))
        
        print(f"Connexion WebSocket enregistrée (session: {session_id[:8]}...)")
    
    async def unregister_connection(self, session_id: str, websocket):
        """Désenregistre une connexion WebSocket."""
        if session_id in self.connections:
            self.connections[session_id].discard(websocket)
            if not self.connections[session_id]:
                del self.connections[session_id]
        
        print(f"Connexion WebSocket fermée (session: {session_id[:8]}...)")
    
    async def broadcast_to_session(self, session_id: str, message: Dict):
        """
        Diffuse un message à tous les appareils d'une session.
        
        Args:
            session_id: Identifiant de la session
            message: Message à diffuser
        """
        if session_id not in self.connections:
            return
        
        message_json = json.dumps(message)
        
        # Envoyer à toutes les connexions de la session
        dead_connections = set()
        for websocket in self.connections[session_id]:
            try:
                await websocket.send(message_json)
            except Exception as e:
                print(f"Erreur envoi message : {e}")
                dead_connections.add(websocket)
        
        # Nettoyer les connexions mortes
        self.connections[session_id] -= dead_connections
    
    async def send_quiz_question(
        self,
        session_id: str,
        question_data: Dict
    ):
        """
        Envoie une question de quiz aux appareils mobiles.
        
        Args:
            session_id: Identifiant de la session
            question_data: Données de la question
        """
        message = {
            'type': 'quiz_question',
            'data': question_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast_to_session(session_id, message)
        print(f"Question de quiz envoyée (session: {session_id[:8]}...)")
    
    async def sync_audio_playback(
        self,
        session_id: str,
        action: str,
        position: int = 0
    ):
        """
        Synchronise la lecture audio entre appareils.
        
        Args:
            session_id: Identifiant de la session
            action: Action (play, pause, seek)
            position: Position en secondes
        """
        message = {
            'type': 'audio_control',
            'action': action,
            'position': position,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast_to_session(session_id, message)
        print(f"Contrôle audio synchronisé : {action} @ {position}s (session: {session_id[:8]}...)")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """
        Enregistre un gestionnaire d'événements personnalisé.
        
        Args:
            event_type: Type d'événement
            handler: Fonction de gestion
        """
        self.event_handlers[event_type] = handler
        print(f"Handler enregistré pour : {event_type}")
    
    async def handle_client_message(
        self,
        session_id: str,
        message: Dict
    ):
        """
        Traite un message reçu d'un client.
        
        Args:
            session_id: Identifiant de la session
            message: Message reçu
        """
        event_type = message.get('type')
        
        if event_type in self.event_handlers:
            await self.event_handlers[event_type](session_id, message)
        else:
            print(f"Type d'événement non géré : {event_type}")
    
    def get_active_connections_count(self, session_id: Optional[str] = None) -> int:
        """
        Compte le nombre de connexions actives.
        
        Args:
            session_id: Session spécifique (optionnel)
            
        Returns:
            Nombre de connexions
        """
        if session_id:
            return len(self.connections.get(session_id, set()))
        else:
            return sum(len(conns) for conns in self.connections.values())

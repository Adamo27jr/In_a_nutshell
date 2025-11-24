import json
from typing import Dict, List, Optional
from datetime import datetime
import uuid

class MobileSyncManager:
    """Gère la synchronisation en temps réel avec les appareils mobiles."""
    
    def __init__(self, database_path: str):
        """
        Initialise le gestionnaire de synchronisation mobile.
        
        Args:
            database_path: Chemin vers la base de données SQLite
        """
        self.db_path = database_path
        self.active_sessions = {}
        self.sync_queue = []
        
    def create_session(self, user_id: str, device_info: Dict) -> str:
        """
        Crée une nouvelle session pour un appareil mobile.
        
        Args:
            user_id: Identifiant de l'utilisateur
            device_info: Informations sur l'appareil (type, OS, etc.)
            
        Returns:
            session_id: Identifiant unique de la session
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'device_type': device_info.get('type', 'unknown'),
            'device_os': device_info.get('os', 'unknown'),
            'started_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            'current_chapter': None,
            'current_doc_id': None,
            'audio_position': 0,
            'quiz_active': False,
            'is_active': True
        }
        
        self.active_sessions[session_id] = session_data
        
        print(f"📱 Session créée : {session_id} pour {user_id}")
        
        return session_id
    
    def sync_audio_position(self, session_id: str, position_seconds: int):
        """
        Synchronise la position de lecture audio entre appareils.
        
        Args:
            session_id: Identifiant de la session
            position_seconds: Position actuelle en secondes
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['audio_position'] = position_seconds
            self.active_sessions[session_id]['last_active'] = datetime.now().isoformat()
            
            # Ajouter à la file de synchronisation
            self.sync_queue.append({
                'type': 'audio_sync',
                'session_id': session_id,
                'position': position_seconds,
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"🎵 Position audio synchronisée : {position_seconds}s (session: {session_id[:8]}...)")
    
    def get_session_state(self, session_id: str) -> Optional[Dict]:
        """
        Récupère l'état actuel d'une session.
        
        Args:
            session_id: Identifiant de la session
            
        Returns:
            État de la session ou None si inexistante
        """
        return self.active_sessions.get(session_id)
    
    def update_current_document(self, session_id: str, doc_id: str, doc_title: str):
        """
        Met à jour le document en cours de lecture.
        
        Args:
            session_id: Identifiant de la session
            doc_id: Identifiant du document
            doc_title: Titre du document
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['current_doc_id'] = doc_id
            self.active_sessions[session_id]['current_doc_title'] = doc_title
            self.active_sessions[session_id]['last_active'] = datetime.now().isoformat()
            
            print(f"📖 Document actuel : {doc_title} (session: {session_id[:8]}...)")
    
    def update_quiz_state(self, session_id: str, quiz_data: Dict):
        """
        Met à jour l'état du quiz pour une session.
        
        Args:
            session_id: Identifiant de la session
            quiz_data: Données du quiz (question actuelle, score, etc.)
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['quiz_active'] = True
            self.active_sessions[session_id]['current_quiz'] = quiz_data
            self.active_sessions[session_id]['last_active'] = datetime.now().isoformat()
            
            print(f"📝 Quiz actif (session: {session_id[:8]}...)")
    
    def close_session(self, session_id: str):
        """Ferme une session mobile."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['is_active'] = False
            self.active_sessions[session_id]['ended_at'] = datetime.now().isoformat()
            
            print(f"❌ Session fermée : {session_id[:8]}...")
    
    def get_active_sessions(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        Récupère toutes les sessions actives.
        
        Args:
            user_id: Filtrer par utilisateur (optionnel)
            
        Returns:
            Liste des sessions actives
        """
        sessions = [
            session for session in self.active_sessions.values()
            if session.get('is_active', True)
        ]
        
        if user_id:
            sessions = [s for s in sessions if s['user_id'] == user_id]
        
        return sessions
    
    def cleanup_inactive_sessions(self, timeout_minutes: int = 60):
        """
        Nettoie les sessions inactives depuis plus de timeout_minutes.
        
        Args:
            timeout_minutes: Délai d'inactivité en minutes
        """
        from datetime import timedelta
        
        now = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.active_sessions.items():
            last_active = datetime.fromisoformat(session['last_active'])
            
            if (now - last_active) > timedelta(minutes=timeout_minutes):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.close_session(session_id)
            del self.active_sessions[session_id]
        
        if sessions_to_remove:
            print(f"🧹 {len(sessions_to_remove)} sessions inactives nettoyées")

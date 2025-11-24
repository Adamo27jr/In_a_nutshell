/**
 * Lecteur audio mobile avec synchronisation en temps réel
 */

class MobilePlayer {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.audio = document.getElementById('audio-element');
        this.playPauseBtn = document.getElementById('btn-play-pause');
        this.progressFill = document.getElementById('progress-fill');
        this.currentTimeEl = document.getElementById('current-time');
        this.totalTimeEl = document.getElementById('total-time');
        
        this.isPlaying = false;
        this.lastSyncTime = 0;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
    }
    
    setupEventListeners() {
        // Bouton Play/Pause
        this.playPauseBtn.addEventListener('click', () => this.togglePlayPause());
        
        // Boutons de navigation
        document.getElementById('btn-backward').addEventListener('click', () => {
            this.seek(-10);
        });
        
        document.getElementById('btn-forward').addEventListener('click', () => {
            this.seek(10);
        });
        
        // Mise à jour de la progression
        this.audio.addEventListener('timeupdate', () => {
            this.updateProgress();
            this.syncPosition();
        });
        
        // Métadonnées chargées
        this.audio.addEventListener('loadedmetadata', () => {
            this.totalTimeEl.textContent = this.formatTime(this.audio.duration);
        });
        
        // Fin de lecture
        this.audio.addEventListener('ended', () => {
            this.isPlaying = false;
            this.playPauseBtn.textContent = '▶️ Play';
        });
    }
    
    togglePlayPause() {
        if (this.audio.paused) {
            this.play();
        } else {
            this.pause();
        }
    }
    
    play() {
        this.audio.play();
        this.isPlaying = true;
        this.playPauseBtn.textContent = '⏸️ Pause';
        
        // Notifier les autres appareils
        if (window.wsClient) {
            window.wsClient.send({
                type: 'audio_control',
                session_id: this.sessionId,
                action: 'play',
                position: this.audio.currentTime
            });
        }
    }
    
    pause() {
        this.audio.pause();
        this.isPlaying = false;
        this.playPauseBtn.textContent = '▶️ Play';
        
        // Notifier les autres appareils
        if (window.wsClient) {
            window.wsClient.send({
                type: 'audio_control',
                session_id: this.sessionId,
                action: 'pause',
                position: this.audio.currentTime
            });
        }
    }
    
    seek(seconds) {
        const newTime = Math.max(0, Math.min(this.audio.duration, this.audio.currentTime + seconds));
        this.audio.currentTime = newTime;
        
        // Notifier les autres appareils
        if (window.wsClient) {
            window.wsClient.send({
                type: 'audio_control',
                session_id: this.sessionId,
                action: 'seek',
                position: newTime
            });
        }
    }
    
    updateProgress() {
        const progress = (this.audio.currentTime / this.audio.duration) * 100;
        this.progressFill.style.width = `${progress}%`;
        this.currentTimeEl.textContent = this.formatTime(this.audio.currentTime);
    }
    
    syncPosition() {
        // Synchroniser toutes les 5 secondes
        const now = Date.now();
        if (now - this.lastSyncTime > 5000) {
            this.lastSyncTime = now;
            
            fetch('/mobile/sync-position', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    position: Math.floor(this.audio.currentTime)
                })
            }).catch(err => console.error('Sync error:', err));
        }
    }
    
    connectWebSocket() {
        // Connexion WebSocket gérée par websocket_client.js
        if (window.wsClient) {
            window.wsClient.on('audio_sync', (data) => {
                this.handleRemoteControl(data);
            });
        }
    }
    
    handleRemoteControl(data) {
        const syncDot = document.getElementById('sync-indicator');
        syncDot.classList.add('syncing');
        setTimeout(() => syncDot.classList.remove('syncing'), 500);
        
        switch (data.action) {
            case 'play':
                if (this.audio.paused) {
                    this.audio.currentTime = data.position;
                    this.audio.play();
                    this.isPlaying = true;
                    this.playPauseBtn.textContent = '⏸️ Pause';
                }
                break;
                
            case 'pause':
                if (!this.audio.paused) {
                    this.audio.pause();
                    this.isPlaying = false;
                    this.playPauseBtn.textContent = '▶️ Play';
                }
                break;
                
            case 'seek':
                this.audio.currentTime = data.position;
                break;
        }
    }
    
    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    loadAudio(audioUrl, title) {
        document.getElementById('chapter-title').textContent = title;
        document.getElementById('audio-source').src = audioUrl;
        this.audio.load();
    }
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    const sessionId = new URLSearchParams(window.location.search).get('session') || 'default';
    window.mobilePlayer = new MobilePlayer(sessionId);
});

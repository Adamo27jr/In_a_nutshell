from gtts import gTTS
from pydub import AudioSegment
import os
import tempfile
from typing import Dict
from datetime import datetime


class AudioGenerator:
    """Génère l'audio final du podcast"""
    
    def __init__(self, voice_config: Dict = None):
        """
        Initialise le générateur audio
        
        Args:
            voice_config: Configuration de la voix (langue, vitesse)
        """
        self.voice_config = voice_config or {
            'lang': 'fr',
            'slow': False,
            'tld': 'fr'  # Accent français
        }
    
    def generate_podcast(
        self, 
        script: Dict,
        include_music: bool = False
    ) -> str:
        """
        Génère le podcast audio complet
        
        Args:
            script: Script généré par AudioScriptGenerator
            include_music: Ajouter des transitions musicales (optionnel)
            
        Returns:
            Chemin vers le fichier MP3 généré
        """
        print(" Génération de l'audio...")
        
        audio_segments = []
        
        # 1. Introduction
        if script.get('intro'):
            intro_audio = self._text_to_speech(script['intro'])
            audio_segments.append(intro_audio)
            print("    Intro générée")
        
        # 2. Contenu principal
        if script.get('main_content'):
            main_audio = self._text_to_speech(script['main_content'])
            audio_segments.append(main_audio)
            print("   Contenu principal généré")
        
        # 3. Conclusion
        if script.get('conclusion'):
            conclusion_audio = self._text_to_speech(script['conclusion'])
            audio_segments.append(conclusion_audio)
            print("   Conclusion générée")
        
        # Fusion de tous les segments
        if audio_segments:
            final_audio = self._merge_segments(audio_segments)
        else:
            # Fallback si rien n'a été généré
            fallback_text = "Erreur de génération audio. Veuillez réessayer."
            final_audio = self._text_to_speech(fallback_text)
        
        # Export
        output_path = self._export_audio(final_audio)
        
        print(f"Podcast généré: {output_path}")
        
        return output_path
    
    def _text_to_speech(self, text: str) -> AudioSegment:
        """
        Convertit du texte en audio avec gTTS
        
        Args:
            text: Texte à convertir
            
        Returns:
            Segment audio
        """
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Génération TTS
            tts = gTTS(
                text=text,
                lang=self.voice_config['lang'],
                slow=self.voice_config['slow'],
                tld=self.voice_config.get('tld', 'com')
            )
            
            tts.save(temp_path)
            
            # Charger comme AudioSegment
            audio = AudioSegment.from_mp3(temp_path)
            
            return audio
            
        finally:
            # Nettoyage du fichier temporaire
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _merge_segments(self, segments: list) -> AudioSegment:
        """
        Fusionne plusieurs segments audio
        
        Args:
            segments: Liste de AudioSegment
            
        Returns:
            Audio fusionné
        """
        if not segments:
            return AudioSegment.silent(duration=1000)
        
        # Fusion avec crossfade léger pour transitions douces
        merged = segments[0]
        
        for segment in segments[1:]:
            # Pause de 500ms entre segments
            pause = AudioSegment.silent(duration=500)
            merged = merged + pause + segment
        
        # Normalisation du volume
        merged = merged.normalize()
        
        return merged
    
    def _export_audio(self, audio: AudioSegment) -> str:
        """
        Exporte l'audio final en MP3
        
        Args:
            audio: Segment audio à exporter
            
        Returns:
            Chemin du fichier exporté
        """
        # Créer le dossier de sortie
        output_dir = 'generated_podcasts'
        os.makedirs(output_dir, exist_ok=True)
        
        # Nom de fichier avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(output_dir, f'podcast_{timestamp}.mp3')
        
        # Export avec qualité optimisée
        audio.export(
            output_path,
            format='mp3',
            bitrate='192k',
            tags={
                'artist': 'SnapLearn',
                'album': 'AMU Data Science Podcasts',
                'title': f'Podcast {timestamp}'
            }
        )
        
        # Calcul de la durée
        duration_seconds = len(audio) / 1000
        duration_minutes = duration_seconds / 60
        
        print(f"   Durée: {duration_minutes:.1f} min ({duration_seconds:.0f}s)")
        print(f"   Taille: {os.path.getsize(output_path) / (1024*1024):.1f} MB")
        
        return output_path

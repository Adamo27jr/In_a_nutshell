import qrcode
from pathlib import Path
from typing import Optional

class QRCodeGenerator:
    """Génère des QR codes stylisés pour la connexion mobile."""
    
    def __init__(self, output_dir: str = "mobile/static/qr_codes"):
        """
        Initialise le générateur de QR codes.
        
        Args:
            output_dir: Répertoire de sortie pour les QR codes
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_session_qr(
        self, 
        session_id: str, 
        base_url: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Génère un QR code pour une session mobile.
        
        Args:
            session_id: Identifiant de la session
            base_url: URL de base de l'application
            filename: Nom du fichier (optionnel)
            
        Returns:
            Chemin vers le fichier QR code généré
        """
        # URL complète avec session_id
        session_url = f"{base_url}/mobile/join?session={session_id}"
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        qr.add_data(session_url)
        qr.make(fit=True)
        
        # Générer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder
        if filename is None:
            filename = f"session_{session_id[:8]}.png"
            
        output_path = self.output_dir / filename
        img.save(str(output_path))
        
        print(f"📱 QR Code généré : {output_path}")
        
        return str(output_path)
    
    def generate_chapter_qr(
        self,
        chapter_id: str,
        base_url: str,
        include_quiz: bool = False
    ) -> str:
        """
        Génère un QR code pour accéder directement à un chapitre.
        
        Args:
            chapter_id: Identifiant du chapitre
            base_url: URL de base
            include_quiz: Inclure le quiz dans le lien
            
        Returns:
            Chemin vers le fichier QR code
        """
        url = f"{base_url}/chapter/{chapter_id}"
        if include_quiz:
            url += "?quiz=true"
            
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=3,
        )
        
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        filename = f"chapter_{chapter_id}.png"
        output_path = self.output_dir / filename
        img.save(str(output_path))
        
        print(f"📖 QR Code chapitre généré : {output_path}")
        
        return str(output_path)
    
    def generate_course_qr(
        self,
        doc_id: str,
        base_url: str,
        title: Optional[str] = None
    ) -> str:
        """
        Génère un QR code pour accéder à un cours.
        
        Args:
            doc_id: Identifiant du document
            base_url: URL de base
            title: Titre du cours (optionnel)
            
        Returns:
            Chemin vers le fichier QR code
        """
        url = f"{base_url}/api/courses/{doc_id}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        filename = f"course_{doc_id}.png"
        output_path = self.output_dir / filename
        img.save(str(output_path))
        
        print(f"📚 QR Code cours généré : {output_path}")
        
        return str(output_path)

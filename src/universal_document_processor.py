import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import cv2
import numpy as np
import google.generativeai as genai
import os
from typing import Dict, Union
from pathlib import Path
import json


class UniversalDocumentProcessor:
    """Processeur universel pour PDFs et images"""
    
    def __init__(self, gemini_api_key: str):
        """
        Initialise le processeur avec l'API Gemini
        
        Args:
            gemini_api_key: Clé API Google Gemini
        """
        genai.configure(api_key=gemini_api_key)
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
    
    def process_document(self, file_path: str) -> Dict:
        """
        Point d'entrée principal - détecte et traite tout type de document
        
        Args:
            file_path: Chemin vers le fichier (PDF ou image)
            
        Returns:
            Dict contenant le contenu extrait et les métadonnées
        """
        extension = Path(file_path).suffix.lower()
        
        if extension == '.pdf':
            return self.process_pdf(file_path)
        elif extension in ['.jpg', '.jpeg', '.png', '.heic']:
            return self.process_image(file_path)
        else:
            raise ValueError(f"Format non supporté: {extension}")
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """
        Traite un fichier PDF complet
        
        Args:
            pdf_path: Chemin vers le PDF
            
        Returns:
            Dict avec métadonnées et contenu extrait
        """
        print(f"📄 Traitement du PDF: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        
        # Métadonnées du document
        metadata = {
            'title': doc.metadata.get('title', 'Sans titre'),
            'author': doc.metadata.get('author', 'Inconnu'),
            'total_pages': len(doc),
            'file_size_mb': os.path.getsize(pdf_path) / (1024 * 1024)
        }
        
        # Extraction du contenu par page
        pages_content = []
        max_pages = min(len(doc), 15)  # Limiter à 15 pages pour le hackathon
        
        for page_num in range(max_pages):
            page = doc[page_num]
            text = page.get_text()
            
            pages_content.append({
                'page_number': page_num + 1,
                'text': text,
                'word_count': len(text.split()),
                'has_images': len(page.get_images()) > 0
            })
        
        doc.close()
        
        # Analyse globale
        total_words = sum(p['word_count'] for p in pages_content)
        
        return {
            'type': 'pdf',
            'metadata': metadata,
            'pages': pages_content,
            'total_words': total_words,
            'estimated_duration': min(total_words / 150, 20),  # max 20min
            'source_path': pdf_path
        }
    
    def process_image(self, image_path: str) -> Dict:
        """
        Traite une image (couverture, page, notes)
        
        Args:
            image_path: Chemin vers l'image
            
        Returns:
            Dict avec type détecté et contenu extrait
        """
        print(f"🖼️ Traitement de l'image: {image_path}")
        
        image = Image.open(image_path)
        
        # Classification du type d'image
        image_type = self._classify_image(image)
        print(f"   Type détecté: {image_type}")
        
        # OCR pour extraction de texte
        text = self._ocr_image(image)
        
        # Enrichissement avec Vision AI
        enhanced = self._enhance_with_vision(image, text, image_type)
        
        return {
            'type': 'image',
            'image_type': image_type,
            'text': text,
            'word_count': len(text.split()),
            'enhanced_metadata': enhanced,
            'source_path': image_path
        }
    
    def _classify_image(self, image: Image.Image) -> str:
        """
        Classifie automatiquement le type d'image
        
        Args:
            image: Image PIL
            
        Returns:
            Type d'image détecté
        """
        prompt = """
        Classifie cette image dans UNE de ces catégories:
        
        - book_cover: Couverture de livre
        - text_page: Page de texte imprimé (livre, article, document)
        - diagram: Diagramme, schéma, graphique
        - handwritten: Notes manuscrites
        - other: Autre type
        
        Réponds UNIQUEMENT avec le mot-clé de la catégorie (sans ponctuation).
        """
        
        try:
            response = self.vision_model.generate_content([prompt, image])
            classification = response.text.strip().lower()
            
            valid_types = ['book_cover', 'text_page', 'diagram', 'handwritten', 'other']
            return classification if classification in valid_types else 'text_page'
        except Exception as e:
            print(f"   Erreur classification: {e}")
            return 'text_page'
    
    def _ocr_image(self, image: Image.Image) -> str:
        """
        OCR avec preprocessing avancé
        
        Args:
            image: Image PIL
            
        Returns:
            Texte extrait
        """
        # Conversion en array numpy
        img_array = np.array(image)
        
        # Preprocessing
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Débruitage
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Binarisation adaptative
        binary = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # OCR avec Tesseract
        try:
            text = pytesseract.image_to_string(binary, lang='fra+eng')
            return text.strip()
        except Exception as e:
            print(f"   Erreur OCR: {e}")
            return ""
    
    def _enhance_with_vision(
        self, 
        image: Image.Image, 
        ocr_text: str,
        image_type: str
    ) -> Dict:
        """
        Enrichit avec Gemini Vision AI
        
        Args:
            image: Image PIL
            ocr_text: Texte extrait par OCR
            image_type: Type d'image détecté
            
        Returns:
            Métadonnées enrichies
        """
        # Prompts adaptés au type
        if image_type == 'book_cover':
            prompt = f"""
            Analyse cette couverture de livre.
            
            OCR: {ocr_text[:200]}
            
            Extrais en JSON:
            {{
                "title": "titre du livre",
                "author": "auteur",
                "genre": "genre littéraire",
                "themes": ["thème1", "thème2"],
                "main_topic": "sujet principal",
                "key_concepts": ["concept1", "concept2"],
                "estimated_difficulty": "beginner/intermediate/advanced"
            }}
            """
        else:
            prompt = f"""
            Analyse ce document.
            
            OCR: {ocr_text[:300]}
            
            Extrais en JSON:
            {{
                "main_topic": "sujet principal du document",
                "key_concepts": ["concept1", "concept2", "concept3"],
                "estimated_difficulty": "beginner/intermediate/advanced",
                "document_purpose": "description courte"
            }}
            """
        
        try:
            response = self.vision_model.generate_content([prompt, image])
            
            # Parser JSON
            json_text = response.text.replace('```json', '').replace('```', '').strip()
            enhanced = json.loads(json_text)
            
            return enhanced
        except Exception as e:
            print(f"   Erreur Vision AI: {e}")
            return {
                "main_topic": "Inconnu",
                "key_concepts": [],
                "estimated_difficulty": "intermediate"
            }

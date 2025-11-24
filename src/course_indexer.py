Copy"""
Indexe automatiquement les PDFs existants dans data/course_materials/
sans créer de fichiers JSON redondants.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
import PyPDF2
import re

class CourseIndexer:
    """Indexe et catalogue automatiquement les cours existants."""
    
    def __init__(self, course_materials_path: str, index_db_path: str):
        """
        Initialise l'indexeur de cours.
        
        Args:
            course_materials_path: Chemin vers data/course_materials/
            index_db_path: Chemin vers la base de données d'index
        """
        self.course_path = Path(course_materials_path)
        self.db_path = index_db_path
        self._init_database()
        
    def _init_database(self):
        """Crée la structure de base de données légère."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des documents
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            file_path TEXT UNIQUE NOT NULL,
            level TEXT,
            category TEXT,
            filename TEXT,
            file_hash TEXT,
            page_count INTEGER,
            extracted_title TEXT,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Table des chunks (morceaux de texte)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT,
            chunk_index INTEGER,
            content TEXT,
            page_number INTEGER,
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        )
        ''')
        
        # Table des métadonnées extraites
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_metadata (
            doc_id TEXT PRIMARY KEY,
            keywords TEXT,
            topics TEXT,
            difficulty_level TEXT,
            estimated_duration_min INTEGER,
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def scan_and_index_all(self) -> Dict[str, int]:
        """
        Scanne tous les PDFs dans data/course_materials/ et les indexe.
        
        Returns:
            Statistiques d'indexation
        """
        stats = {
            'total_files': 0,
            'new_indexed': 0,
            'updated': 0,
            'errors': 0
        }
        
        print(f"🔍 Scan du répertoire : {self.course_path}")
        
        # Parcourir M1 et M2
        for level in ['m1', 'm2']:
            level_path = self.course_path / level
            
            if not level_path.exists():
                print(f"⚠️  Dossier {level} introuvable")
                continue
            
            # Parcourir les catégories
            for category_path in level_path.iterdir():
                if not category_path.is_dir():
                    continue
                
                category = category_path.name
                print(f"\n📂 Catégorie : {level.upper()}/{category}")
                
                # Indexer tous les PDFs de cette catégorie
                for pdf_file in category_path.glob('**/*.pdf'):
                    stats['total_files'] += 1
                    
                    try:
                        result = self._index_document(
                            pdf_file, 
                            level.upper(), 
                            category
                        )
                        
                        if result == 'new':
                            stats['new_indexed'] += 1
                            print(f"  ✅ Indexé : {pdf_file.name}")
                        elif result == 'updated':
                            stats['updated'] += 1
                            print(f"  🔄 Mis à jour : {pdf_file.name}")
                        else:
                            print(f"  ⏭️  Déjà à jour : {pdf_file.name}")
                            
                    except Exception as e:
                        stats['errors'] += 1
                        print(f"  ❌ Erreur avec {pdf_file.name}: {e}")
        
        return stats
    
    def _index_document(
        self, 
        pdf_path: Path, 
        level: str, 
        category: str
    ) -> str:
        """
        Indexe un document PDF.
        
        Args:
            pdf_path: Chemin vers le PDF
            level: M1 ou M2
            category: Catégorie du cours
            
        Returns:
            'new', 'updated', ou 'unchanged'
        """
        # Calculer le hash du fichier
        file_hash = self._calculate_file_hash(pdf_path)
        doc_id = self._generate_doc_id(pdf_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier si le document existe déjà
        cursor.execute(
            'SELECT file_hash FROM documents WHERE doc_id = ?', 
            (doc_id,)
        )
        result = cursor.fetchone()
        
        if result and result[0] == file_hash:
            conn.close()
            return 'unchanged'
        
        # Extraire le contenu du PDF
        text_content, page_count = self._extract_pdf_content(pdf_path)
        title = self._extract_title_from_content(text_content, pdf_path.name)
        
        # Insérer ou mettre à jour le document
        cursor.execute('''
        INSERT OR REPLACE INTO documents 
        (doc_id, file_path, level, category, filename, file_hash, page_count, extracted_title)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doc_id,
            str(pdf_path.relative_to(self.course_path.parent)),
            level,
            category,
            pdf_path.name,
            file_hash,
            page_count,
            title
        ))
        
        # Découper le texte en chunks
        chunks = self._create_text_chunks(text_content)
        
        # Supprimer les anciens chunks
        cursor.execute('DELETE FROM document_chunks WHERE doc_id = ?', (doc_id,))
        
        # Insérer les nouveaux chunks
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            cursor.execute('''
            INSERT INTO document_chunks (chunk_id, doc_id, chunk_index, content, page_number)
            VALUES (?, ?, ?, ?, ?)
            ''', (chunk_id, doc_id, i, chunk['text'], chunk['page']))
        
        # Extraire et stocker les métadonnées
        metadata = self._extract_metadata(text_content, title)
        cursor.execute('''
        INSERT OR REPLACE INTO document_metadata 
        (doc_id, keywords, topics, difficulty_level, estimated_duration_min)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            doc_id,
            ','.join(metadata['keywords']),
            ','.join(metadata['topics']),
            metadata['difficulty'],
            metadata['duration']
        ))
        
        conn.commit()
        conn.close()
        
        return 'new' if result is None else 'updated'
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcule le hash MD5 d'un fichier."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _generate_doc_id(self, pdf_path: Path) -> str:
        """Génère un ID unique pour un document."""
        # Format: M1_statistics_chapter1_regression
        parts = pdf_path.parts
        level = parts[-3].upper()  # m1 ou m2
        category = parts[-2]
        filename = pdf_path.stem
        return f"{level}_{category}_{filename}".replace(' ', '_')
    
    def _extract_pdf_content(self, pdf_path: Path) -> tuple:
        """
        Extrait le texte complet d'un PDF.
        
        Returns:
            (texte_complet, nombre_de_pages)
        """
        text_content = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_content.append({
                        'page': page_num,
                        'text': text
                    })
        
        full_text = '\n\n'.join([p['text'] for p in text_content])
        return full_text, page_count
    
    def _extract_title_from_content(self, content: str, filename: str) -> str:
        """Extrait ou déduit le titre du document."""
        # Chercher un titre dans les premières lignes
        lines = content.split('\n')[:20]
        
        for line in lines:
            line = line.strip()
            # Titre probable : ligne courte en majuscules ou avec des mots-clés
            if (len(line) > 10 and len(line) < 100 and 
                (line.isupper() or 
                 any(keyword in line.lower() for keyword in 
                     ['chapitre', 'chapter', 'cours', 'introduction']))):
                return line
        
        # Sinon, utiliser le nom du fichier nettoyé
        return filename.replace('_', ' ').replace('.pdf', '').title()
    
    def _create_text_chunks(
        self, 
        content: str, 
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Dict]:
        """
        Découpe le texte en chunks avec overlap pour le RAG.
        
        Args:
            content: Texte complet
            chunk_size: Taille de chaque chunk (en caractères)
            overlap: Chevauchement entre chunks
            
        Returns:
            Liste de dictionnaires {text, page}
        """
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]
            
            # Essayer de couper à la fin d'une phrase
            if end < len(content):
                last_period = chunk_text.rfind('.')
                if last_period > chunk_size * 0.5:
                    end = start + last_period + 1
                    chunk_text = content[start:end]
            
            chunks.append({
                'text': chunk_text.strip(),
                'page': 0  # À améliorer avec le numéro de page réel
            })
            
            start = end - overlap
        
        return chunks
    
    def _extract_metadata(self, content: str, title: str) -> Dict:
        """
        Extrait automatiquement des métadonnées du contenu.
        
        Returns:
            Dictionnaire avec keywords, topics, difficulty, duration
        """
        # Mots-clés techniques courants en Data Science
        technical_keywords = {
            'regression', 'classification', 'clustering', 'neural', 'deep learning',
            'cnn', 'rnn', 'lstm', 'transformer', 'gradient', 'optimization',
            'numpy', 'pandas', 'scikit-learn', 'tensorflow', 'pytorch',
            'supervised', 'unsupervised', 'reinforcement', 'probability',
            'statistics', 'variance', 'covariance', 'distribution'
        }
        
        content_lower = content.lower()
        
        # Extraire les mots-clés présents
        found_keywords = [kw for kw in technical_keywords if kw in content_lower]
        
        # Déterminer les topics principaux
        topics = []
        if any(kw in content_lower for kw in ['neural', 'deep', 'cnn', 'rnn']):
            topics.append('Deep Learning')
        if any(kw in content_lower for kw in ['regression', 'classification']):
            topics.append('Machine Learning')
        if any(kw in content_lower for kw in ['numpy', 'pandas', 'python']):
            topics.append('Python')
        if any(kw in content_lower for kw in ['probability', 'statistics']):
            topics.append('Statistics')
        
        # Estimer la difficulté
        difficulty = 'intermediate'
        if 'advanced' in title.lower() or 'expert' in content_lower[:500]:
            difficulty = 'advanced'
        elif 'introduction' in title.lower() or 'basics' in content_lower[:500]:
            difficulty = 'beginner'
        
        # Estimer la durée de lecture (250 mots/min)
        word_count = len(content.split())
        estimated_duration = max(10, word_count // 250)
        
        return {
            'keywords': found_keywords[:10],
            'topics': topics if topics else ['General'],
            'difficulty': difficulty,
            'duration': estimated_duration
        }
    
    def get_all_documents(self) -> List[Dict]:
        """Récupère tous les documents indexés."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT d.doc_id, d.file_path, d.level, d.category, d.filename, 
               d.extracted_title, d.page_count, m.topics, m.difficulty_level
        FROM documents d
        LEFT JOIN document_metadata m ON d.doc_id = m.doc_id
        ORDER BY d.level, d.category, d.filename
        ''')
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                'doc_id': row[0],
                'file_path': row[1],
                'level': row[2],
                'category': row[3],
                'filename': row[4],
                'title': row[5],
                'page_count': row[6],
                'topics': row[7].split(',') if row[7] else [],
                'difficulty': row[8]
            })
        
        conn.close()
        return documents
    
    def search_documents(
        self, 
        query: str, 
        level: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Recherche des documents par mots-clés.
        
        Args:
            query: Termes de recherche
            level: Filtrer par niveau (M1, M2)
            category: Filtrer par catégorie
            
        Returns:
            Liste de documents correspondants
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = '''
        SELECT DISTINCT d.doc_id, d.file_path, d.level, d.category, 
               d.filename, d.extracted_title, d.page_count
        FROM documents d
        JOIN document_chunks c ON d.doc_id = c.doc_id
        WHERE c.content LIKE ?
        '''
        
        params = [f'%{query}%']
        
        if level:
            sql += ' AND d.level = ?'
            params.append(level)
        
        if category:
            sql += ' AND d.category = ?'
            params.append(category)
        
        sql += ' ORDER BY d.level, d.category'
        
        cursor.execute(sql, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'doc_id': row[0],
                'file_path': row[1],
                'level': row[2],
                'category': row[3],
                'filename': row[4],
                'title': row[5],
                'page_count': row[6]
            })
        
        conn.close()
        return results

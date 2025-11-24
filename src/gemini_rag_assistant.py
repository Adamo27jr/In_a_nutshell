import os
from typing import List, Dict, Optional
import google.generativeai as genai
from pathlib import Path
import sqlite3
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class GeminiRAGAssistant:
    """Assistant Gemini avec accès aux cours AMU via RAG."""
    
    def __init__(
        self, 
        course_index_db: str,
        embedding_model: str = 'all-MiniLM-L6-v2'
    ):
        """
        Initialise l'assistant Gemini avec RAG.
        
        Args:
            course_index_db: Chemin vers la base d'index des cours
            embedding_model: Modèle pour les embeddings sémantiques
        """
        # Configuration Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY non trouvée dans .env")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name=os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        )
        
        # Base de données des cours
        self.db_path = course_index_db
        
        # Modèle d'embeddings pour la recherche sémantique
        print("Chargement du modèle d'embeddings...")
        self.embedding_model = SentenceTransformer(embedding_model)
        print("Modèle d'embeddings chargé")
        
        # Cache des embeddings
        self.chunk_embeddings = None
        self.chunk_data = None
        self._load_embeddings_cache()
    
    def _load_embeddings_cache(self):
        """Charge ou crée le cache des embeddings."""
        cache_path = Path(self.db_path).parent / 'embeddings_cache.npz'
        
        if cache_path.exists():
            print("Chargement du cache d'embeddings...")
            data = np.load(cache_path, allow_pickle=True)
            self.chunk_embeddings = data['embeddings']
            self.chunk_data = data['chunk_data'].tolist()
            print(f"{len(self.chunk_data)} chunks chargés depuis le cache")
        else:
            print("🔨 Création du cache d'embeddings...")
            self._create_embeddings_cache()
            if self.chunk_embeddings is not None:
                np.savez(
                    cache_path,
                    embeddings=self.chunk_embeddings,
                    chunk_data=np.array(self.chunk_data, dtype=object)
                )
                print(f"Cache créé avec {len(self.chunk_data)} chunks")
    
    def _create_embeddings_cache(self):
        """Crée les embeddings pour tous les chunks."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT c.chunk_id, c.content, c.doc_id, d.extracted_title, 
               d.level, d.category, d.file_path
        FROM document_chunks c
        JOIN documents d ON c.doc_id = d.doc_id
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("Aucun chunk trouvé dans la base de données")
            return
        
        # Préparer les données
        self.chunk_data = []
        texts = []
        
        for row in rows:
            self.chunk_data.append({
                'chunk_id': row[0],
                'content': row[1],
                'doc_id': row[2],
                'title': row[3],
                'level': row[4],
                'category': row[5],
                'file_path': row[6]
            })
            texts.append(row[1])
        
        # Créer les embeddings
        print(f"Création des embeddings pour {len(texts)} chunks...")
        self.chunk_embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
    
    def find_relevant_chunks(
        self, 
        query: str, 
        top_k: int = 5,
        level: Optional[str] = None
    ) -> List[Dict]:
        """
        Trouve les chunks les plus pertinents pour une question.
        
        Args:
            query: Question de l'utilisateur
            top_k: Nombre de chunks à retourner
            level: Filtrer par niveau (M1, M2)
            
        Returns:
            Liste des chunks pertinents avec métadonnées
        """
        if self.chunk_embeddings is None:
            return []
        
        # Encoder la question
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True
        )
        
        # Calculer les similarités cosinus
        similarities = np.dot(self.chunk_embeddings, query_embedding) / (
            np.linalg.norm(self.chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Filtrer par niveau si spécifié
        if level:
            valid_indices = [
                i for i, chunk in enumerate(self.chunk_data)
                if chunk['level'] == level
            ]
            filtered_similarities = np.array([
                similarities[i] if i in valid_indices else -1
                for i in range(len(similarities))
            ])
        else:
            filtered_similarities = similarities
        
        # Récupérer les top_k
        top_indices = np.argsort(filtered_similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if filtered_similarities[idx] > 0.3:  # Seuil de pertinence
                chunk = self.chunk_data[idx].copy()
                chunk['similarity'] = float(filtered_similarities[idx])
                results.append(chunk)
        
        return results
    
    def answer_question(
        self, 
        question: str,
        level: Optional[str] = None,
        include_sources: bool = True
    ) -> Dict:
        """
        Répond à une question en utilisant les cours comme références.
        
        Args:
            question: Question de l'utilisateur
            level: Filtrer les références par niveau
            include_sources: Inclure les sources dans la réponse
            
        Returns:
            Dictionnaire avec la réponse et les sources
        """
        # Trouver les chunks pertinents
        relevant_chunks = self.find_relevant_chunks(
            question, 
            top_k=5,
            level=level
        )
        
        if not relevant_chunks:
            # Réponse sans contexte
            prompt = f"""Tu es un assistant pédagogique spécialisé en Data Science.
            
Question : {question}

Réponds de manière claire et pédagogique, même sans documents de référence disponibles."""
            
            response = self.model.generate_content(prompt)
            
            return {
                'answer': response.text,
                'sources': [],
                'has_course_references': False
            }
        
        # Construire le contexte à partir des chunks
        context = self._build_context(relevant_chunks)
        
        # Créer le prompt avec contexte
        prompt = f"""Tu es un assistant pédagogique spécialisé en Data Science pour l'université AMU.

CONTEXTE (extrait des cours AMU) :
{context}

QUESTION DE L'ÉTUDIANT :
{question}

INSTRUCTIONS :
1. Réponds de manière claire, pédagogique et structurée
2. Utilise les informations du contexte fourni
3. Cite explicitement les cours utilisés (ex: "Selon le cours de Machine Learning M1...")
4. Si le contexte ne suffit pas, indique-le et donne quand même une réponse générale
5. Utilise des exemples concrets si possible
6. Structure ta réponse avec des sections claires

RÉPONSE :"""
        
        # Générer la réponse
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=float(os.getenv('GEMINI_TEMPERATURE', 0.7)),
                max_output_tokens=int(os.getenv('GEMINI_MAX_TOKENS', 2048))
            )
        )
        
        # Préparer les sources
        sources = []
        if include_sources:
            sources = self._format_sources(relevant_chunks)
        
        return {
            'answer': response.text,
            'sources': sources,
            'has_course_references': True,
            'relevant_courses': list(set([c['title'] for c in relevant_chunks]))
        }
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Construit le contexte à partir des chunks pertinents."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk['title']} - {chunk['level']}/{chunk['category']}]\n"
                f"{chunk['content']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Formate les sources pour l'affichage."""
        sources = []
        seen_docs = set()
        
        for chunk in chunks:
            doc_id = chunk['doc_id']
            if doc_id not in seen_docs:
                sources.append({
                    'title': chunk['title'],
                    'level': chunk['level'],
                    'category': chunk['category'],
                    'file_path': chunk['file_path'],
                    'relevance': round(chunk['similarity'] * 100, 1)
                })
                seen_docs.add(doc_id)
        
        return sources
    
    def generate_quiz_from_course(
        self, 
        doc_id: str, 
        num_questions: int = 5
    ) -> List[Dict]:
        """
        Génère un quiz basé sur un cours spécifique.
        
        Args:
            doc_id: Identifiant du document
            num_questions: Nombre de questions à générer
            
        Returns:
            Liste de questions avec options et réponses
        """
        # Récupérer le contenu du cours
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT c.content, d.extracted_title
        FROM document_chunks c
        JOIN documents d ON c.doc_id = d.doc_id
        WHERE c.doc_id = ?
        ORDER BY c.chunk_index
        LIMIT 10
        ''', (doc_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        # Combiner les chunks
        course_content = '\n\n'.join([row[0] for row in rows])
        course_title = rows[0][1]
        
        # Prompt pour générer le quiz
        prompt = f"""Tu es un professeur créant un quiz pédagogique.

COURS : {course_title}

EXTRAIT DU CONTENU :
{course_content[:3000]}

Génère {num_questions} questions à choix multiples basées sur ce contenu.

Format JSON strict :
[
  {{
    "question": "Question claire et précise",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option correcte",
    "explanation": "Explication détaillée de la réponse",
    "difficulty": "beginner|intermediate|advanced"
  }}
]

Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire."""
        
        response = self.model.generate_content(prompt)
        
        # Parser la réponse JSON
        import json
        import re
        
        # Extraire le JSON de la réponse
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            try:
                quiz_questions = json.loads(json_match.group())
                return quiz_questions
            except json.JSONDecodeError:
                print("Erreur de parsing JSON")
                return []
        
        return []

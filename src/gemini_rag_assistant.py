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
            model_name=os.getenv('GEMINI_MODEL', 'models/gemini-2.5-flash')
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
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Génère l'embedding pour un texte donné."""
        return self.embedding_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
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
        if self.chunk_embeddings is None or len(self.chunk_embeddings) == 0:
            return []
        
        # Encoder la question avec normalisation
        query_embedding = self._generate_embedding(query)
        
        # Normaliser les embeddings des chunks si ce n'est pas déjà fait
        chunk_norms = np.linalg.norm(self.chunk_embeddings, axis=1, keepdims=True)
        chunk_norms = np.where(chunk_norms == 0, 1, chunk_norms)  # Éviter division par zéro
        normalized_chunks = self.chunk_embeddings / chunk_norms
        
        # Calculer les similarités cosinus
        similarities = np.dot(normalized_chunks, query_embedding)
        
        # Remplacer les NaN et Inf par 0
        similarities = np.nan_to_num(similarities, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Filtrer par niveau si spécifié
        if level:
            valid_indices = [
                i for i, chunk in enumerate(self.chunk_data)
                if chunk['level'] == level
            ]
            
            if not valid_indices:
                return []
            
            # Créer un masque pour les indices valides
            mask = np.zeros(len(similarities), dtype=bool)
            mask[valid_indices] = True
            
            # Mettre -1 pour les indices non valides
            filtered_similarities = np.where(mask, similarities, -1.0)
        else:
            filtered_similarities = similarities
        
        # Récupérer les top_k indices
        top_indices = np.argsort(filtered_similarities)[-top_k:][::-1]
        
        # Construire les résultats
        results = []
        for idx in top_indices:
            similarity_score = float(filtered_similarities[idx])
            
            # Vérifier que la similarité est valide et au-dessus du seuil
            if similarity_score > 0.2:  # Seuil de pertinence abaissé
                chunk = self.chunk_data[idx].copy()
                
                # S'assurer que similarity est un nombre valide
                if np.isnan(similarity_score) or np.isinf(similarity_score):
                    similarity_score = 0.0
                
                chunk['similarity'] = similarity_score
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
                'answer': self._extract_response_text(response),
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
            'answer': self._extract_response_text(response),
            'sources': sources,
            'has_course_references': True,
            'relevant_courses': list(set([c['title'] for c in relevant_chunks]))
        }
    
    def _extract_response_text(self, response) -> str:
        """
        Extrait le texte d'une réponse Gemini de manière robuste.
        Compatible avec toutes les versions de l'API.
        """
        try:
            # Méthode 1 : Accessor simple
            return response.text
        except AttributeError:
            # Méthode 2 : Accessor complet
            try:
                if response.candidates and len(response.candidates) > 0:
                    parts = response.candidates[0].content.parts
                    if parts and len(parts) > 0:
                        return parts[0].text
            except:
                pass
        
        # Si tout échoue
        return "Erreur : Impossible d'extraire la réponse de Gemini"
    
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
            similarity = chunk.get('similarity', 0.0)
            
            # Vérifier que similarity est valide
            if np.isnan(similarity) or np.isinf(similarity):
                similarity = 0.0
            
            if doc_id not in seen_docs:
                sources.append({
                    'doc_id': doc_id,
                    'title': chunk['title'],
                    'level': chunk['level'],
                    'category': chunk['category'],
                    'file_path': chunk['file_path'],
                    'similarity': float(similarity)
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
        response_text = self._extract_response_text(response)
        
        # Parser la réponse JSON
        import json
        import re
        
        # Extraire le JSON de la réponse
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            try:
                quiz_questions = json.loads(json_match.group())
                return quiz_questions
            except json.JSONDecodeError:
                print("Erreur de parsing JSON")
                return []
        
        return []

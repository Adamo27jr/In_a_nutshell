from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
from typing import List, Dict
import pickle
import os


class AMUKnowledgeBase:
    """Base de connaissance AMU Data Science pour RAG"""
    
    def __init__(self, corpus_path: str = "data/amu_datascience_corpus.json"):
        """
        Initialise la base de connaissance
        
        Args:
            corpus_path: Chemin vers le fichier JSON du corpus
        """
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunks = []
        self.metadata = []
        self.index = None
        
        # Charger le corpus
        if os.path.exists(corpus_path):
            with open(corpus_path, 'r', encoding='utf-8') as f:
                self.corpus = json.load(f)
        else:
            print(f" Corpus non trouvé: {corpus_path}")
            self.corpus = {"course_materials": [], "common_questions": []}
        
        self._build_index()
    
    def _build_index(self):
        """Construit l'index FAISS à partir du corpus"""
        print(" Construction de l'index de connaissance AMU...")
        
        # Extraction de tous les chunks
        for material in self.corpus.get('course_materials', []):
            # Chunk principal (contenu complet)
            self.chunks.append(material['content'])
            self.metadata.append({
                'type': 'course_content',
                'week': material['week'],
                'title': material['title'],
                'topics': material['topics']
            })
            
            # Chunks des concepts clés
            for concept in material.get('key_concepts', []):
                chunk_text = f"{concept['term']}: {concept['definition']}. Exemple: {concept['example']}"
                self.chunks.append(chunk_text)
                self.metadata.append({
                    'type': 'concept',
                    'week': material['week'],
                    'term': concept['term'],
                    'topics': [concept['term'].lower()]
                })
        
        # Ajout des questions communes
        for qa in self.corpus.get('common_questions', []):
            chunk_text = f"Question: {qa['question']}\nRéponse: {qa['answer']}"
            self.chunks.append(chunk_text)
            self.metadata.append({
                'type': 'qa',
                'week': qa.get('week', 0),
                'topics': qa.get('related_topics', [])
            })
        
        if not self.chunks:
            print(" Aucun chunk extrait du corpus")
            return
        
        # Génération des embeddings
        print(f"📊 Génération des embeddings pour {len(self.chunks)} chunks...")
        embeddings = self.embedding_model.encode(
            self.chunks,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Construction de l'index FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance
        self.index.add(embeddings.astype('float32'))
        
        print(f" Index construit: {len(self.chunks)} chunks indexés")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Dict = None
    ) -> List[Dict]:
        """
        Recherche sémantique dans la base
        
        Args:
            query: Question ou texte de recherche
            top_k: Nombre de résultats à retourner
            filters: Filtres optionnels (ex: {'week': 3})
            
        Returns:
            Liste de résultats avec texte, métadonnées et scores
        """
        if self.index is None or len(self.chunks) == 0:
            print("⚠️ Index vide, retour de résultats vides")
            return []
        
        # Embedding de la query
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        
        # Recherche dans FAISS
        search_k = min(top_k * 3, len(self.chunks))  # Chercher plus pour filtrage
        distances, indices = self.index.search(
            query_embedding.astype('float32'), 
            search_k
        )
        
        # Récupération des résultats
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:  # Pas de résultat
                continue
            
            result = {
                'text': self.chunks[idx],
                'metadata': self.metadata[idx],
                'score': float(distances[0][i]),
                'rank': i + 1
            }
            
            # Filtrage par métadonnées
            if filters:
                if not self._matches_filters(result['metadata'], filters):
                    continue
            
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Vérifie si les métadonnées correspondent aux filtres"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                # Intersection pour les listes
                if not any(v in metadata[key] for v in value):
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True
    
    def get_context(
        self, 
        query: str, 
        max_tokens: int = 1500,
        week_filter: int = None
    ) -> str:
        """
        Récupère le contexte optimal pour une query (pour RAG)
        
        Args:
            query: Question ou sujet
            max_tokens: Nombre max de tokens dans le contexte
            week_filter: Filtrer par semaine spécifique
            
        Returns:
            Contexte formaté pour le prompt
        """
        # Filtres optionnels
        filters = {}
        if week_filter:
            filters['week'] = week_filter
        
        # Recherche
        results = self.search(query, top_k=5, filters=filters if filters else None)
        
        if not results:
            return "Aucun contexte pertinent trouvé dans la base de cours."
        
        # Construction du contexte
        context_parts = []
        current_tokens = 0
        
        for result in results:
            # Estimation tokens (rough: 1 token ≈ 4 chars)
            chunk_tokens = len(result['text']) // 4
            
            if current_tokens + chunk_tokens > max_tokens:
                break
            
            # Formatage avec source
            source_info = f"[Semaine {result['metadata']['week']} - {result['metadata'].get('title', result['metadata'].get('type', 'Source'))}]"
            context_parts.append(f"{source_info}\n{result['text']}\n")
            
            current_tokens += chunk_tokens
        
        return "\n---\n".join(context_parts)
    
    def save(self, path: str = "data/amu_knowledge_base.pkl"):
        """Sauvegarde l'index pour réutilisation rapide"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata,
                'index': faiss.serialize_index(self.index) if self.index else None
            }, f)
        
        print(f" Base sauvegardée: {path}")
    
    @classmethod
    def load(cls, path: str = "data/amu_knowledge_base.pkl"):
        """Charge une base sauvegardée"""
        instance = cls.__new__(cls)
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        instance.chunks = data['chunks']
        instance.metadata = data['metadata']
        instance.index = faiss.deserialize_index(data['index']) if data['index'] else None
        instance.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        instance.corpus = {}
        
        print(f" Base chargée: {len(instance.chunks)} chunks")
        
        return instance

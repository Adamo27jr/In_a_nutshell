import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import pickle

class VectorStoreManager:
    """Gère le stockage et la recherche de vecteurs d'embeddings."""
    
    def __init__(self, store_path: str = "database/vector_embeddings"):
        """
        Initialise le gestionnaire de stockage vectoriel.
        
        Args:
            store_path: Chemin vers le dossier de stockage
        """
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.embeddings = None
        self.metadata = []
        
    def save_embeddings(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict],
        name: str = "course_embeddings"
    ):
        """
        Sauvegarde les embeddings et leurs métadonnées.
        
        Args:
            embeddings: Tableau numpy des embeddings
            metadata: Liste des métadonnées associées
            name: Nom du fichier de sauvegarde
        """
        embedding_file = self.store_path / f"{name}.npy"
        metadata_file = self.store_path / f"{name}_metadata.pkl"
        
        # Sauvegarder les embeddings
        np.save(embedding_file, embeddings)
        
        # Sauvegarder les métadonnées
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"✅ Embeddings sauvegardés : {embedding_file}")
        print(f"✅ Métadonnées sauvegardées : {metadata_file}")
    
    def load_embeddings(self, name: str = "course_embeddings") -> tuple:
        """
        Charge les embeddings et métadonnées.
        
        Args:
            name: Nom du fichier à charger
            
        Returns:
            Tuple (embeddings, metadata)
        """
        embedding_file = self.store_path / f"{name}.npy"
        metadata_file = self.store_path / f"{name}_metadata.pkl"
        
        if not embedding_file.exists():
            print(f"⚠️  Fichier d'embeddings non trouvé : {embedding_file}")
            return None, []
        
        # Charger les embeddings
        embeddings = np.load(embedding_file)
        
        # Charger les métadonnées
        if metadata_file.exists():
            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)
        else:
            metadata = []
        
        self.embeddings = embeddings
        self.metadata = metadata
        
        print(f"✅ {len(embeddings)} embeddings chargés")
        
        return embeddings, metadata
    
    def search_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Dict]:
        """
        Recherche les embeddings les plus similaires.
        
        Args:
            query_embedding: Vecteur de requête
            top_k: Nombre de résultats
            threshold: Seuil de similarité minimum
            
        Returns:
            Liste des résultats avec scores
        """
        if self.embeddings is None:
            print("⚠️  Aucun embedding chargé")
            return []
        
        # Calculer les similarités cosinus
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Récupérer les top_k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] >= threshold:
                result = self.metadata[idx].copy() if idx < len(self.metadata) else {}
                result['similarity'] = float(similarities[idx])
                results.append(result)
        
        return results
    
    def add_embedding(
        self,
        embedding: np.ndarray,
        metadata: Dict
    ):
        """
        Ajoute un nouvel embedding au store.
        
        Args:
            embedding: Vecteur d'embedding
            metadata: Métadonnées associées
        """
        if self.embeddings is None:
            self.embeddings = embedding.reshape(1, -1)
            self.metadata = [metadata]
        else:
            self.embeddings = np.vstack([self.embeddings, embedding])
            self.metadata.append(metadata)
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du store."""
        if self.embeddings is None:
            return {
                'total_embeddings': 0,
                'embedding_dim': 0
            }
        
        return {
            'total_embeddings': len(self.embeddings),
            'embedding_dim': self.embeddings.shape[1],
            'metadata_count': len(self.metadata)
        }

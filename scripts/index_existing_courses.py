import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.append(str(Path(__file__).parent.parent))

from src.course_indexer import CourseIndexer
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    """Indexe tous les cours existants."""
    
    print("=" * 70)
    print("📚 INDEXATION AUTOMATIQUE DES COURS AMU DATA SCIENCE")
    print("=" * 70)
    
    # Chemins
    course_path = os.getenv('COURSE_MATERIALS_PATH', 'data/course_materials')
    index_db = os.getenv('INDEX_DB_PATH', 'database/course_index.db')
    
    # Créer le dossier database si nécessaire
    Path(index_db).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialiser l'indexeur
    indexer = CourseIndexer(course_path, index_db)
    
    # Scanner et indexer
    stats = indexer.scan_and_index_all()
    
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DE L'INDEXATION")
    print("=" * 70)
    print(f"✅ Fichiers scannés : {stats['total_files']}")
    print(f"🆕 Nouveaux indexés : {stats['new_indexed']}")
    print(f"🔄 Mis à jour : {stats['updated']}")
    print(f"❌ Erreurs : {stats['errors']}")
    print("=" * 70)
    
    # Afficher les documents indexés
    print("\n📖 DOCUMENTS INDEXÉS :")
    documents = indexer.get_all_documents()
    
    current_level = None
    for doc in documents:
        if doc['level'] != current_level:
            current_level = doc['level']
            print(f"\n{'='*70}")
            print(f"Niveau {current_level}")
            print(f"{'='*70}")
        
        print(f"\n📄 {doc['title']}")
        print(f"   Catégorie: {doc['category']}")
        print(f"   Fichier: {doc['filename']}")
        print(f"   Pages: {doc['page_count']}")
        print(f"   Topics: {', '.join(doc['topics'])}")
        print(f"   Difficulté: {doc['difficulty']}")
    
    print(f"\n✅ Indexation terminée ! Base de données : {index_db}")

if __name__ == "__main__":
    main()

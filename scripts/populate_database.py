"""
Script pour peupler la base de données avec les cours AMU.
Charge les données depuis les fichiers JSON ou directement depuis les PDFs.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import sys

# Ajouter le dossier parent au path
sys.path.append(str(Path(__file__).parent.parent))

from src.course_indexer import CourseIndexer

def create_database_schema(db_path: str):
    """
    Crée le schéma de la base de données.
    
    Args:
        db_path: Chemin vers le fichier de base de données
    """
    # Créer le dossier si nécessaire
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📋 Création du schéma de base de données...")
    
    # Lire et exécuter le schéma SQL
    schema_path = Path(__file__).parent.parent / 'database' / 'schema.sql'
    
    if schema_path.exists():
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Exécuter le schéma
        cursor.executescript(schema_sql)
        print("✅ Schéma créé avec succès")
    else:
        print("⚠️  Fichier schema.sql non trouvé, création manuelle...")
        
        # Créer les tables manuellement
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
        
        print("✅ Tables créées manuellement")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Base de données initialisée : {db_path}\n")

def load_sample_data_from_json(db_path: str, json_files: list):
    """
    Charge les données d'exemple depuis les fichiers JSON.
    
    Args:
        db_path: Chemin vers la base de données
        json_files: Liste des fichiers JSON à charger
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_courses = 0
    total_chapters = 0
    total_quizzes = 0
    
    for json_file in json_files:
        if not Path(json_file).exists():
            print(f"⚠️  Fichier non trouvé : {json_file}")
            continue
        
        print(f"\n📥 Chargement de {Path(json_file).name}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        courses_loaded = 0
        chapters_loaded = 0
        quizzes_loaded = 0
        
        for course in data.get('courses', []):
            try:
                # Insérer le cours
                cursor.execute('''
                INSERT OR IGNORE INTO courses 
                (course_id, level, title, category, professor, semester, credits, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    course['course_id'],
                    course['level'],
                    course['title'],
                    course['category'],
                    course.get('professor'),
                    course.get('semester'),
                    course.get('credits'),
                    course.get('description')
                ))
                courses_loaded += 1
                
                # Insérer les chapitres
                for chapter in course.get('chapters', []):
                    cursor.execute('''
                    INSERT OR IGNORE INTO chapters 
                    (chapter_id, course_id, chapter_number, title, content_path, 
                     duration_minutes, difficulty_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        chapter['chapter_id'],
                        course['course_id'],
                        chapter['chapter_number'],
                        chapter['title'],
                        chapter['content_path'],
                        chapter['duration_minutes'],
                        chapter['difficulty_level']
                    ))
                    chapters_loaded += 1
                    
                    # Insérer les quiz
                    for quiz in chapter.get('quizzes', []):
                        cursor.execute('''
                        INSERT OR IGNORE INTO quizzes 
                        (quiz_id, chapter_id, question_text, question_type, 
                         options, correct_answer, explanation, difficulty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            quiz['quiz_id'],
                            chapter['chapter_id'],
                            quiz['question_text'],
                            quiz['question_type'],
                            json.dumps(quiz['options']),
                            quiz['correct_answer'],
                            quiz['explanation'],
                            quiz['difficulty']
                        ))
                        quizzes_loaded += 1
            
            except Exception as e:
                print(f"⚠️  Erreur lors de l'insertion de {course['course_id']}: {e}")
                continue
        
        print(f"   ✅ {courses_loaded} cours, {chapters_loaded} chapitres, {quizzes_loaded} quiz")
        
        total_courses += courses_loaded
        total_chapters += chapters_loaded
        total_quizzes += quizzes_loaded
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Total chargé : {total_courses} cours, {total_chapters} chapitres, {total_quizzes} quiz")

def populate_from_pdfs(db_path: str, course_materials_path: str):
    """
    Peuple la base de données en scannant directement les PDFs.
    
    Args:
        db_path: Chemin vers la base de données
        course_materials_path: Chemin vers data/course_materials/
    """
    print("\n📚 Indexation des PDFs existants...")
    
    indexer = CourseIndexer(
        course_materials_path=course_materials_path,
        index_db_path=db_path
    )
    
    stats = indexer.scan_and_index_all()
    
    print("\n📊 Statistiques d'indexation :")
    print(f"   📄 Fichiers scannés : {stats['total_files']}")
    print(f"   🆕 Nouveaux indexés : {stats['new_indexed']}")
    print(f"   🔄 Mis à jour : {stats['updated']}")
    print(f"   ❌ Erreurs : {stats['errors']}")

def display_database_stats(db_path: str):
    """
    Affiche les statistiques de la base de données.
    
    Args:
        db_path: Chemin vers la base de données
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
    print("="*70)
    
    # Compter les documents
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    print(f"\n📄 Documents indexés : {doc_count}")
    
    # Compter les chunks
    cursor.execute("SELECT COUNT(*) FROM document_chunks")
    chunk_count = cursor.fetchone()[0]
    print(f"📦 Chunks de texte : {chunk_count}")
    
    # Documents par niveau
    cursor.execute("""
        SELECT level, COUNT(*) 
        FROM documents 
        GROUP BY level
        ORDER BY level
    """)
    print("\n📚 Par niveau :")
    for level, count in cursor.fetchall():
        print(f"   {level} : {count} documents")
    
    # Documents par catégorie
    cursor.execute("""
        SELECT category, COUNT(*) 
        FROM documents 
        GROUP BY category
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    print("\n📂 Top 10 catégories :")
    for category, count in cursor.fetchall():
        print(f"   {category} : {count} documents")
    
    # Métadonnées
    cursor.execute("SELECT COUNT(*) FROM document_metadata")
    metadata_count = cursor.fetchone()[0]
    print(f"\n🏷️  Métadonnées : {metadata_count}")
    
    conn.close()
    print("="*70)

def main():
    """Fonction principale."""
    
    print("="*70)
    print("🗄️  POPULATION DE LA BASE DE DONNÉES AMU DATA SCIENCE")
    print("="*70)
    
    # Chemins
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'database' / 'amu_courses.db'
    course_materials_path = project_root / 'data' / 'course_materials'
    sample_data_dir = project_root / 'database' / 'sample_data'
    
    # 1. Créer le schéma
    print("\n📋 Étape 1 : Création du schéma")
    create_database_schema(str(db_path))
    
    # 2. Charger les données JSON si disponibles
    json_files = []
    if sample_data_dir.exists():
        json_files = list(sample_data_dir.glob('*.json'))
    
    if json_files:
        print("\n📥 Étape 2 : Chargement des données JSON")
        load_sample_data_from_json(str(db_path), [str(f) for f in json_files])
    else:
        print("\n⚠️  Pas de fichiers JSON trouvés dans database/sample_data/")
    
    # 3. Scanner et indexer les PDFs
    if course_materials_path.exists():
        print("\n📚 Étape 3 : Indexation des PDFs")
        populate_from_pdfs(str(db_path), str(course_materials_path))
    else:
        print(f"\n⚠️  Dossier {course_materials_path} introuvable")
        print("💡 Créez le dossier et ajoutez vos cours avant de lancer ce script")
    
    # 4. Afficher les statistiques
    display_database_stats(str(db_path))
    
    print("\n✅ Population de la base de données terminée !")
    print(f"📍 Base de données : {db_path}")
    
    print("\n🎯 Prochaines étapes :")
    print("   1. Vérifiez les données : sqlite3 database/amu_courses.db")
    print("   2. Lancez l'application : python app.py")
    print("   3. Testez l'API : curl http://localhost:5000/api/courses")
    print("="*70)

if __name__ == "__main__":
    main()

"""
Script d'initialisation de la base de données.
Crée les tables et peut charger des données de test.
"""

import sqlite3
from pathlib import Path
import json

def init_database(db_path='database/amu_courses.db', schema_path='database/schema.sql'):
    """
    Initialise la base de données avec le schéma.
    
    Args:
        db_path: Chemin vers le fichier de base de données
        schema_path: Chemin vers le fichier SQL du schéma
    """
    # Créer le dossier si nécessaire
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lire et exécuter le schéma SQL
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Exécuter le schéma
    cursor.executescript(schema_sql)
    
    conn.commit()
    conn.close()
    
    print(f"Base de données initialisée : {db_path}")

def load_sample_data(db_path='database/amu_courses.db'):
    """
    Charge les données d'exemple depuis les fichiers JSON.
    
    Args:
        db_path: Chemin vers la base de données
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    sample_data_dir = Path('database/sample_data')
    
    # Charger M1 et M2
    for json_file in sample_data_dir.glob('*.json'):
        print(f"Chargement de {json_file.name}...")
        
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
                print(f"Erreur lors du chargement de {course['course_id']}: {e}")
        
        print(f"   {courses_loaded} cours, {chapters_loaded} chapitres, {quizzes_loaded} quiz")
    
    conn.commit()
    conn.close()
    
    print("Données d'exemple chargées")

if __name__ == '__main__':
    print("="*70)
    print("INITIALISATION DE LA BASE DE DONNÉES AMU")
    print("="*70)
    
    # Initialiser le schéma
    init_database()
    
    # Charger les données d'exemple si disponibles
    if Path('database/sample_data').exists():
        load_sample_data()
    
    print("="*70)
    print("Initialisation terminée !")
    print("="*70)

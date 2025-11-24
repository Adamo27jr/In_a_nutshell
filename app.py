"""
Application Flask principale - Upload et Scan de Livre/PDF → Résumés Vocaux + Quiz + Assistant Gemini
Projet AMU Data Science avec interaction mobile et assistant IA
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv
import google.generativeai as genai
import socket

# Imports des modules existants
from src.universal_document_processor import UniversalDocumentProcessor
from src.amu_knowledge_base import AMUKnowledgeBase
from src.audio_script_generator import AudioScriptGenerator
from src.audio_generator import AudioGenerator
from src.interactive_quiz_manager import InteractiveQuizManager

# Nouveaux imports pour mobile et Gemini
from src.mobile_sync_manager import MobileSyncManager
from src.qr_code_generator import QRCodeGenerator
from src.real_time_interaction import RealTimeInteractionManager
from src.gemini_rag_assistant import GeminiRAGAssistant
from src.course_indexer import CourseIndexer

# Charger les variables d'environnement
load_dotenv()

# ============================================================================
# FONCTION HELPER POUR EXTRAIRE LES RÉPONSES GEMINI
# ============================================================================

def extract_gemini_response(response):
    """
    Extrait le texte d'une réponse Gemini de manière robuste
    Compatible avec toutes les versions de l'API
    """
    try:
        # Méthode 1 : Accessor simple (anciennes versions)
        return response.text
    except AttributeError:
        # Méthode 2 : Accessor complet (nouvelles versions)
        try:
            if response.candidates and len(response.candidates) > 0:
                parts = response.candidates[0].content.parts
                if parts and len(parts) > 0:
                    return parts[0].text
        except:
            pass
    
    # Si tout échoue
    return "Erreur : Impossible d'extraire la réponse de Gemini"

# ============================================================================
# FONCTION POUR OBTENIR L'IP LOCALE
# ============================================================================

def get_local_ip():
    """Obtient l'adresse IP locale de la machine."""
    try:
        # Créer une socket pour obtenir l'IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

# ============================================================================
# CONFIGURATION DE L'APPLICATION
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'docx'}

# Configuration CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Créer les dossiers nécessaires
REQUIRED_FOLDERS = [
    'uploads',
    'generated_podcasts/audio_files',
    'generated_podcasts/transcripts',
    'generated_podcasts/metadata',
    'mobile/static/qr_codes',
    'database',
    'database/vector_embeddings'
]

for folder in REQUIRED_FOLDERS:
    Path(folder).mkdir(parents=True, exist_ok=True)

# ============================================================================
# INITIALISATION DES GESTIONNAIRES
# ============================================================================

print("🚀 Initialisation de l'application...")

# Gestionnaires existants
try:
    document_processor = UniversalDocumentProcessor()
    print("✅ UniversalDocumentProcessor initialisé")
except Exception as e:
    print(f"⚠️  Erreur UniversalDocumentProcessor: {e}")
    document_processor = None

try:
    knowledge_base = AMUKnowledgeBase()
    print("✅ AMUKnowledgeBase initialisé")
except Exception as e:
    print(f"⚠️  Erreur AMUKnowledgeBase: {e}")
    knowledge_base = None

try:
    script_generator = AudioScriptGenerator()
    print("✅ AudioScriptGenerator initialisé")
except Exception as e:
    print(f"⚠️  Erreur AudioScriptGenerator: {e}")
    script_generator = None

try:
    audio_generator = AudioGenerator()
    print("✅ AudioGenerator initialisé")
except Exception as e:
    print(f"⚠️  Erreur AudioGenerator: {e}")
    audio_generator = None

try:
    quiz_manager = InteractiveQuizManager()
    print("✅ InteractiveQuizManager initialisé")
except Exception as e:
    print(f"⚠️  Erreur InteractiveQuizManager: {e}")
    quiz_manager = None

# Gestionnaires mobiles
try:
    sync_manager = MobileSyncManager(database_path='database/amu_courses.db')
    print("✅ MobileSyncManager initialisé")
except Exception as e:
    print(f"⚠️  Erreur MobileSyncManager: {e}")
    sync_manager = None

try:
    qr_generator = QRCodeGenerator(output_dir='mobile/static/qr_codes')
    print("✅ QRCodeGenerator initialisé")
except Exception as e:
    print(f"⚠️  Erreur QRCodeGenerator: {e}")
    qr_generator = None

try:
    rt_manager = RealTimeInteractionManager()
    print("✅ RealTimeInteractionManager initialisé")
except Exception as e:
    print(f"⚠️  Erreur RealTimeInteractionManager: {e}")
    rt_manager = None

# Gestionnaire Gemini et indexeur
try:
    # Configuration Gemini
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel(
            model_name=os.getenv('GEMINI_MODEL', 'models/gemini-2.5-flash')
        )
        print("✅ Gemini API configurée")
    else:
        gemini_model = None
        print("⚠️  GOOGLE_API_KEY non trouvée dans .env")
except Exception as e:
    print(f"⚠️  Erreur configuration Gemini: {e}")
    gemini_model = None

try:
    gemini_assistant = GeminiRAGAssistant(
        course_index_db='database/amu_courses.db'
    )
    print("✅ GeminiRAGAssistant initialisé")
except Exception as e:
    print(f"⚠️  Erreur GeminiRAGAssistant: {e}")
    gemini_assistant = None

try:
    course_indexer = CourseIndexer(
        course_materials_path=os.getenv('COURSE_MATERIALS_PATH', 'data/course_materials'),
        index_db_path='database/amu_courses.db'
    )
    print("✅ CourseIndexer initialisé")
except Exception as e:
    print(f"⚠️  Erreur CourseIndexer: {e}")
    course_indexer = None

print("✅ Application initialisée avec succès!\n")

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def allowed_file(filename):
    """Vérifie si le fichier a une extension autorisée."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_unique_id():
    """Génère un ID unique."""
    return str(uuid.uuid4())

# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================

@app.route('/')
def index():
    """Page d'accueil."""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Endpoint de vérification de santé."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'document_processor': document_processor is not None,
            'knowledge_base': knowledge_base is not None,
            'audio_generator': audio_generator is not None,
            'quiz_manager': quiz_manager is not None,
            'gemini_model': gemini_model is not None,
            'gemini_assistant': gemini_assistant is not None,
            'course_indexer': course_indexer is not None
        }
    })

# ============================================================================
# ROUTES UPLOAD ET TRAITEMENT DE DOCUMENTS AVEC GEMINI
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload simple d'un document."""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Type de fichier non autorisé'}), 400
    
    try:
        # Sauvegarder le fichier
        filename = secure_filename(file.filename)
        file_id = generate_unique_id()
        file_path = Path(app.config['UPLOAD_FOLDER']) / f"{file_id}_{filename}"
        file.save(str(file_path))
        
        # Traiter le document
        if document_processor:
            extracted_text = document_processor.process_document(str(file_path))
        else:
            extracted_text = "Document processor non disponible"
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'text_preview': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text,
            'text_length': len(extracted_text)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-and-explain', methods=['POST'])
def upload_and_explain():
    """
    Upload un document, l'explique avec Gemini et cherche des références
    dans les cours existants de data/course_materials/
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Type de fichier non autorisé'}), 400
    
    if not gemini_model:
        return jsonify({'error': 'Gemini API non configurée'}), 503
    
    try:
        # 1. Sauvegarder le fichier uploadé
        filename = secure_filename(file.filename)
        file_id = generate_unique_id()
        file_path = Path(app.config['UPLOAD_FOLDER']) / f"{file_id}_{filename}"
        file.save(str(file_path))
        
        print(f"📄 Fichier uploadé : {filename}")
        
        # 2. Extraire le texte du document
        if document_processor:
            extracted_text = document_processor.process_document(str(file_path))
            print(f"✅ Texte extrait : {len(extracted_text)} caractères")
        else:
            return jsonify({'error': 'Document processor non disponible'}), 500
        
        if len(extracted_text) < 50:
            return jsonify({'error': 'Document trop court ou vide'}), 400
        
        # 3. Analyser le contenu pour identifier le sujet
        print("🔍 Analyse du sujet avec Gemini...")
        subject_prompt = f"""Analyse ce texte et identifie le sujet principal en quelques mots-clés pertinents pour la Data Science.

Texte:
{extracted_text[:1500]}

Réponds UNIQUEMENT avec 3-5 mots-clés séparés par des virgules (ex: machine learning, régression, python).
Ne donne pas d'explication, juste les mots-clés."""
        
        subject_response = gemini_model.generate_content(subject_prompt)
        keywords = extract_gemini_response(subject_response).strip()
        print(f"🏷️  Mots-clés identifiés : {keywords}")
        
        # 4. Chercher des cours pertinents dans data/course_materials/
        relevant_courses = []
        if gemini_assistant:
            print("📚 Recherche de cours pertinents...")
            try:
                relevant_chunks = gemini_assistant.find_relevant_chunks(
                    query=keywords,
                    top_k=5
                )
                
                # Dédupliquer par doc_id
                seen_docs = set()
                for chunk in relevant_chunks:
                    doc_id = chunk['doc_id']
                    if doc_id not in seen_docs:
                        relevant_courses.append({
                            'doc_id': doc_id,
                            'title': chunk['title'],
                            'level': chunk['level'],
                            'category': chunk['category'],
                            'file_path': chunk['file_path'],
                            'relevance': round(chunk['similarity'] * 100, 1),
                            'content_preview': chunk['content'][:300] + '...'
                        })
                        seen_docs.add(doc_id)
                
                print(f"✅ {len(relevant_courses)} cours pertinents trouvés")
            except Exception as e:
                print(f"⚠️  Erreur recherche de cours : {e}")
        
        # 5. Générer l'explication avec Gemini + références aux cours
        print("🤖 Génération de l'explication avec Gemini...")
        
        if relevant_courses:
            # Construire le contexte avec les cours trouvés
            context_parts = []
            for i, course in enumerate(relevant_courses[:3], 1):
                context_parts.append(
                    f"[Cours {i}: {course['title']} - {course['level']}/{course['category']} - Pertinence: {course['relevance']}%]\n"
                    f"{course['content_preview']}"
                )
            
            context = "\n\n---\n\n".join(context_parts)
            
            explanation_prompt = f"""Tu es un assistant pédagogique expert en Data Science pour l'université AMU.

DOCUMENT UPLOADÉ PAR L'ÉTUDIANT:
{extracted_text[:3000]}

COURS DE RÉFÉRENCE DISPONIBLES DANS LA BASE AMU:
{context}

TÂCHE:
1. Explique le contenu du document uploadé de manière claire et pédagogique
2. Fais des liens explicites avec les cours de référence AMU mentionnés ci-dessus
3. Structure ta réponse avec des sections claires (utilise des titres avec **)
4. Cite les cours AMU pertinents (ex: "Selon le cours Machine Learning M1...")
5. Ajoute des exemples concrets si pertinent
6. Si le document traite d'un sujet similaire à un cours AMU, mentionne-le

EXPLICATION DÉTAILLÉE:"""
        else:
            explanation_prompt = f"""Tu es un assistant pédagogique expert en Data Science pour l'université AMU.

DOCUMENT UPLOADÉ PAR L'ÉTUDIANT:
{extracted_text[:3000]}

TÂCHE:
1. Explique le contenu de ce document de manière claire et pédagogique
2. Structure ta réponse avec des sections claires (utilise des titres avec **)
3. Ajoute des exemples concrets si pertinent
4. Indique que ce sujet n'est pas directement couvert dans les cours AMU disponibles

EXPLICATION DÉTAILLÉE:"""
        
        explanation_response = gemini_model.generate_content(
            explanation_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048
            )
        )
        explanation = extract_gemini_response(explanation_response)
        print("✅ Explication générée")
        
        # 6. Générer un résumé court
        print("📝 Génération du résumé...")
        summary_prompt = f"""Résume en 2-3 phrases claires le contenu principal de ce document:

{extracted_text[:2000]}

Résumé concis:"""
        
        summary_response = gemini_model.generate_content(summary_prompt)
        summary = extract_gemini_response(summary_response).strip()
        
        # 7. Retourner la réponse complète
        response_data = {
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'keywords': keywords,
            'summary': summary,
            'explanation': explanation,
            'relevant_courses': relevant_courses,
            'has_course_references': len(relevant_courses) > 0,
            'text_length': len(extracted_text),
            'text_preview': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text
        }
        
        print(f"✅ Réponse complète générée pour {filename}")
        return jsonify(response_data)
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/<file_id>', methods=['POST'])
def process_document(file_id):
    """Traite un document uploadé pour générer un podcast."""
    try:
        data = request.json
        options = data.get('options', {})
        
        # Récupérer le fichier
        upload_folder = Path(app.config['UPLOAD_FOLDER'])
        file_path = None
        
        for file in upload_folder.glob(f"{file_id}_*"):
            file_path = file
            break
        
        if not file_path:
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        # Extraire le texte
        if document_processor:
            text = document_processor.process_document(str(file_path))
        else:
            return jsonify({'error': 'Document processor non disponible'}), 500
        
        # Générer le script audio
        if script_generator:
            script = script_generator.generate_script(
                text,
                style=options.get('style', 'educational'),
                duration_target=options.get('duration', 10)
            )
        else:
            script = text
        
        # Générer l'audio
        if audio_generator:
            audio_path = audio_generator.generate_audio(
                script,
                output_dir='generated_podcasts/audio_files',
                voice=options.get('voice', 'default')
            )
        else:
            return jsonify({'error': 'Audio generator non disponible'}), 500
        
        # Sauvegarder les métadonnées
        metadata = {
            'file_id': file_id,
            'original_filename': file_path.name,
            'generated_at': datetime.now().isoformat(),
            'script_length': len(script),
            'audio_path': str(audio_path),
            'options': options
        }
        
        metadata_path = Path('generated_podcasts/metadata') / f"{file_id}_metadata.json"
        import json
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'audio_url': f'/api/audio/{file_id}',
            'script': script,
            'metadata': metadata
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio/<file_id>')
def get_audio(file_id):
    """Récupère le fichier audio généré."""
    try:
        audio_folder = Path('generated_podcasts/audio_files')
        
        for audio_file in audio_folder.glob(f"*{file_id}*"):
            return send_file(
                str(audio_file),
                mimetype='audio/mpeg',
                as_attachment=False
            )
        
        return jsonify({'error': 'Fichier audio non trouvé'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ROUTES GEMINI AI ASSISTANT
# ============================================================================

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    Endpoint pour poser une question à l'assistant Gemini.
    
    Body JSON:
    {
        "question": "Qu'est-ce qu'un CNN ?",
        "level": "M2",  // Optionnel: M1 ou M2
        "include_sources": true
    }
    """
    if not gemini_assistant:
        return jsonify({'error': 'Assistant Gemini non disponible'}), 503
    
    try:
        data = request.json
        question = data.get('question')
        level = data.get('level')
        include_sources = data.get('include_sources', True)
        
        if not question:
            return jsonify({'error': 'Question requise'}), 400
        
        print(f"❓ Question reçue : {question}")
        
        # Obtenir la réponse avec références aux cours
        result = gemini_assistant.answer_question(
            question=question,
            level=level,
            include_sources=include_sources
        )
        
        print(f"✅ Réponse générée avec {len(result['sources'])} sources")
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': result['answer'],
            'sources': result['sources'],
            'has_course_references': result['has_course_references'],
            'relevant_courses': result.get('relevant_courses', []),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_with_assistant():
    """
    Endpoint de chat conversationnel avec l'assistant.
    """
    if not gemini_assistant:
        return jsonify({'error': 'Assistant Gemini non disponible'}), 503
    
    try:
        data = request.json
        message = data.get('message')
        conversation_id = data.get('conversation_id', generate_unique_id())
        
        if not message:
            return jsonify({'error': 'Message requis'}), 400
        
        # Pour l'instant, traiter comme une question simple
        result = gemini_assistant.answer_question(
            question=message,
            include_sources=True
        )
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'message': message,
            'response': result['answer'],
            'sources': result['sources'],
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/explain-topic', methods=['POST'])
def explain_topic():
    """
    Explique un sujet spécifique en utilisant les cours comme référence.
    
    Body JSON:
    {
        "topic": "Réseaux de neurones convolutifs",
        "level": "M2",
        "detail_level": "detailed"  // simple, detailed, expert
    }
    """
    if not gemini_model:
        return jsonify({'error': 'Gemini API non configurée'}), 503
    
    try:
        data = request.json
        topic = data.get('topic')
        level = data.get('level')
        detail_level = data.get('detail_level', 'detailed')
        
        if not topic:
            return jsonify({'error': 'Topic requis'}), 400
        
        print(f"📖 Explication demandée : {topic} (niveau: {detail_level})")
        
        # Chercher des cours pertinents
        relevant_courses = []
        if gemini_assistant:
            relevant_chunks = gemini_assistant.find_relevant_chunks(
                query=topic,
                top_k=3,
                level=level
            )
            
            seen_docs = set()
            for chunk in relevant_chunks:
                doc_id = chunk['doc_id']
                if doc_id not in seen_docs:
                    relevant_courses.append({
                        'title': chunk['title'],
                        'level': chunk['level'],
                        'category': chunk['category'],
                        'content': chunk['content'][:500]
                    })
                    seen_docs.add(doc_id)
        
        # Construire le prompt selon le niveau de détail
        detail_instructions = {
            'simple': "Explique de manière simple et accessible, comme à un débutant. Utilise des analogies.",
            'detailed': "Explique de manière détaillée avec des exemples concrets et des formules si nécessaire.",
            'expert': "Explique de manière technique et approfondie, avec les détails mathématiques et les nuances importantes."
        }
        
        if relevant_courses:
            context = "\n\n".join([
                f"Extrait du cours '{course['title']}' ({course['level']}/{course['category']}):\n{course['content']}"
                for course in relevant_courses
            ])
            
            prompt = f"""Tu es un professeur expert en Data Science à l'université AMU.

SUJET À EXPLIQUER: {topic}

EXTRAITS DES COURS AMU PERTINENTS:
{context}

INSTRUCTIONS:
{detail_instructions.get(detail_level, detail_instructions['detailed'])}

Structure ta réponse ainsi:
1. Définition : Qu'est-ce que c'est ?
2. Principe de fonctionnement : Comment ça marche ?
3. Applications : À quoi ça sert ?
4. Exemples concrets
5. Lien avec les cours AMU : Mentionne explicitement les cours pertinents

EXPLICATION:"""
        else:
            prompt = f"""Tu es un professeur expert en Data Science.

SUJET À EXPLIQUER: {topic}

INSTRUCTIONS:
{detail_instructions.get(detail_level, detail_instructions['detailed'])}

Structure ta réponse ainsi:
1. Définition : Qu'est-ce que c'est ?
2. Principe de fonctionnement : Comment ça marche ?
3. Applications : À quoi ça sert ?
4. Exemples concrets

Note: Ce sujet n'est pas directement couvert dans les cours AMU disponibles.

EXPLICATION:"""
        
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048
            )
        )
        
        return jsonify({
            'success': True,
            'topic': topic,
            'detail_level': detail_level,
            'explanation': extract_gemini_response(response),
            'relevant_courses': [
                {'title': c['title'], 'level': c['level'], 'category': c['category']}
                for c in relevant_courses
            ],
            'has_course_references': len(relevant_courses) > 0
        })
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ROUTES GESTION DES COURS
# ============================================================================

@app.route('/api/courses')
def list_courses():
    """Liste tous les cours indexés."""
    if not course_indexer:
        return jsonify({'error': 'Course indexer non disponible'}), 503
    
    try:
        documents = course_indexer.get_all_documents()
        
        # Organiser par niveau et catégorie
        organized = {
            'M1': {},
            'M2': {}
        }
        
        for doc in documents:
            level = doc['level']
            category = doc['category']
            
            if level not in organized:
                organized[level] = {}
            
            if category not in organized[level]:
                organized[level][category] = []
            
            organized[level][category].append(doc)
        
        return jsonify({
            'success': True,
            'total_courses': len(documents),
            'courses': documents,
            'organized': organized
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/search', methods=['POST'])
def search_courses():
    """
    Recherche dans les cours.
    
    Body JSON:
    {
        "query": "machine learning",
        "level": "M1",  // Optionnel
        "category": "machine_learning"  // Optionnel
    }
    """
    if not course_indexer:
        return jsonify({'error': 'Course indexer non disponible'}), 503
    
    try:
        data = request.json
        query = data.get('query')
        level = data.get('level')
        category = data.get('category')
        
        if not query:
            return jsonify({'error': 'Query requise'}), 400
        
        results = course_indexer.search_documents(
            query=query,
            level=level,
            category=category
        )
        
        return jsonify({
            'success': True,
            'query': query,
            'filters': {
                'level': level,
                'category': category
            },
            'results_count': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<doc_id>')
def get_course_details(doc_id):
    """Récupère les détails d'un cours spécifique."""
    if not course_indexer:
        return jsonify({'error': 'Course indexer non disponible'}), 503
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('database/amu_courses.db')
        cursor = conn.cursor()
        
        # Récupérer les informations du document
        cursor.execute('''
        SELECT d.doc_id, d.file_path, d.level, d.category, d.filename,
               d.extracted_title, d.page_count, d.indexed_at,
               m.keywords, m.topics, m.difficulty_level, m.estimated_duration_min
        FROM documents d
        LEFT JOIN document_metadata m ON d.doc_id = m.doc_id
        WHERE d.doc_id = ?
        ''', (doc_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        # Récupérer les chunks
        cursor.execute('''
        SELECT chunk_id, content, page_number
        FROM document_chunks
        WHERE doc_id = ?
        ORDER BY chunk_index
        LIMIT 5
        ''', (doc_id,))
        
        chunks = cursor.fetchall()
        conn.close()
        
        course_details = {
            'doc_id': row[0],
            'file_path': row[1],
            'level': row[2],
            'category': row[3],
            'filename': row[4],
            'title': row[5],
            'page_count': row[6],
            'indexed_at': row[7],
            'keywords': row[8].split(',') if row[8] else [],
            'topics': row[9].split(',') if row[9] else [],
            'difficulty': row[10],
            'estimated_duration_min': row[11],
            'content_preview': [
                {
                    'chunk_id': chunk[0],
                    'content': chunk[1][:300] + '...' if len(chunk[1]) > 300 else chunk[1],
                    'page': chunk[2]
                }
                for chunk in chunks
            ]
        }
        
        return jsonify({
            'success': True,
            'course': course_details
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<doc_id>/download')
def download_course(doc_id):
    """Télécharge le PDF d'un cours."""
    try:
        import sqlite3
        
        conn = sqlite3.connect('database/amu_courses.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT file_path, filename
        FROM documents
        WHERE doc_id = ?
        ''', (doc_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print(f"❌ Cours non trouvé : {doc_id}")
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        # Récupérer le chemin et le nom du fichier
        file_path_str = row[0]
        filename = row[1]
        
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG TÉLÉCHARGEMENT")
        print(f"{'='*60}")
        print(f"doc_id: {doc_id}")
        print(f"file_path (DB): {file_path_str}")
        print(f"filename (DB): {filename}")
        print(f"Current working dir: {os.getcwd()}")
        
        # Essayer plusieurs chemins possibles
        possible_paths = []
        
        # 1. Chemin direct depuis la DB
        if file_path_str:
            possible_paths.append(Path(file_path_str))
        
        # 2. Chemin relatif depuis data/course_materials
        possible_paths.append(Path('data/course_materials') / filename)
        
        # 3. Chemin depuis .env
        course_materials_path = os.getenv('COURSE_MATERIALS_PATH', 'data/course_materials')
        possible_paths.append(Path(course_materials_path) / filename)
        
        # 4. Chercher dans tous les sous-dossiers de data/course_materials
        course_materials_dir = Path('data/course_materials')
        if course_materials_dir.exists():
            for pdf_file in course_materials_dir.rglob(filename):
                possible_paths.append(pdf_file)
                break
        
        # Trouver le premier chemin qui existe
        file_path = None
        for i, path in enumerate(possible_paths, 1):
            abs_path = path.absolute()
            print(f"Essai {i}: {abs_path}")
            print(f"  Existe: {path.exists()}")
            if path.exists() and path.is_file():
                file_path = path
                print(f"  ✅ Trouvé !")
                break
        
        print(f"{'='*60}\n")
        
        if not file_path:
            # Lister les fichiers disponibles dans data/course_materials pour debug
            if course_materials_dir.exists():
                print(f"📁 Fichiers PDF dans {course_materials_dir.absolute()}:")
                for f in list(course_materials_dir.rglob('*.pdf'))[:10]:
                    print(f"  - {f.name}")
            
            return jsonify({
                'error': 'Fichier PDF introuvable',
                'file_path_in_db': file_path_str,
                'filename': filename,
                'paths_tested': [str(p.absolute()) for p in possible_paths],
                'current_dir': os.getcwd()
            }), 404
        
        print(f"✅ Téléchargement de : {file_path.absolute()}")
        
        return send_file(
            str(file_path.absolute()),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        import traceback
        print(f"❌ Erreur lors du téléchargement :")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/reindex', methods=['POST'])
def reindex_courses():
    """Réindexe tous les cours (utile après ajout de nouveaux PDFs)."""
    if not course_indexer:
        return jsonify({'error': 'Course indexer non disponible'}), 503
    
    try:
        print("🔄 Début de la réindexation...")
        stats = course_indexer.scan_and_index_all()
        
        # Recréer le cache d'embeddings
        if gemini_assistant:
            print("🔄 Recréation du cache d'embeddings...")
            gemini_assistant._create_embeddings_cache()
            
            # Sauvegarder le cache
            import numpy as np
            cache_path = Path('database/embeddings_cache.npz')
            np.savez(
                cache_path,
                embeddings=gemini_assistant.chunk_embeddings,
                chunk_data=np.array(gemini_assistant.chunk_data, dtype=object)
            )
            print("✅ Cache d'embeddings sauvegardé")
        
        return jsonify({
            'success': True,
            'message': 'Réindexation terminée',
            'stats': stats
        })
    
    except Exception as e:
        print(f"❌ Erreur réindexation : {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ROUTES QUIZ
# ============================================================================

@app.route('/api/quiz/generate/<doc_id>')
def generate_quiz(doc_id):
    """
    Génère un quiz pour un cours spécifique.
    
    Query params:
    - num: nombre de questions (défaut: 5)
    """
    if not gemini_assistant:
        return jsonify({'error': 'Assistant Gemini non disponible'}), 503
    
    try:
        num_questions = request.args.get('num', 5, type=int)
        
        quiz = gemini_assistant.generate_quiz_from_course(
            doc_id=doc_id,
            num_questions=num_questions
        )
        
        if not quiz:
            return jsonify({'error': 'Impossible de générer le quiz'}), 500
        
        return jsonify({
            'success': True,
            'doc_id': doc_id,
            'num_questions': len(quiz),
            'quiz': quiz
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/custom', methods=['POST'])
def generate_custom_quiz():
    """
    Génère un quiz personnalisé basé sur un sujet.
    
    Body JSON:
    {
        "topic": "Réseaux de neurones convolutifs",
        "level": "M2",
        "num_questions": 5,
        "difficulty": "intermediate"
    }
    """
    if not gemini_assistant:
        return jsonify({'error': 'Assistant Gemini non disponible'}), 503
    
    try:
        data = request.json
        topic = data.get('topic')
        level = data.get('level')
        num_questions = data.get('num_questions', 5)
        difficulty = data.get('difficulty', 'intermediate')
        
        if not topic:
            return jsonify({'error': 'Topic requis'}), 400
        
        # Trouver les chunks pertinents
        relevant_chunks = gemini_assistant.find_relevant_chunks(
            query=topic,
            top_k=3,
            level=level
        )
        
        if not relevant_chunks:
            return jsonify({
                'error': 'Aucun contenu pertinent trouvé pour ce sujet'
            }), 404
        
        # Utiliser le premier document pertinent
        doc_id = relevant_chunks[0]['doc_id']
        
        quiz = gemini_assistant.generate_quiz_from_course(
            doc_id=doc_id,
            num_questions=num_questions
        )
        
        return jsonify({
            'success': True,
            'topic': topic,
            'based_on': relevant_chunks[0]['title'],
            'quiz': quiz
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/from-upload/<file_id>', methods=['POST'])
def generate_quiz_from_upload(file_id):
    """
    Génère un quiz à partir d'un document uploadé.
    
    Body JSON:
    {
        "num_questions": 5,
        "difficulty": "intermediate"
    }
    """
    if not gemini_model:
        return jsonify({'error': 'Gemini API non configurée'}), 503
    
    try:
        data = request.json or {}
        num_questions = data.get('num_questions', 5)
        difficulty = data.get('difficulty', 'intermediate')
        
        # Récupérer le fichier
        upload_folder = Path(app.config['UPLOAD_FOLDER'])
        file_path = None
        
        for file in upload_folder.glob(f"{file_id}_*"):
            file_path = file
            break
        
        if not file_path:
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        # Extraire le texte
        if document_processor:
            text = document_processor.process_document(str(file_path))
        else:
            return jsonify({'error': 'Document processor non disponible'}), 500
        
        # Générer le quiz avec Gemini
        quiz_prompt = f"""Génère {num_questions} questions à choix multiples basées sur ce contenu.
Difficulté: {difficulty}

CONTENU:
{text[:3000]}

Format JSON strict (sans texte supplémentaire):
[
  {{
    "question": "Question claire et précise",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option correcte",
    "explanation": "Explication détaillée",
    "difficulty": "{difficulty}"
  }}
]"""
        
        response = gemini_model.generate_content(quiz_prompt)
        response_text = extract_gemini_response(response)
        
        # Parser le JSON
        import json
        import re
        
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            quiz = json.loads(json_match.group())
            return jsonify({
                'success': True,
                'file_id': file_id,
                'num_questions': len(quiz),
                'quiz': quiz
            })
        else:
            return jsonify({'error': 'Impossible de parser le quiz généré'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ROUTES MOBILE
# ============================================================================

@app.route('/mobile/create-session', methods=['POST'])
def create_mobile_session():
    """Crée une nouvelle session mobile et génère un QR code."""
    if not sync_manager or not qr_generator:
        return jsonify({'error': 'Services mobiles non disponibles'}), 503
    
    try:
        data = request.json or {}
        user_id = data.get('user_id', 'anonymous')
        device_info = data.get('device_info', {})
        
        # Créer la session
        session_id = sync_manager.create_session(user_id, device_info)
        
        # Obtenir l'IP locale
        local_ip = get_local_ip()
        base_url = f"http://{local_ip}:5000"
        
        print(f"📱 Génération QR Code - IP locale: {local_ip}")
        print(f"📱 Base URL: {base_url}")
        
        # Générer le QR code
        qr_path = qr_generator.generate_session_qr(session_id, base_url)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'qr_code_url': f'/static/qr_codes/{os.path.basename(qr_path)}',
            'join_url': f'{base_url}/mobile/join?session={session_id}',
            'local_ip': local_ip
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/mobile/join')
def join_session():
    """Page de connexion mobile via QR code."""
    session_id = request.args.get('session')
    
    if not session_id:
        return "Session invalide", 400
    
    if not sync_manager:
        return "Service mobile non disponible", 503
    
    session_state = sync_manager.get_session_state(session_id)
    
    if not session_state:
        return "Session introuvable", 404
    
    return render_template('mobile/mobile_player.html', session=session_state)

@app.route('/mobile/sync-position', methods=['POST'])
def sync_audio_position():
    """Synchronise la position de lecture audio."""
    if not sync_manager:
        return jsonify({'error': 'Service mobile non disponible'}), 503
    
    try:
        data = request.json
        session_id = data.get('session_id')
        position = data.get('position', 0)
        
        sync_manager.sync_audio_position(session_id, position)
        
        # Notifier les autres appareils via WebSocket
        socketio.emit('audio_sync', {
            'position': position
        }, room=session_id)
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/mobile/session/<session_id>')
def get_session_state(session_id):
    """Récupère l'état actuel d'une session."""
    if not sync_manager:
        return jsonify({'error': 'Service mobile non disponible'}), 503
    
    try:
        session_state = sync_manager.get_session_state(session_id)
        
        if not session_state:
            return jsonify({'error': 'Session non trouvée'}), 404
        
        return jsonify({
            'success': True,
            'session': session_state
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Gère la connexion WebSocket."""
    print(f"✅ Client connecté: {request.sid}")
    emit('connected', {'message': 'Connexion établie', 'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Gère la déconnexion WebSocket."""
    print(f"❌ Client déconnecté: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    """Gère la connexion d'un appareil à une session."""
    session_id = data.get('session_id')
    
    if not session_id:
        emit('error', {'message': 'Session ID requis'})
        return
    
    join_room(session_id)
    
    print(f"📱 Client {request.sid} a rejoint la session {session_id}")
    
    emit('session_joined', {
        'message': 'Connecté à la session',
        'session_id': session_id,
        'sid': request.sid
    })
    
    # Notifier les autres participants
    emit('user_joined', {
        'sid': request.sid,
        'timestamp': datetime.now().isoformat()
    }, room=session_id, include_self=False)

@socketio.on('leave_session')
def handle_leave_session(data):
    """Gère la déconnexion d'une session."""
    session_id = data.get('session_id')
    
    if not session_id:
        return
    
    leave_room(session_id)
    
    print(f"📱 Client {request.sid} a quitté la session {session_id}")
    
    # Notifier les autres participants
    emit('user_left', {
        'sid': request.sid,
        'timestamp': datetime.now().isoformat()
    }, room=session_id)

@socketio.on('submit_quiz_answer')
def handle_quiz_answer(data):
    """Traite une réponse de quiz soumise depuis mobile."""
    session_id = data.get('session_id')
    quiz_id = data.get('quiz_id')
    answer = data.get('answer')
    
    # TODO: Implémenter la logique de vérification de la réponse
    is_correct = True  # À calculer
    
    emit('quiz_result', {
        'quiz_id': quiz_id,
        'correct': is_correct,
        'explanation': "Explication de la réponse...",
        'timestamp': datetime.now().isoformat()
    }, room=session_id)

@socketio.on('audio_control')
def handle_audio_control(data):
    """Synchronise les contrôles audio entre appareils."""
    session_id = data.get('session_id')
    action = data.get('action')  # play, pause, seek
    position = data.get('position', 0)
    
    print(f"🎵 Audio control: {action} @ {position}s (session: {session_id})")
    
    # Diffuser à tous les appareils de la session sauf l'émetteur
    emit('audio_sync', {
        'action': action,
        'position': position,
        'timestamp': datetime.now().isoformat()
    }, room=session_id, include_self=False)

# ============================================================================
# ROUTES STATIQUES
# ============================================================================

@app.route('/static/qr_codes/<filename>')
def serve_qr_code(filename):
    """Sert les QR codes générés."""
    return send_from_directory('mobile/static/qr_codes', filename)

# ============================================================================
# GESTION DES ERREURS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Gestion des erreurs 404."""
    return jsonify({'error': 'Route non trouvée'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Gestion des erreurs 500."""
    return jsonify({'error': 'Erreur interne du serveur'}), 500

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == '__main__':
    local_ip = get_local_ip()
    
    print("\n" + "="*70)
    print("🚀 DÉMARRAGE DE L'APPLICATION AMU DATA SCIENCE")
    print("="*70)
    print(f"📍 URL locale: http://127.0.0.1:5000")
    print(f"📍 URL réseau: http://{local_ip}:5000")
    print(f"📱 API: http://{local_ip}:5000/api/")
    print(f"🤖 Gemini Model: {'✅ Actif' if gemini_model else '❌ Inactif'}")
    print(f"🤖 Gemini Assistant: {'✅ Actif' if gemini_assistant else '❌ Actif'}")
    print(f"📚 Course Indexer: {'✅ Actif' if course_indexer else '❌ Inactif'}")
    print(f"📱 Mobile Sync: {'✅ Actif' if sync_manager else '❌ Inactif'}")
    print("="*70)
    print("\n📋 ENDPOINTS PRINCIPAUX:")
    print("  POST /api/upload-and-explain - Upload + Explication Gemini")
    print("  POST /api/ask - Poser une question")
    print("  POST /api/explain-topic - Expliquer un sujet")
    print("  GET  /api/courses - Lister les cours")
    print("  GET  /api/courses/<doc_id>/download - Télécharger un PDF")
    print("  POST /api/quiz/from-upload/<file_id> - Quiz depuis upload")
    print("="*70)
    print(f"\n📱 Pour accès mobile, scannez le QR code généré avec l'IP: {local_ip}")
    print("="*70 + "\n")
    
    # Lancer l'application
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        allow_unsafe_werkzeug=True,
        use_reloader=False
    )

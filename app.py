from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv

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
    gemini_assistant = GeminiRAGAssistant(
        course_index_db='database/course_index.db'
    )
    print("✅ GeminiRAGAssistant initialisé")
except Exception as e:
    print(f"⚠️  Erreur GeminiRAGAssistant: {e}")
    gemini_assistant = None

try:
    course_indexer = CourseIndexer(
        course_materials_path=os.getenv('COURSE_MATERIALS_PATH', 'data/course_materials'),
        index_db_path='database/course_index.db'
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
            'gemini_assistant': gemini_assistant is not None,
            'course_indexer': course_indexer is not None
        }
    })

# ============================================================================
# ROUTES UPLOAD ET TRAITEMENT DE DOCUMENTS
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload et traitement d'un document."""
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
        
        # Obtenir la réponse avec références aux cours
        result = gemini_assistant.answer_question(
            question=question,
            level=level,
            include_sources=include_sources
        )
        
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_with_assistant():
    """
    Endpoint de chat conversationnel avec l'assistant.
    Maintient un historique de conversation.
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
        # TODO: Implémenter la gestion de l'historique de conversation
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
        
        conn = sqlite3.connect('database/course_index.db')
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

@app.route('/api/courses/reindex', methods=['POST'])
def reindex_courses():
    """Réindexe tous les cours (utile après ajout de nouveaux PDFs)."""
    if not course_indexer:
        return jsonify({'error': 'Course indexer non disponible'}), 503
    
    try:
        stats = course_indexer.scan_and_index_all()
        
        # Recréer le cache d'embeddings
        if gemini_assistant:
            gemini_assistant._create_embeddings_cache()
            
            # Sauvegarder le cache
            import numpy as np
            cache_path = Path('database/embeddings_cache.npz')
            np.savez(
                cache_path,
                embeddings=gemini_assistant.chunk_embeddings,
                chunk_data=np.array(gemini_assistant.chunk_data, dtype=object)
            )
        
        return jsonify({
            'success': True,
            'message': 'Réindexation terminée',
            'stats': stats
        })
    
    except Exception as e:
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
        
        # Générer le QR code
        base_url = request.host_url.rstrip('/')
        qr_path = qr_generator.generate_session_qr(session_id, base_url)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'qr_code_url': f'/static/qr_codes/{os.path.basename(qr_path)}',
            'join_url': f'{base_url}/mobile/join?session={session_id}'
        })
    
    except Exception as e:
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
    # Pour l'instant, réponse simulée
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
    print("\n" + "="*70)
    print("🚀 DÉMARRAGE DE L'APPLICATION AMU DATA SCIENCE")
    print("="*70)
    print(f"📍 URL: http://localhost:5000")
    print(f"📱 API: http://localhost:5000/api/")
    print(f"🤖 Gemini Assistant: {'✅ Actif' if gemini_assistant else '❌ Inactif'}")
    print(f"📚 Course Indexer: {'✅ Actif' if course_indexer else '❌ Inactif'}")
    print(f"📱 Mobile Sync: {'✅ Actif' if sync_manager else '❌ Inactif'}")
    print("="*70 + "\n")
    
    # Lancer l'application
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        allow_unsafe_werkzeug=True  # Pour le développement uniquement
    )

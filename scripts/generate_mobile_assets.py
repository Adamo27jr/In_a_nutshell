"""
Script pour générer les assets mobiles (QR codes, métadonnées, etc.).
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Ajouter le dossier parent au path
sys.path.append(str(Path(__file__).parent.parent))

from src.qr_code_generator import QRCodeGenerator
from src.course_indexer import CourseIndexer
from src.mobile_sync_manager import MobileSyncManager

def generate_qr_codes_for_all_courses(
    base_url: str = 'http://localhost:5000',
    output_dir: str = 'mobile/static/qr_codes'
):
    """
    Génère des QR codes pour tous les cours indexés.
    
    Args:
        base_url: URL de base de l'application
        output_dir: Dossier de sortie pour les QR codes
    """
    print("\n📱 Génération des QR codes pour tous les cours...")
    
    # Initialiser les gestionnaires
    qr_generator = QRCodeGenerator(output_dir=output_dir)
    indexer = CourseIndexer(
        course_materials_path='data/course_materials',
        index_db_path='database/amu_courses.db'
    )
    
    # Récupérer tous les cours
    courses = indexer.get_all_documents()
    
    if not courses:
        print("⚠️  Aucun cours trouvé dans la base de données")
        print("💡 Exécutez d'abord : python scripts/populate_database.py")
        return
    
    print(f"📚 {len(courses)} cours trouvés\n")
    
    generated_count = 0
    qr_metadata = []
    
    for course in courses:
        try:
            # Générer le QR code
            qr_path = qr_generator.generate_course_qr(
                doc_id=course['doc_id'],
                base_url=base_url,
                title=course['title']
            )
            
            # Sauvegarder les métadonnées
            qr_metadata.append({
                'doc_id': course['doc_id'],
                'title': course['title'],
                'level': course['level'],
                'category': course['category'],
                'qr_code_path': qr_path,
                'url': f"{base_url}/api/courses/{course['doc_id']}",
                'generated_at': datetime.now().isoformat()
            })
            
            generated_count += 1
            print(f"✅ {course['level']}/{course['category']}: {course['title'][:50]}...")
            
        except Exception as e:
            print(f"❌ Erreur pour {course['doc_id']}: {e}")
    
    # Sauvegarder les métadonnées
    metadata_path = Path(output_dir) / 'qr_codes_metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(qr_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {generated_count} QR codes générés")
    print(f"📍 Dossier : {output_dir}")
    print(f"📄 Métadonnées : {metadata_path}")

def generate_demo_sessions(count: int = 5):
    """
    Génère des sessions de démonstration avec QR codes.
    
    Args:
        count: Nombre de sessions à créer
    """
    print(f"\n📱 Génération de {count} sessions de démonstration...")
    
    sync_manager = MobileSyncManager(database_path='database/amu_courses.db')
    qr_generator = QRCodeGenerator(output_dir='mobile/static/qr_codes')
    
    sessions_metadata = []
    
    devices = [
        {'type': 'smartphone', 'os': 'iOS'},
        {'type': 'tablet', 'os': 'Android'},
        {'type': 'smartphone', 'os': 'Android'},
        {'type': 'desktop', 'os': 'Windows'},
        {'type': 'tablet', 'os': 'iOS'}
    ]
    
    for i in range(count):
        # Créer la session
        device_info = devices[i % len(devices)]
        session_id = sync_manager.create_session(
            user_id=f'demo_user_{i+1}',
            device_info=device_info
        )
        
        # Générer le QR code
        qr_path = qr_generator.generate_session_qr(
            session_id=session_id,
            base_url='http://localhost:5000',
            filename=f'demo_session_{i+1}.png'
        )
        
        # Sauvegarder les métadonnées
        session_data = {
            'session_id': session_id,
            'user_id': f'demo_user_{i+1}',
            'device_type': device_info['type'],
            'device_os': device_info['os'],
            'qr_code_path': qr_path,
            'join_url': f'http://localhost:5000/mobile/join?session={session_id}',
            'created_at': datetime.now().isoformat()
        }
        
        sessions_metadata.append(session_data)
        
        print(f"✅ Session {i+1}: {session_id[:12]}... ({device_info['type']}/{device_info['os']})")
    
    # Sauvegarder les métadonnées
    metadata_path = Path('mobile/static/qr_codes') / 'demo_sessions.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(sessions_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {count} sessions de démonstration créées")
    print(f"📄 Métadonnées : {metadata_path}")

def generate_mobile_html_index():
    """
    Génère une page HTML d'index pour tester les QR codes.
    """
    print("\n📄 Génération de la page d'index HTML...")
    
    # Charger les métadonnées des QR codes
    qr_metadata_path = Path('mobile/static/qr_codes/qr_codes_metadata.json')
    
    if not qr_metadata_path.exists():
        print("⚠️  Générez d'abord les QR codes avec generate_qr_codes_for_all_courses()")
        return
    
    with open(qr_metadata_path, 'r', encoding='utf-8') as f:
        qr_metadata = json.load(f)
    
    # Générer le HTML
    html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR Codes AMU Data Science</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 40px;
            font-size: 36px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            font-size: 18px;
            color: #333;
            margin-bottom: 10px;
        }
        
        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 5px;
            margin-bottom: 10px;
        }
        
        .badge-m1 {
            background: #4caf50;
            color: white;
        }
        
        .badge-m2 {
            background: #2196f3;
            color: white;
        }
        
        .badge-category {
            background: #f0f0f0;
            color: #666;
        }
        
        .qr-code {
            width: 100%;
            max-width: 250px;
            margin: 15px auto;
            display: block;
            border-radius: 10px;
        }
        
        .url {
            font-size: 12px;
            color: #666;
            word-break: break-all;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        
        .stats {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 40px;
            text-align: center;
        }
        
        .stat-item {
            display: inline-block;
            margin: 0 20px;
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: 700;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 QR Codes AMU Data Science</h1>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">""" + str(len(qr_metadata)) + """</div>
                <div class="stat-label">Cours</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">""" + str(len([c for c in qr_metadata if c['level'] == 'M1'])) + """</div>
                <div class="stat-label">M1</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">""" + str(len([c for c in qr_metadata if c['level'] == 'M2'])) + """</div>
                <div class="stat-label">M2</div>
            </div>
        </div>
        
        <div class="grid">
"""
    
    # Ajouter chaque cours
    for course in qr_metadata:
        qr_filename = Path(course['qr_code_path']).name
        badge_class = 'badge-m1' if course['level'] == 'M1' else 'badge-m2'
        
        html_content += f"""
            <div class="card">
                <h2>{course['title']}</h2>
                <div>
                    <span class="badge {badge_class}">{course['level']}</span>
                    <span class="badge badge-category">{course['category']}</span>
                </div>
                <img src="/static/qr_codes/{qr_filename}" alt="QR Code" class="qr-code">
                <div class="url">{course['url']}</div>
            </div>
"""
    
    html_content += """
        </div>
    </div>
</body>
</html>
"""
    
    # Sauvegarder le fichier
    output_path = Path('mobile/templates/qr_codes_index.html')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Page HTML générée : {output_path}")
    print(f"🌐 Accédez à : http://localhost:5000/mobile/qr-codes")

def create_mobile_config():
    """
    Crée un fichier de configuration pour l'application mobile.
    """
    print("\n⚙️  Génération du fichier de configuration mobile...")
    
    config = {
        'app_name': 'AMU Data Science Mobile',
        'version': '1.0.0',
        'api_base_url': 'http://localhost:5000',
        'websocket_url': 'ws://localhost:5000',
        'features': {
            'audio_sync': True,
            'quiz': True,
            'qr_codes': True,
            'offline_mode': False
        },
        'sync_interval_seconds': 5,
        'max_reconnect_attempts': 5,
        'supported_formats': ['pdf', 'mp3', 'wav'],
        'theme': {
            'primary_color': '#667eea',
            'secondary_color': '#764ba2',
            'accent_color': '#4caf50'
        },
        'generated_at': datetime.now().isoformat()
    }
    
    config_path = Path('mobile/config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuration créée : {config_path}")

def main():
    """Fonction principale."""
    
    print("="*70)
    print("📱 GÉNÉRATION DES ASSETS MOBILES")
    print("="*70)
    
    # 1. Générer les QR codes pour tous les cours
    print("\n🎯 Étape 1 : QR codes des cours")
    generate_qr_codes_for_all_courses(
        base_url='http://localhost:5000',
        output_dir='mobile/static/qr_codes'
    )
    
    # 2. Générer des sessions de démonstration
    print("\n🎯 Étape 2 : Sessions de démonstration")
    generate_demo_sessions(count=5)
    
    # 3. Générer la page HTML d'index
    print("\n🎯 Étape 3 : Page HTML d'index")
    generate_mobile_html_index()
    
    # 4. Créer le fichier de configuration
    print("\n🎯 Étape 4 : Configuration mobile")
    create_mobile_config()
    
    print("\n" + "="*70)
    print("✅ GÉNÉRATION TERMINÉE")
    print("="*70)
    print("\n📂 Assets générés dans :")
    print("   - mobile/static/qr_codes/")
    print("   - mobile/templates/")
    print("   - mobile/config.json")
    print("\n🎯 Prochaines étapes :")
    print("   1. Lancez l'application : python app.py")
    print("   2. Accédez aux QR codes : http://localhost:5000/mobile/qr-codes")
    print("   3. Testez sur mobile en scannant les QR codes")
    print("="*70)

if __name__ == "__main__":
    main()

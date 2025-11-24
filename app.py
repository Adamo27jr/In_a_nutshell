import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime

# Imports locaux
from src.universal_document_processor import UniversalDocumentProcessor
from src.amu_knowledge_base import AMUKnowledgeBase
from src.audio_script_generator import AudioScriptGenerator
from src.audio_generator import AudioGenerator
from src.interactive_quiz_manager import QuizManager

# Configuration
load_dotenv()

st.set_page_config(
    page_title="📚 SnapLearn",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Mobile-Optimized
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 18px;
        font-weight: 600;
        border-radius: 12px;
        margin: 8px 0;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    .streamlit-expanderHeader {
        background-color: #f8f9ff;
        border-radius: 10px;
        font-weight: 600;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialisation des composants (avec cache)
@st.cache_resource
def init_components():
    """Initialise tous les composants de l'application"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY non trouvée dans .env")
        st.stop()
    
    processor = UniversalDocumentProcessor(api_key)
    kb = AMUKnowledgeBase()
    script_gen = AudioScriptGenerator(api_key, kb)
    audio_gen = AudioGenerator()
    quiz_mgr = QuizManager()
    
    return processor, kb, script_gen, audio_gen, quiz_mgr

# Chargement des composants
with st.spinner("🚀 Initialisation de SnapLearn..."):
    processor, kb, script_gen, audio_gen, quiz_mgr = init_components()

# Session state
if 'processed_docs' not in st.session_state:
    st.session_state.processed_docs = []

if 'current_script' not in st.session_state:
    st.session_state.current_script = None

if 'current_audio_path' not in st.session_state:
    st.session_state.current_audio_path = None

# Header
st.title("📚 SnapLearn")
st.caption("Transforme tes documents d'étude en podcasts audio avec quiz interactifs")

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📥 Import", "🎧 Générer Audio", "❓ Quiz"])

# ==================== TAB 1: IMPORT ====================
with tab1:
    st.subheader("📥 Importer un document")
    
    upload_type = st.radio(
        "Type de document",
        ["📄 PDF", "📸 Image"],
        horizontal=True
    )
    
    if upload_type == "📄 PDF":
        st.write("**Upload un fichier PDF**")
        st.caption("Manuel de cours, article scientifique, livre...")
        
        uploaded_file = st.file_uploader(
            "Choisis un PDF",
            type=['pdf'],
            help="Taille max recommandée: 10 MB"
        )
        
        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"📄 **{uploaded_file.name}** ({file_size_mb:.1f} MB)")
            
            temp_path = f"temp_{uploaded_file.name}"
            
            if st.button("🔍 Analyser le PDF", type="primary", use_container_width=True):
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.read())
                
                with st.spinner("📄 Analyse du PDF en cours..."):
                    try:
                        result = processor.process_document(temp_path)
                        
                        st.success("✅ PDF analysé avec succès!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Pages", result['metadata']['total_pages'])
                        with col2:
                            st.metric("Mots", f"{result['total_words']:,}")
                        with col3:
                            st.metric("Durée estimée", f"{result['estimated_duration']:.0f} min")
                        
                        with st.expander("👁️ Aperçu du contenu (3 premières pages)"):
                            for page in result['pages'][:3]:
                                st.markdown(f"**Page {page['page_number']}** ({page['word_count']} mots)")
                                st.text_area(
                                    f"Contenu page {page['page_number']}",
                                    page['text'][:300] + "...",
                                    height=100,
                                    key=f"preview_{page['page_number']}"
                                )
                        
                        if st.button("➕ Ajouter à ma bibliothèque", use_container_width=True):
                            st.session_state.processed_docs.append(result)
                            st.success(f"✅ Document ajouté! Total: {len(st.session_state.processed_docs)}")
                            st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'analyse: {str(e)}")
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
    
    else:  # Image
        st.write("**Upload une image**")
        st.caption("Couverture de livre, page de cours, notes manuscrites, diagramme...")
        
        uploaded_image = st.file_uploader(
            "Choisis une image",
            type=['jpg', 'jpeg', 'png', 'heic'],
            help="Formats supportés: JPG, PNG, HEIC"
        )
        
        if uploaded_image:
            st.image(uploaded_image, caption="Image uploadée", use_container_width=True)
            
            temp_path = f"temp_{uploaded_image.name}"
            
            if st.button("🔍 Analyser l'image", type="primary", use_container_width=True):
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_image.read())
                
                with st.spinner("🖼️ Analyse de l'image en cours..."):
                    try:
                        result = processor.process_document(temp_path)
                        
                        st.success("✅ Image analysée avec succès!")
                        
                        type_labels = {
                            'book_cover': '📚 Couverture de livre',
                            'text_page': '📄 Page de texte',
                            'diagram': '📊 Diagramme/Schéma',
                            'handwritten': '✍️ Notes manuscrites',
                            'other': '📋 Autre'
                        }
                        
                        st.info(f"**Type détecté:** {type_labels.get(result['image_type'], result['image_type'])}")
                        
                        enhanced = result.get('enhanced_metadata', {})
                        
                        if result['image_type'] == 'book_cover':
                            st.markdown("### 📚 Informations du livre")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Titre:** {enhanced.get('title', 'Non détecté')}")
                                st.write(f"**Auteur:** {enhanced.get('author', 'Inconnu')}")
                            with col2:
                                st.write(f"**Genre:** {enhanced.get('genre', 'Inconnu')}")
                                st.write(f"**Difficulté:** {enhanced.get('estimated_difficulty', 'N/A')}")
                            
                            if enhanced.get('themes'):
                                st.write(f"**Thèmes:** {', '.join(enhanced['themes'])}")
                        
                        if result.get('text'):
                            with st.expander("📝 Texte extrait (OCR)"):
                                st.text_area("Contenu", result['text'], height=200)
                                st.caption(f"{result['word_count']} mots extraits")
                        
                        if enhanced.get('key_concepts'):
                            st.write("**🔑 Concepts clés identifiés:**")
                            st.write(", ".join(enhanced['key_concepts']))
                        
                        if st.button("➕ Ajouter à ma bibliothèque", use_container_width=True):
                            st.session_state.processed_docs.append(result)
                            st.success(f"✅ Document ajouté! Total: {len(st.session_state.processed_docs)}")
                            st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'analyse: {str(e)}")
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

                      # ==================== TAB 2: GÉNÉRER AUDIO ====================
with tab2:
    st.subheader("🎧 Générer un Podcast Audio")
    
    if not st.session_state.processed_docs:
        st.warning("⚠️ Importe d'abord un document dans l'onglet **Import**")
        st.info("💡 Upload un PDF ou une image pour commencer")
    else:
        st.success(f"✅ **{len(st.session_state.processed_docs)} document(s)** prêt(s) à être transformé(s) en podcast")
        
        if len(st.session_state.processed_docs) > 1:
            doc_options = []
            for i, doc in enumerate(st.session_state.processed_docs):
                if doc['type'] == 'pdf':
                    label = f"{i+1}. {doc['metadata']['title']} (PDF - {doc['metadata']['total_pages']} pages)"
                else:
                    label = f"{i+1}. Image ({doc['image_type']})"
                doc_options.append(label)
            
            selected_idx = st.selectbox(
                "Sélectionne le document à transformer",
                range(len(doc_options)),
                format_func=lambda i: doc_options[i]
            )
            
            selected_doc = st.session_state.processed_docs[selected_idx]
        else:
            selected_doc = st.session_state.processed_docs[0]
            st.info(f"📄 Document sélectionné: {selected_doc.get('metadata', {}).get('title', 'Document 1')}")
        
        st.markdown("---")
        
        st.markdown("### ⚙️ Paramètres du podcast")
        
        col1, col2 = st.columns(2)
        
        with col1:
            duration = st.slider(
                "⏱️ Durée cible (minutes)",
                min_value=3,
                max_value=15,
                value=5,
                step=1,
                help="Durée approximative du podcast audio"
            )
        
        with col2:
            style = st.selectbox(
                "🎭 Style de narration",
                ["conversational", "academic", "storytelling"],
                format_func=lambda x: {
                    "conversational": "💬 Conversationnel (amical)",
                    "academic": "🎓 Académique (formel)",
                    "storytelling": "📖 Storytelling (narratif)"
                }[x]
            )
        
        st.markdown("---")
        
        if st.button("🎙️ Générer le Podcast", type="primary", use_container_width=True):
            
            with st.spinner("✍️ Génération du script pédagogique..."):
                try:
                    script = script_gen.generate_script(
                        selected_doc,
                        target_duration=duration * 60,
                        style=style
                    )
                    
                    st.session_state.current_script = script
                    st.success("✅ Script généré!")
                    
                except Exception as e:
                    st.error(f"❌ Erreur génération script: {str(e)}")
                    st.stop()
            
            with st.expander("📝 Aperçu du script généré"):
                st.markdown("**Introduction:**")
                st.write(script.get('intro', '')[:200] + "...")
                
                st.markdown("**Contenu principal:**")
                st.write(script.get('main_content', '')[:300] + "...")
                
                st.markdown("**Conclusion:**")
                st.write(script.get('conclusion', '')[:200] + "...")
                
                if script.get('quiz_questions'):
                    st.markdown(f"**Quiz:** {len(script['quiz_questions'])} questions générées")
            
            with st.spinner("🎵 Génération de l'audio (cela peut prendre 1-2 minutes)..."):
                try:
                    audio_path = audio_gen.generate_podcast(script)
                    
                    st.session_state.current_audio_path = audio_path
                    st.success("✅ Podcast audio généré!")
                    
                except Exception as e:
                    st.error(f"❌ Erreur génération audio: {str(e)}")
                    st.stop()
            
            st.markdown("---")
            st.markdown("## 🎉 Ton podcast est prêt!")
            
            st.audio(audio_path)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                file_size = os.path.getsize(audio_path) / (1024 * 1024)
                st.metric("📦 Taille", f"{file_size:.1f} MB")
            
            with col2:
                from pydub import AudioSegment
                audio = AudioSegment.from_mp3(audio_path)
                actual_duration = len(audio) / 1000 / 60
                st.metric("⏱️ Durée", f"{actual_duration:.1f} min")
            
            with col3:
                word_count = script.get('total_word_count', 0)
                st.metric("📝 Mots", f"{word_count}")
            
            with open(audio_path, 'rb') as f:
                st.download_button(
                    "⬇️ Télécharger le MP3",
                    f,
                    file_name=f"snaplearn_podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3",
                    mime="audio/mpeg",
                    use_container_width=True
                )
            
            with st.expander("📄 Transcript complet"):
                full_transcript = script.get('intro', '') + "\n\n" + \
                                script.get('main_content', '') + "\n\n" + \
                                script.get('conclusion', '')
                
                st.markdown(full_transcript)
                
                st.download_button(
                    "⬇️ Télécharger le transcript",
                    full_transcript,
                    file_name="transcript.txt",
                    mime="text/plain"
                )

# ==================== TAB 3: QUIZ ====================
with tab3:
    st.subheader("❓ Quiz Interactif")
    
    if st.session_state.current_script is None:
        st.info("💡 Génère d'abord un podcast dans l'onglet **Générer Audio** pour avoir des questions quiz!")
    else:
        questions = st.session_state.current_script.get('quiz_questions', [])
        
        if not questions:
            st.warning("⚠️ Aucune question quiz n'a été générée pour ce podcast")
            st.info("Essaye de régénérer le podcast avec un document différent")
        else:
            quiz_mgr.render_quiz(questions)

# ==================== SIDEBAR (optionnel) ====================
with st.sidebar:
    st.markdown("### 📊 Statistiques")
    st.metric("Documents traités", len(st.session_state.processed_docs))
    
    if st.session_state.current_audio_path:
        st.metric("Podcasts générés", "1")
    
    st.markdown("---")
    st.markdown("### ℹ️ À propos")
    st.caption("**SnapLearn** v1.0")
    st.caption("Hackathon AMU Data Science 2025")
    st.caption("Construit avec ❤️ et ☕")
    
    st.markdown("---")
    
    if st.button("🗑️ Réinitialiser tout", use_container_width=True):
        st.session_state.processed_docs = []
        st.session_state.current_script = None
        st.session_state.current_audio_path = None
        st.session_state.quiz_state = {'current': 0, 'score': 0, 'answers': [], 'active': False}
        st.rerun()

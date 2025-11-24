-- ============================================================================
-- Schéma de base de données pour AMU Data Science Platform
-- ============================================================================

-- Table principale des cours
CREATE TABLE IF NOT EXISTS courses (
    course_id VARCHAR(20) PRIMARY KEY,
    level VARCHAR(5) NOT NULL,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    professor VARCHAR(100),
    semester VARCHAR(20),
    credits INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des chapitres
CREATE TABLE IF NOT EXISTS chapters (
    chapter_id VARCHAR(30) PRIMARY KEY,
    course_id VARCHAR(20),
    chapter_number INTEGER,
    title VARCHAR(200),
    content_path VARCHAR(500),
    duration_minutes INTEGER,
    difficulty_level VARCHAR(20),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Table des documents indexés
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
);

-- Table des chunks (morceaux de texte pour RAG)
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT,
    chunk_index INTEGER,
    content TEXT,
    page_number INTEGER,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
);

-- Table des métadonnées des documents
CREATE TABLE IF NOT EXISTS document_metadata (
    doc_id TEXT PRIMARY KEY,
    keywords TEXT,
    topics TEXT,
    difficulty_level TEXT,
    estimated_duration_min INTEGER,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
);

-- Table des contenus générés (podcasts, résumés)
CREATE TABLE IF NOT EXISTS generated_content (
    content_id VARCHAR(50) PRIMARY KEY,
    chapter_id VARCHAR(30),
    content_type VARCHAR(30),
    file_path VARCHAR(500),
    duration_seconds INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id)
);

-- Table des sessions utilisateurs
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    device_type VARCHAR(20),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP
);

-- Table de progression utilisateur
CREATE TABLE IF NOT EXISTS user_progress (
    progress_id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50),
    chapter_id VARCHAR(30),
    completion_percentage DECIMAL(5,2),
    audio_position_seconds INTEGER,
    quiz_score DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id),
    FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id)
);

-- Table des quiz
CREATE TABLE IF NOT EXISTS quizzes (
    quiz_id VARCHAR(50) PRIMARY KEY,
    chapter_id VARCHAR(30),
    question_text TEXT,
    question_type VARCHAR(30),
    options TEXT,
    correct_answer VARCHAR(200),
    explanation TEXT,
    difficulty VARCHAR(20),
    FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id)
);

-- Table des réponses utilisateurs aux quiz
CREATE TABLE IF NOT EXISTS quiz_responses (
    response_id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50),
    quiz_id VARCHAR(50),
    user_answer VARCHAR(200),
    is_correct BOOLEAN,
    response_time_seconds INTEGER,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id),
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_documents_level ON documents(level);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_session ON user_progress(session_id);
CREATE INDEX IF NOT EXISTS idx_quiz_chapter ON quizzes(chapter_id);

-- Vue pour les statistiques des cours
CREATE VIEW IF NOT EXISTS course_statistics AS
SELECT 
    d.level,
    d.category,
    COUNT(DISTINCT d.doc_id) as total_documents,
    SUM(d.page_count) as total_pages,
    AVG(m.estimated_duration_min) as avg_duration_minutes
FROM documents d
LEFT JOIN document_metadata m ON d.doc_id = m.doc_id
GROUP BY d.level, d.category;

-- Vue pour la progression globale
CREATE VIEW IF NOT EXISTS user_progress_summary AS
SELECT 
    s.user_id,
    s.session_id,
    COUNT(DISTINCT p.chapter_id) as chapters_started,
    AVG(p.completion_percentage) as avg_completion,
    SUM(p.audio_position_seconds) as total_listening_time_seconds
FROM user_sessions s
LEFT JOIN user_progress p ON s.session_id = p.session_id
GROUP BY s.user_id, s.session_id;

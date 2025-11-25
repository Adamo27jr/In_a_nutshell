## In_a_nutshell - Assistant d'Apprentissage Intelligent

**In_a_nutshell** est un assistant d'étude alimenté par l'IA qui transforme vos cours de Data Science en expérience d'apprentissage interactive. Grâce à la technologie **RAG (Retrieval-Augmented Generation)** et l'**API Gemini de Google**, posez des questions directement à vos documents et obtenez des réponses précises avec sources citées.

### Fonctionnalités Actuelles

- **Chat Intelligent avec vos Cours** : Interrogez 2834+ chunks de cours indexés en langage naturel
- **Recherche Sémantique Avancée** : Réponses contextualisées avec citations de sources
- **Base de Connaissances AMU** : Cours M1/M2 Data Science pré-indexés (Apprentissage, Stats, Deep Learning...)
- **Interface Mobile Optimisée** : Accès via QR code pour réviser en déplacement
- **Accès aux Documents** : Téléchargement direct des PDFs depuis l'interface
- **Quiz Interactifs** : Génération de QCM basés sur vos cours (fonctionnalité de base opérationnelle)

### Axes d'Amélioration Prévus

- **Génération de Podcasts Audio** : Transformation automatique de vos cours en format audio pour l'apprentissage passif
- **Quiz Avancés Auto-Générés** : Amélioration du système actuel avec adaptation au niveau et suivi de progression
- **Système d'Upload Optimisé** : Support multi-format avec OCR et traitement par Gemini Vision

## Équipe

- Adam Belhassan
- Antoine Legendre
- Alex Van Tran Nhieu
- Sabine Mansour
- Lyna Kartout

## Installation

### Prérequis

- Python 3.10+
- Tesseract OCR installé sur votre système
  - **macOS:** `brew install tesseract`
  - **Ubuntu:** `sudo apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng`
  - **Windows:** [Télécharger ici](https://github.com/UB-Mannheim/tesseract/wiki)

# Setup Rapide

## Installation Complète (Copier-Coller par Bloc)

### Windows (PowerShell)

```powershell
# 1. Clonage et navigation
cd Desktop
git clone https://github.com/Adamo27jr/In_a_nutshell
cd In_a_nutshell

# 2. Configuration Python
python --version
python -m venv venv
venv\Scripts\activate

# 3. Installation des dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configuration .env (ouvre le bloc-notes pour édition)
New-Item .env
notepad .env

# 5. Initialisation et lancement
python database/init_database.py
python scripts/index_existing_courses.py
python app.py
```

### Mac / Linux

```bash
# 1. Clonage et navigation
cd ~/Desktop
git clone https://github.com/Adamo27jr/In_a_nutshell
cd In_a_nutshell

# 2. Configuration Python
python3 --version
python3 -m venv venv
source venv/bin/activate

# 3. Installation des dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configuration .env (ouvre nano pour édition)
touch .env
nano .env

# 5. Initialisation et lancement
python database/init_database.py
python scripts/index_existing_courses.py
python app.py
```

---

## Configuration du fichier .env

Ajoutez ce contenu dans votre fichier `.env` :

```env
# API Gemini
GOOGLE_API_KEY=votre_clé_api_gemini_ici

# Configuration Gemini
GEMINI_MODEL=models/gemini-2.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048

# Chemins
COURSE_MATERIALS_PATH=data/course_materials
INDEX_DB_PATH=database/amu_courses.db
VECTOR_STORE_PATH=database/vector_embeddings

# Secret Key
SECRET_KEY=dev-secret-key-change-in-production
```

**Obtenir une clé API :** https://makersuite.google.com/app/apikey

---

## Accès à l'application

Une fois lancée, ouvrez : **http://localhost:5000**

---

---

## ATTENTION : Accès Mobile via QR Code

### Problème Réseau Universitaire

Sur les réseaux Eduroam ou WiFi publics, la communication entre appareils est bloquée par sécurité. Le QR code ne fonctionnera pas directement.

### SOLUTION RECOMMANDÉE : Partage de Connexion

Vous devez activer le partage de connexion de votre téléphone vers votre PC.

python app.py
```

---

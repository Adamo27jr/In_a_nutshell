# In_a_nutshell
1. README.md

Transforme tes documents d'étude (PDFs, couvertures de livres, notes de cours) en podcasts audio avec quiz auto-générés. Construit avec RAG, Gemini Vision AI, et optimisé pour l'apprentissage mobile en déplacement.

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

# 🚀 Setup Rapide

## 📋 Installation Complète (Copier-Coller par Bloc)

### 🪟 Windows (PowerShell)

```powershell
# 1. Clonage et navigation
cd Desktop
git clone https://github.com/votre-username/nom-du-repo.git
cd nom-du-repo

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

### 🍎 Mac / 🐧 Linux

```bash
# 1. Clonage et navigation
cd ~/Desktop
git clone https://github.com/votre-username/nom-du-repo.git
cd nom-du-repo

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

## 🔑 Configuration du fichier .env

Ajoutez ce contenu dans votre fichier `.env` :

```env
# API Gemini
GOOGLE_API_KEY=votre_clé_api_gemini_ici

# Configuration
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
COURSE_MATERIALS_PATH=data/course_materials
INDEX_DB_PATH=database/amu_courses.db
SECRET_KEY=dev-secret-key-change-in-production
```

**📍 Obtenir une clé API :** https://makersuite.google.com/app/apikey

---

## 🌐 Accès à l'application

Une fois lancée, ouvrez : **http://localhost:5000**

---

## 🔄 Relancer plus tard

### Windows
```powershell
cd Desktop\nom-du-repo
venv\Scripts\activate
python app.py
```

### Mac/Linux
```bash
cd ~/Desktop/nom-du-repo
source venv/bin/activate
python app.py
```

---

## ✅ Checklist

- [ ] Python 3.8+ installé
- [ ] Git installé
- [ ] Environnement virtuel activé `(venv)`
- [ ] Clé API Gemini configurée
- [ ] Application accessible sur localhost:5000

🎉 **Setup terminé !**

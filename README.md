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

### Setup

Windows (PowerShell):

# Clonage et navigation
cd Desktop
git clone https://github.com/votre-username/nom-du-repo.git
cd nom-du-repo

# Configuration Python
python --version
python -m venv venv
venv\Scripts\activate

# Installation
pip install --upgrade pip
pip install -r requirements.txt

# Configuration .env (puis éditer le fichier)
New-Item .env
notepad .env

# Initialisation et lancement
python database/init_database.py
python scripts/index_existing_courses.py  # optionnel
python app.py

MAC / Linux :

# Clonage et navigation
cd ~/Desktop
git clone https://github.com/votre-username/nom-du-repo.git
cd nom-du-repo

# Configuration Python
python3 --version
python3 -m venv venv
source venv/bin/activate

# Installation
pip install --upgrade pip
pip install -r requirements.txt

# Configuration .env (puis éditer le fichier)
touch .env
nano .env

# Initialisation et lancement
python database/init_database.py
python scripts/index_existing_courses.py  # optionnel
python app.py

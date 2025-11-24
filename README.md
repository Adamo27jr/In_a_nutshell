# In_a_nutshell
1. README.md

Transforme tes documents d'étude (PDFs, couvertures de livres, notes de cours) en podcasts audio avec quiz auto-générés. Construit avec RAG, Gemini Vision AI, et optimisé pour l'apprentissage mobile en déplacement.

## 🎯 Équipe

- Adam Belhassan
- Antoine Legendre
- Alex Van Tran Nhieu
- Sabine Mansour
- Lyna Kartout

## 🚀 Installation

### Prérequis

- Python 3.10+
- Tesseract OCR installé sur votre système
  - **macOS:** `brew install tesseract`
  - **Ubuntu:** `sudo apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng`
  - **Windows:** [Télécharger ici](https://github.com/UB-Mannheim/tesseract/wiki)

### Setup

```bash
# Clone le repository
git clone https://github.com/votre-equipe/snaplearn_audio_quiz.git
cd snaplearn_audio_quiz

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env et ajouter votre GEMINI_API_KEY
API : AIzaSyCk6WIE0SpHVxko_H2GUcOCQb5Nq2fzS4c

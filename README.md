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

### **Problème Réseau Universitaire**

Sur les réseaux **Eduroam** ou WiFi publics, la communication entre appareils est **bloquée par sécurité**. Le QR code ne fonctionnera pas directement.

### **SOLUTION RECOMMANDÉE : Partage de Connexion**

**Vous DEVEZ activer le partage de connexion de votre téléphone vers votre PC**

#### **Android :**
1. **Paramètres** → **Connexions** → **Point d'accès mobile et modem**
2. Activer **"Point d'accès mobile"**
3. Noter le nom du réseau WiFi et le mot de passe
4. Sur votre PC : Se connecter à ce WiFi
5. Relancer l'application : `python app.py`
6. Scanner le nouveau QR code 

#### **iPhone :**
1. **Réglages** → **Partage de connexion**
2. Activer **"Autoriser d'autres utilisateurs"**
3. Noter le mot de passe WiFi affiché
4. Sur votre PC : Se connecter au réseau de votre iPhone
5. Relancer l'application : `python app.py`
6. Scanner le nouveau QR code 

#### **Côté PC (Windows) :**
```powershell
# 1. Connectez-vous au WiFi de votre téléphone
# 2. Vérifiez la connexion
ipconfig | findstr IPv4
# 3. Relancez l'app
venv\Scripts\activate
python app.py

---

## Relancer plus tard

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

## Checklist

- [ ] Python 3.8+ installé
- [ ] Git installé
- [ ] Environnement virtuel activé `(venv)`
- [ ] Clé API Gemini configurée
- [ ] Application accessible sur localhost:5000

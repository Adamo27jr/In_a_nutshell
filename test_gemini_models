"""
Tester les modeles Flash disponibles
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=api_key)

# Liste des modeles Flash a tester (par ordre de preference)
flash_models = [
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-flash-latest",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.0-flash-lite"
]

print("Test des modeles Flash...\n")

for model_name in flash_models:
    print(f"Test de {model_name}...")
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Dis bonjour en une phrase")
        
        print(f"✅ SUCCES !")
        print(f"Reponse : {response.text}")
        print(f"\n🎯 UTILISEZ CE MODELE :")
        print(f"GEMINI_MODEL={model_name}")
        print("\nAjoutez cette ligne dans votre fichier .env")
        break  # Arreter des qu'on trouve un modele qui fonctionne
        
    except Exception as e:
        print(f"❌ Echec : {str(e)[:100]}...\n")

print("\nTermine !")

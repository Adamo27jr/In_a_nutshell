"""
Script pour tester et identifier les modeles Gemini disponibles
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("Erreur : GOOGLE_API_KEY non trouvee dans .env")
    exit(1)

print(f"Cle API : {api_key[:15]}...")

genai.configure(api_key=api_key)

print("\nModeles Gemini disponibles pour generateContent :\n")

available_models = []

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"OK {model.name}")
        available_models.append(model.name)

if not available_models:
    print("\nAucun modele disponible avec votre cle API")
    print("\nSolutions :")
    print("1. Verifiez que votre cle API est valide")
    print("2. Allez sur https://aistudio.google.com/app/apikey")
    print("3. Creez une nouvelle cle API")
else:
    print(f"\n{len(available_models)} modele(s) disponible(s)")
    
    # Tester le premier modele
    print(f"\nTest du modele : {available_models[0]}")
    
    try:
        model = genai.GenerativeModel(available_models[0])
        response = model.generate_content("Dis bonjour")
        print(f"Test reussi !")
        print(f"Reponse : {response.text[:100]}...")
        
        print(f"\nAjoutez ceci dans votre .env :")
        print(f"GEMINI_MODEL={available_models[0]}")
        
    except Exception as e:
        print(f"Erreur lors du test : {e}")

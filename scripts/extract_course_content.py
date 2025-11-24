import fitz  # PyMuPDF
import json
import os
from pathlib import Path


def extract_all_courses(course_root="data/course_materials"):
    """Extrait tous les PDFs trouvés dans course_materials"""
    
    print("Extraction des cours AMU...\n")
    
    corpus = {
        "course_materials": [],
        "common_questions": [
            {
                "question": "Qu'est-ce qu'un embedding?",
                "answer": "Une représentation vectorielle dense qui capture la sémantique des mots dans un espace géométrique.",
                "related_topics": ["embeddings", "transformers"],
                "week": 1
            },
            {
                "question": "Comment utiliser Hugging Face?",
                "answer": "Hugging Face fournit des pipelines et des modèles pré-entraînés accessibles via la bibliothèque transformers.",
                "related_topics": ["huggingface", "pipelines"],
                "week": 2
            },
            {
                "question": "Qu'est-ce que le RAG?",
                "answer": "Le RAG (Retrieval-Augmented Generation) combine recherche d'information et génération LLM pour ancrer les réponses dans des données externes.",
                "related_topics": ["rag", "retrieval"],
                "week": 5
            }
        ]
    }
    
    # Parcourir tous les PDFs
    all_pdfs = list(Path(course_root).rglob("*.pdf"))
    
    print(f"{len(all_pdfs)} fichiers PDF trouvés\n")
    
    for pdf_path in all_pdfs:
        print(f"{pdf_path.name}")
        
        try:
            # Ouvrir le PDF
            doc = fitz.open(str(pdf_path))
            
            # Extraire le texte
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            
            doc.close()
            
            # Déterminer level et semester depuis le chemin
            parts = str(pdf_path).lower()
            level = "M2" if "m2" in parts else "M1" if "m1" in parts else "Unknown"
            semester = "S2" if "s2" in parts else "S1" if "s1" in parts else "Unknown"
            
            # Créer l'entrée
            course_entry = {
                "id": f"{level}_{semester}_{pdf_path.stem}",
                "level": level,
                "semester": semester,
                "title": pdf_path.stem.replace('_', ' ').title(),
                "topics": [],  # À compléter manuellement si besoin
                "content": full_text[:3000],  # Premiers 3000 caractères
                "key_concepts": [],  # À compléter manuellement si besoin
                "source_file": pdf_path.name,
                "page_count": len(doc)
            }
            
            corpus["course_materials"].append(course_entry)
            print(f"   {len(doc)} pages extraites\n")
            
        except Exception as e:
            print(f"   Erreur: {e}\n")
    
    # Sauvegarder
    output_file = "data/amu_datascience_corpus.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(corpus, indent=2, ensure_ascii=False, fp=f)
    
    print(f"Corpus sauvegardé: {output_file}")
    print(f"{len(corpus['course_materials'])} cours extraits")


if __name__ == "__main__":
    extract_all_courses()

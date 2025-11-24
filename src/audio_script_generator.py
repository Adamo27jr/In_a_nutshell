import google.generativeai as genai
from typing import List, Dict
import json
import os


class AudioScriptGenerator:
    """Génère des scripts audio pédagogiques optimisés"""
    
    def __init__(self, gemini_api_key: str, knowledge_base):
        """
        Initialise le générateur
        
        Args:
            gemini_api_key: Clé API Gemini
            knowledge_base: Instance de AMUKnowledgeBase pour RAG
        """
        genai.configure(api_key=gemini_api_key)
        self.llm = genai.GenerativeModel('gemini-1.5-flash')
        self.kb = knowledge_base
    
    def generate_script(
        self, 
        document_data: Dict,
        target_duration: int = 300,
        style: str = "conversational"
    ) -> Dict:
        """
        Génère un script de podcast complet
        
        Args:
            document_data: Données du document traité
            target_duration: Durée cible en secondes
            style: Style du podcast (conversational, academic, storytelling)
            
        Returns:
            Dict avec intro, contenu, conclusion, quiz
        """
        print(f" Génération du script ({target_duration}s, style: {style})...")
        
        # Extraction du contenu selon le type
        content = self._extract_content(document_data)
        
        # Enrichissement RAG
        main_topic = self._get_main_topic(document_data)
        rag_context = ""
        if main_topic and self.kb:
            rag_context = self.kb.get_context(main_topic, max_tokens=1000)
        
        # Calcul du nombre de mots cibles (150 mots/min pour audio)
        target_words = int(target_duration / 60 * 150)
        
        # Génération du script
        script = self._generate_script_with_llm(
            content, 
            rag_context, 
            target_words, 
            style,
            document_data
        )
        
        return script
    
    def _extract_content(self, document_data: Dict) -> str:
        """Extrait le contenu textuel du document"""
        if document_data['type'] == 'pdf':
            # Concaténer les 5 premières pages
            pages_text = [p['text'] for p in document_data['pages'][:5]]
            return "\n\n".join(pages_text)
        else:  # image
            return document_data.get('text', '')
    
    def _get_main_topic(self, document_data: Dict) -> str:
        """Extrait le sujet principal pour la recherche RAG"""
        enhanced = document_data.get('enhanced_metadata', {})
        
        if 'title' in enhanced:  # Couverture de livre
            return enhanced['title']
        elif 'main_topic' in enhanced:
            return enhanced['main_topic']
        elif document_data['type'] == 'pdf':
            return document_data['metadata'].get('title', '')
        
        return ""
    
    def _generate_script_with_llm(
        self,
        content: str,
        rag_context: str,
        target_words: int,
        style: str,
        document_data: Dict
    ) -> Dict:
        """Génère le script via Gemini LLM"""
        
        # Styles de narration
        style_prompts = {
            "conversational": "Ton amical et décontracté, comme si tu expliquais à un ami autour d'un café",
            "academic": "Ton académique mais accessible, comme un bon professeur passionné",
            "storytelling": "Raconte une histoire captivante autour des concepts, avec une narration engageante"
        }
        
        # Construction du prompt
        prompt = f"""
Tu es un créateur de podcasts éducatifs pour étudiants en Data Science à l'Université Aix-Marseille.

CONTENU DU DOCUMENT À RÉSUMER:
{content[:2500]}

CONTEXTE DU COURS AMU (RAG):
{rag_context[:1500] if rag_context else "Pas de contexte additionnel disponible"}

TYPE DE DOCUMENT: {document_data['type']}
SUJET PRINCIPAL: {self._get_main_topic(document_data)}

CONSIGNES DE CRÉATION:
- Durée cible: {target_words} mots (environ {target_words//150} minutes d'audio)
- Style: {style_prompts.get(style, style_prompts['conversational'])}
- Structure obligatoire: 
  * Introduction accrocheuse (10% du contenu)
  * Développement en 2-3 sections claires (70%)
  * Conclusion avec takeaways (20%)
- Inclure 3 questions quiz de compréhension
- Langage simple mais précis
- Transitions naturelles entre les sections

IMPORTANT:
- Génère UNIQUEMENT du texte à lire (pas de stage directions)
- Utilise des phrases courtes et claires pour l'audio
- Fais des liens avec le cours AMU Data Science quand pertinent
- Termine chaque section par une phrase de transition

Génère le script en format JSON strict:
{{
    "intro": "Texte d'introduction complet...",
    "main_content": "Contenu principal complet avec toutes les sections...",
    "conclusion": "Conclusion complète avec résumé des points clés...",
    "quiz_questions": [
        {{
            "question": "Question de compréhension claire",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option B",
            "explanation": "Explication de pourquoi c'est la bonne réponse"
        }}
    ],
    "total_word_count": {target_words}
}}
"""
        
        try:
            response = self.llm.generate_content(prompt)
            
            # Parser le JSON
            json_text = response.text.replace('```json', '').replace('```', '').strip()
            script = json.loads(json_text)
            
            print(f" Script généré: {script.get('total_word_count', 0)} mots")
            
            return script
            
        except json.JSONDecodeError as e:
            print(f" Erreur parsing JSON: {e}")
            # Fallback simple
            return self._create_fallback_script(content, target_words)
        except Exception as e:
            print(f" Erreur génération: {e}")
            return self._create_fallback_script(content, target_words)
    
    def _create_fallback_script(self, content: str, target_words: int) -> Dict:
        """Crée un script de secours si la génération LLM échoue"""
        return {
            "intro": "Bienvenue dans ce podcast éducatif. Nous allons explorer ensemble les concepts clés de ce document.",
            "main_content": content[:target_words * 5],  # Approximation
            "conclusion": "Merci d'avoir écouté ce podcast. N'hésitez pas à réécouter les sections qui vous semblent importantes.",
            "quiz_questions": [
                {
                    "question": "Quel est le sujet principal de ce document?",
                    "options": ["Sujet A", "Sujet B", "Sujet C", "Sujet D"],
                    "correct_answer": "Sujet A",
                    "explanation": "Le document traite principalement de ce sujet."
                }
            ],
            "total_word_count": len(content.split())
        }

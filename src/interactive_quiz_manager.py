import streamlit as st
from typing import List, Dict


class QuizManager:
    """Gestionnaire de quiz interactifs"""
    
    def __init__(self):
        """Initialise le gestionnaire de quiz"""
        pass
    
    def render_quiz(self, questions: List[Dict]):
        """
        Affiche un quiz interactif complet
        
        Args:
            questions: Liste de questions avec options et réponses
        """
        # Initialisation du state si nécessaire
        if 'quiz_state' not in st.session_state:
            st.session_state.quiz_state = {
                'current': 0,
                'score': 0,
                'answers': [],
                'active': False
            }
        
        # Affichage selon l'état
        if not st.session_state.quiz_state['active']:
            self._render_start_screen(questions)
        else:
            current_idx = st.session_state.quiz_state['current']
            
            if current_idx >= len(questions):
                self._render_results(questions)
            else:
                self._render_question(questions, current_idx)
    
    def _render_start_screen(self, questions: List[Dict]):
        """Écran de démarrage du quiz"""
        st.markdown("###  Quiz Interactif")
        st.write(f"**{len(questions)} questions** pour tester ta compréhension du podcast")
        
        # Aperçu
        with st.expander(" Aperçu des questions"):
            for i, q in enumerate(questions, 1):
                st.write(f"{i}. {q['question'][:60]}...")
        
        # Bouton de démarrage
        if st.button(" Commencer le Quiz", use_container_width=True, type="primary"):
            st.session_state.quiz_state['active'] = True
            st.session_state.quiz_state['current'] = 0
            st.session_state.quiz_state['score'] = 0
            st.session_state.quiz_state['answers'] = []
            st.rerun()
    
    def _render_question(self, questions: List[Dict], idx: int):
        """Affiche une question avec ses options"""
        question = questions[idx]
        
        # Barre de progression
        progress = (idx + 1) / len(questions)
        st.progress(progress)
        st.caption(f"Question {idx + 1} sur {len(questions)}")
        
        # Question
        st.markdown(f"###  {question['question']}")
        
        # Espacement
        st.write("")
        
        # Options (boutons)
        options = question.get('options', [])
        
        # Variable pour stocker la réponse sélectionnée
        if f'selected_answer_{idx}' not in st.session_state:
            st.session_state[f'selected_answer_{idx}'] = None
        
        # Affichage des options
        for i, option in enumerate(options):
            button_label = f"{chr(65+i)}. {option}"
            
            if st.button(
                button_label, 
                key=f"quiz_{idx}_option_{i}",
                use_container_width=True
            ):
                st.session_state[f'selected_answer_{idx}'] = option
                
                # Vérification
                is_correct = option == question['correct_answer']
                
                # Feedback immédiat
                if is_correct:
                    st.success(" Correct !")
                    st.session_state.quiz_state['score'] += 1
                else:
                    st.error(f" Incorrect. La bonne réponse était : **{question['correct_answer']}**")
                
                # Explication
                if question.get('explanation'):
                    st.info(f" **Explication :** {question['explanation']}")
                
                # Sauvegarder la réponse
                st.session_state.quiz_state['answers'].append({
                    'question': question['question'],
                    'user_answer': option,
                    'correct_answer': question['correct_answer'],
                    'is_correct': is_correct
                })
                
                # Bouton suivant
                st.write("")
                if st.button(" Question suivante", type="primary", use_container_width=True):
                    st.session_state.quiz_state['current'] += 1
                    st.rerun()
    
    def _render_results(self, questions: List[Dict]):
        """Affiche les résultats finaux du quiz"""
        score = st.session_state.quiz_state['score']
        total = len(questions)
        percentage = (score / total) * 100 if total > 0 else 0
        
        # Titre
        st.markdown("##  Quiz Terminé !")
        
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Score", f"{score}/{total}")
        
        with col2:
            st.metric("Pourcentage", f"{percentage:.0f}%")
        
        with col3:
            # Badge selon le score
            if percentage >= 80:
                st.metric("Niveau", " Expert")
            elif percentage >= 60:
                st.metric("Niveau", " Bien")
            else:
                st.metric("Niveau", " À réviser")
        
        # Message selon le score
        st.write("")
        if percentage >= 80:
            st.success(" **Excellent !** Tu maîtrises parfaitement le sujet.")
        elif percentage >= 60:
            st.info(" **Bien joué !** Continue comme ça, tu es sur la bonne voie.")
        else:
            st.warning(" **Continue à réviser.** Réécoute le podcast et réessaye !")
        
        # Détails des réponses
        st.write("")
        with st.expander("📊 Détails de tes réponses"):
            for i, answer in enumerate(st.session_state.quiz_state['answers'], 1):
                if answer['is_correct']:
                    st.success(f"**Question {i} :**  {answer['question'][:60]}...")
                else:
                    st.error(f"**Question {i} :**  {answer['question'][:60]}...")
                    st.caption(f"Ta réponse : {answer['user_answer']} | Correct : {answer['correct_answer']}")
        
        # Actions
        st.write("")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refaire le quiz", use_container_width=True):
                st.session_state.quiz_state = {
                    'current': 0,
                    'score': 0,
                    'answers': [],
                    'active': False
                }
                st.rerun()
        
        with col2:
            if st.button("🏠 Retour à l'accueil", use_container_width=True):
                st.session_state.quiz_state = {
                    'current': 0,
                    'score': 0,
                    'answers': [],
                    'active': False
                }
                # Retour au tab principal
                st.rerun()

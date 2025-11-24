"""
Gestionnaire de quiz interactifs pour Flask.
"""

from typing import List, Dict, Optional
import random
import json
from datetime import datetime
import uuid


class InteractiveQuizManager:
    """Gestionnaire de quiz interactifs"""
    
    def __init__(self):
        """Initialise le gestionnaire de quiz"""
        self.quizzes = {}
        self.user_responses = {}
        self.quiz_sessions = {}
    
    def create_quiz(
        self,
        quiz_id: str,
        questions: List[Dict],
        title: str = "Quiz",
        shuffle: bool = True
    ) -> Dict:
        """
        Crée un nouveau quiz.
        
        Args:
            quiz_id: Identifiant unique du quiz
            questions: Liste de questions avec options et réponses
            title: Titre du quiz
            shuffle: Mélanger les questions
            
        Returns:
            Métadonnées du quiz créé
        """
        if shuffle:
            questions = random.sample(questions, len(questions))
        
        quiz_data = {
            'quiz_id': quiz_id,
            'title': title,
            'questions': questions,
            'created_at': datetime.now().isoformat(),
            'total_questions': len(questions)
        }
        
        self.quizzes[quiz_id] = quiz_data
        return quiz_data
    
    def get_quiz(self, quiz_id: str) -> Optional[Dict]:
        """
        Récupère un quiz par son ID.
        
        Args:
            quiz_id: Identifiant du quiz
            
        Returns:
            Données du quiz ou None
        """
        return self.quizzes.get(quiz_id)
    
    def start_quiz_session(self, quiz_id: str, user_id: str = "anonymous") -> str:
        """
        Démarre une nouvelle session de quiz.
        
        Args:
            quiz_id: ID du quiz
            user_id: ID de l'utilisateur
            
        Returns:
            session_id: ID de la session créée
        """
        session_id = str(uuid.uuid4())
        
        self.quiz_sessions[session_id] = {
            'session_id': session_id,
            'quiz_id': quiz_id,
            'user_id': user_id,
            'current_question': 0,
            'score': 0,
            'answers': [],
            'started_at': datetime.now().isoformat(),
            'completed': False
        }
        
        return session_id
    
    def submit_answer(
        self,
        session_id: str,
        question_index: int,
        user_answer: str
    ) -> Dict:
        """
        Soumet une réponse à une question.
        
        Args:
            session_id: ID de la session
            question_index: Index de la question
            user_answer: Réponse de l'utilisateur
            
        Returns:
            Résultat de l'évaluation
        """
        session = self.quiz_sessions.get(session_id)
        if not session:
            return {'error': 'Session non trouvée'}
        
        quiz = self.quizzes.get(session['quiz_id'])
        if not quiz:
            return {'error': 'Quiz non trouvé'}
        
        if question_index >= len(quiz['questions']):
            return {'error': 'Question invalide'}
        
        question = quiz['questions'][question_index]
        correct_answer = question.get('correct_answer', '')
        
        # Vérifier la réponse
        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
        
        # Mettre à jour le score
        if is_correct:
            session['score'] += 1
        
        # Enregistrer la réponse
        answer_record = {
            'question': question['question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'timestamp': datetime.now().isoformat()
        }
        
        session['answers'].append(answer_record)
        session['current_question'] = question_index + 1
        
        return {
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'explanation': question.get('explanation', ''),
            'current_score': session['score'],
            'total_questions': len(quiz['questions']),
            'next_question': question_index + 1 if question_index + 1 < len(quiz['questions']) else None
        }
    
    def get_session_state(self, session_id: str) -> Optional[Dict]:
        """
        Récupère l'état d'une session.
        
        Args:
            session_id: ID de la session
            
        Returns:
            État de la session
        """
        return self.quiz_sessions.get(session_id)
    
    def complete_quiz(self, session_id: str) -> Dict:
        """
        Marque un quiz comme terminé et calcule les résultats.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Résultats finaux
        """
        session = self.quiz_sessions.get(session_id)
        if not session:
            return {'error': 'Session non trouvée'}
        
        quiz = self.quizzes.get(session['quiz_id'])
        if not quiz:
            return {'error': 'Quiz non trouvé'}
        
        total_questions = len(quiz['questions'])
        score = session['score']
        percentage = (score / total_questions * 100) if total_questions > 0 else 0
        
        # Déterminer le niveau
        if percentage >= 80:
            level = "Expert"
            message = "Excellent ! Tu maîtrises parfaitement le sujet."
        elif percentage >= 60:
            level = "Bien"
            message = "Bien joué ! Continue comme ça, tu es sur la bonne voie."
        else:
            level = "À réviser"
            message = "Continue à réviser. Réécoute le podcast et réessaye !"
        
        session['completed'] = True
        session['completed_at'] = datetime.now().isoformat()
        
        return {
            'session_id': session_id,
            'quiz_id': session['quiz_id'],
            'score': score,
            'total_questions': total_questions,
            'percentage': round(percentage, 2),
            'level': level,
            'message': message,
            'answers': session['answers'],
            'passed': percentage >= 60
        }
    
    def get_quiz_results(self, session_id: str) -> Dict:
        """
        Récupère les résultats d'un quiz terminé.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Résultats détaillés
        """
        session = self.quiz_sessions.get(session_id)
        if not session:
            return {'error': 'Session non trouvée'}
        
        if not session.get('completed'):
            return self.complete_quiz(session_id)
        
        quiz = self.quizzes.get(session['quiz_id'])
        total_questions = len(quiz['questions']) if quiz else 0
        score = session['score']
        percentage = (score / total_questions * 100) if total_questions > 0 else 0
        
        return {
            'session_id': session_id,
            'quiz_id': session['quiz_id'],
            'score': score,
            'total_questions': total_questions,
            'percentage': round(percentage, 2),
            'answers': session['answers'],
            'passed': percentage >= 60
        }
    
    def generate_sample_quiz(self) -> str:
        """
        Génère un quiz d'exemple pour tester.
        
        Returns:
            quiz_id: ID du quiz créé
        """
        quiz_id = f"sample_quiz_{uuid.uuid4().hex[:8]}"
        
        questions = [
            {
                'question': "Qu'est-ce que le Machine Learning ?",
                'question_type': 'multiple_choice',
                'options': [
                    "Un type de base de données",
                    "Une méthode pour faire apprendre des modèles à partir de données",
                    "Un langage de programmation",
                    "Un système d'exploitation"
                ],
                'correct_answer': "Une méthode pour faire apprendre des modèles à partir de données",
                'explanation': "Le Machine Learning est une branche de l'IA qui permet aux systèmes d'apprendre à partir de données sans être explicitement programmés.",
                'difficulty': 'beginner'
            },
            {
                'question': "Quel est le langage le plus utilisé en Data Science ?",
                'question_type': 'multiple_choice',
                'options': ["Java", "Python", "C++", "Ruby"],
                'correct_answer': "Python",
                'explanation': "Python est le langage le plus populaire en Data Science grâce à ses bibliothèques comme NumPy, Pandas, et Scikit-learn.",
                'difficulty': 'beginner'
            },
            {
                'question': "Que signifie CNN en Deep Learning ?",
                'question_type': 'multiple_choice',
                'options': [
                    "Computer Neural Network",
                    "Convolutional Neural Network",
                    "Complex Number Network",
                    "Centralized Neural Network"
                ],
                'correct_answer': "Convolutional Neural Network",
                'explanation': "CNN (Convolutional Neural Network) est un type de réseau de neurones spécialement conçu pour traiter des images.",
                'difficulty': 'intermediate'
            }
        ]
        
        self.create_quiz(quiz_id, questions, title="Quiz de Démonstration Data Science")
        return quiz_id
    
    def get_all_quizzes(self) -> List[Dict]:
        """
        Récupère tous les quiz disponibles.
        
        Returns:
            Liste des quiz
        """
        return [
            {
                'quiz_id': quiz_id,
                'title': quiz_data['title'],
                'total_questions': quiz_data['total_questions'],
                'created_at': quiz_data['created_at']
            }
            for quiz_id, quiz_data in self.quizzes.items()
        ]

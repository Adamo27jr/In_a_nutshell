/**
 * Gestionnaire de quiz mobile
 */

class QuizHandler {
    constructor(quizData, sessionId) {
        this.quizData = quizData;
        this.sessionId = sessionId;
        this.currentQuestion = 0;
        this.score = 0;
        this.answers = [];
        
        this.init();
    }
    
    init() {
        this.renderQuestion();
    }
    
    renderQuestion() {
        const question = this.quizData[this.currentQuestion];
        const container = document.getElementById('quiz-container');
        
        // Mettre à jour la barre de progression
        const progress = ((this.currentQuestion + 1) / this.quizData.length) * 100;
        document.getElementById('quiz-progress-bar').style.width = `${progress}%`;
        document.getElementById('question-counter').textContent = 
            `Question ${this.currentQuestion + 1}/${this.quizData.length}`;
        
        // Afficher la question
        const questionHTML = `
            <div class="question-card">
                <div class="question-number">Question ${this.currentQuestion + 1}</div>
                <div class="question-text">${question.question}</div>
                
                <ul class="options-list" id="options-list">
                    ${question.options.map((option, index) => `
                        <li class="option-item" data-index="${index}">
                            ${option}
                        </li>
                    `).join('')}
                </ul>
                
                <div id="explanation" class="explanation" style="display: none;"></div>
                
                <div class="quiz-actions">
                    <button class="btn-quiz btn-submit" id="btn-submit" disabled>
                        Valider
                    </button>
                    <button class="btn-quiz btn-next" id="btn-next" style="display: none;">
                        Suivant
                    </button>
                </div>
            </div>
        `;
        
        container.innerHTML = questionHTML;
        
        this.setupQuestionListeners();
    }
    
    setupQuestionListeners() {
        const options = document.querySelectorAll('.option-item');
        const submitBtn = document.getElementById('btn-submit');
        const nextBtn = document.getElementById('btn-next');
        
        let selectedOption = null;
        
        // Sélection d'une option
        options.forEach(option => {
            option.addEventListener('click', () => {
                if (option.classList.contains('disabled')) return;
                
                // Désélectionner les autres
                options.forEach(opt => opt.classList.remove('selected'));
                
                // Sélectionner celle-ci
                option.classList.add('selected');
                selectedOption = parseInt(option.dataset.index);
                
                // Activer le bouton valider
                submitBtn.disabled = false;
            });
        });
        
        // Valider la réponse
        submitBtn.addEventListener('click', () => {
            if (selectedOption === null) return;
            
            const question = this.quizData[this.currentQuestion];
            const selectedAnswer = question.options[selectedOption];
            const isCorrect = selectedAnswer === question.correct_answer;
            
            // Enregistrer la réponse
            this.answers.push({
                question: question.question,
                selected: selectedAnswer,
                correct: question.correct_answer,
                isCorrect: isCorrect
            });
            
            if (isCorrect) {
                this.score++;
                options[selectedOption].classList.add('correct');
            } else {
                options[selectedOption].classList.add('incorrect');
                
                // Montrer la bonne réponse
                options.forEach((opt, index) => {
                    if (question.options[index] === question.correct_answer) {
                        opt.classList.add('correct');
                    }
                });
            }
            
            // Désactiver toutes les options
            options.forEach(opt => opt.classList.add('disabled'));
            
            // Afficher l'explication
            const explanationEl = document.getElementById('explanation');
            explanationEl.textContent = question.explanation;
            explanationEl.style.display = 'block';
            
            // Cacher le bouton valider, montrer le bouton suivant
            submitBtn.style.display = 'none';
            nextBtn.style.display = 'block';
            
            // Envoyer la réponse au serveur
            this.submitAnswer(selectedAnswer, isCorrect);
        });
        
        // Question suivante
        nextBtn.addEventListener('click', () => {
            this.currentQuestion++;
            
            if (this.currentQuestion < this.quizData.length) {
                this.renderQuestion();
            } else {
                this.showResults();
            }
        });
    }
    
    submitAnswer(answer, isCorrect) {
        if (window.wsClient) {
            window.wsClient.send({
                type: 'submit_quiz_answer',
                session_id: this.sessionId,
                quiz_id: this.quizData[this.currentQuestion].quiz_id || 'unknown',
                answer: answer,
                is_correct: isCorrect
            });
        }
    }
    
    showResults() {
        const container = document.getElementById('quiz-container');
        const percentage = Math.round((this.score / this.quizData.length) * 100);
        
        let message = '';
        if (percentage >= 80) {
            message = 'Excellent travail ! 🎉';
        } else if (percentage >= 60) {
            message = 'Bon travail ! 👍';
        } else {
            message = 'Continuez à réviser ! 📚';
        }
        
        const resultsHTML = `
            <div class="quiz-score">
                <div class="score-circle">
                    <div class="score-value">${percentage}%</div>
                    <div class="score-label">Score</div>
                </div>
                
                <div class="score-message">${message}</div>
                <div class="score-details">
                    ${this.score} / ${this.quizData.length} bonnes réponses
                </div>
                
                <button class="btn-restart" onclick="location.reload()">
                    Recommencer
                </button>
            </div>
        `;
        
        container.innerHTML = resultsHTML;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    // Les données du quiz seront chargées depuis l'API
    const sessionId = new URLSearchParams(window.location.search).get('session') || 'default';
    const chapterId = new URLSearchParams(window.location.search).get('chapter');
    
    if (chapterId) {
        // Charger le quiz depuis l'API
        fetch(`/api/quiz/generate/${chapterId}?num=5`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.quiz) {
                    window.quizHandler = new QuizHandler(data.quiz, sessionId);
                }
            })
            .catch(error => console.error('Error loading quiz:', error));
    }
});

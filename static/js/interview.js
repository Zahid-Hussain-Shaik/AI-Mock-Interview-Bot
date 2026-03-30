/**
 * interview.js — Interview flow logic
 * Fetches questions, handles answer submission, displays evaluation inline.
 */

(function () {
    'use strict';

    const SESSION_ID = window.SESSION_ID;
    if (!SESSION_ID) {
        window.location.href = '/';
        return;
    }

    // DOM Elements
    const progressText = document.getElementById('progress-text');
    const progressFill = document.getElementById('progress-fill');
    const metaRole = document.getElementById('meta-role');
    const metaLevel = document.getElementById('meta-level');
    const questionNumber = document.getElementById('question-number');
    const questionCategory = document.getElementById('question-category');
    const questionDifficulty = document.getElementById('question-difficulty');
    const questionText = document.getElementById('question-text');
    const answerInput = document.getElementById('answer-input');
    const charCount = document.getElementById('char-count');
    const submitBtn = document.getElementById('submit-btn');
    const submitBtnText = document.getElementById('submit-btn-text');
    const submitBtnSpinner = document.getElementById('submit-btn-spinner');
    const skipBtn = document.getElementById('skip-btn');
    const answerSection = document.getElementById('answer-section');
    const evaluationSection = document.getElementById('evaluation-section');
    const evalScore = document.getElementById('eval-score');
    const evalPerformanceBadge = document.getElementById('eval-performance-badge');
    const evalSummary = document.getElementById('eval-summary');
    const evalStrengths = document.getElementById('eval-strengths');
    const evalWeaknesses = document.getElementById('eval-weaknesses');
    const evalImprovements = document.getElementById('eval-improvements');
    const nextBtn = document.getElementById('next-btn');
    const nextBtnText = document.getElementById('next-btn-text');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    const toastContainer = document.getElementById('toast-container');

    let currentQuestion = null;
    let totalQuestions = 0;
    let currentNum = 0;

    // ── Utilities ──

    function showToast(message, type = 'error') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    function setSubmitLoading(loading) {
        submitBtn.disabled = loading;
        skipBtn.disabled = loading;
        submitBtnText.textContent = loading ? 'Evaluating...' : 'Submit Answer';
        submitBtnSpinner.classList.toggle('hidden', !loading);
        loadingOverlay.classList.toggle('active', loading);
    }

    function getScoreColor(score) {
        if (score >= 9) return 'score-excellent';
        if (score >= 7) return 'score-strong';
        if (score >= 5) return 'score-adequate';
        return 'score-poor';
    }

    function getPerformanceLabel(score) {
        if (score >= 9) return 'Excellent';
        if (score >= 7) return 'Strong';
        if (score >= 5) return 'Adequate';
        if (score >= 3) return 'Needs Work';
        return 'Poor';
    }

    function getCategoryClass(category) {
        const map = {
            'technical': 'badge-technical',
            'behavioral': 'badge-behavioral',
            'situational': 'badge-situational',
            'problem-solving': 'badge-problem-solving',
        };
        return map[category] || 'badge-technical';
    }

    function getDifficultyClass(difficulty) {
        const map = {
            'easy': 'badge-easy',
            'medium': 'badge-medium',
            'hard': 'badge-hard',
        };
        return map[difficulty] || 'badge-medium';
    }

    function updateProgress(current, total) {
        const pct = total > 0 ? (current / total) * 100 : 0;
        progressText.textContent = `Question ${current} of ${total}`;
        progressFill.style.width = `${pct}%`;
    }

    // ── Display Functions ──

    function displayQuestion(question, current, total) {
        currentQuestion = question;
        currentNum = current;
        totalQuestions = total;

        questionNumber.textContent = `Q${current}`;
        questionText.textContent = question.text;

        // Category badge
        const cat = question.category || 'technical';
        questionCategory.textContent = cat.charAt(0).toUpperCase() + cat.slice(1).replace('-', ' ');
        questionCategory.className = `badge ${getCategoryClass(cat)}`;

        // Difficulty badge
        const diff = question.difficulty || 'medium';
        questionDifficulty.textContent = diff.charAt(0).toUpperCase() + diff.slice(1);
        questionDifficulty.className = `badge badge-difficulty ${getDifficultyClass(diff)}`;

        updateProgress(current, total);

        // Reset answer area
        answerInput.value = '';
        charCount.textContent = '0';
        answerSection.classList.remove('hidden');
        evaluationSection.classList.add('hidden');
        answerInput.focus();

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function displayEvaluation(evaluation, isCompleted) {
        evaluationSection.classList.remove('hidden');
        answerSection.classList.add('hidden');

        const score = evaluation.score;
        evalScore.textContent = score;
        evalScore.className = `score-value ${getScoreColor(score)}`;

        const perfLabel = getPerformanceLabel(score);
        evalPerformanceBadge.textContent = perfLabel;
        evalPerformanceBadge.className = `badge ${score >= 7 ? 'badge-easy' : score >= 5 ? 'badge-medium' : 'badge-hard'}`;

        evalSummary.textContent = evaluation.summary || '';

        // Lists
        evalStrengths.innerHTML = '';
        (evaluation.strengths || []).forEach(s => {
            const li = document.createElement('li');
            li.textContent = s;
            evalStrengths.appendChild(li);
        });

        evalWeaknesses.innerHTML = '';
        (evaluation.weaknesses || []).forEach(w => {
            const li = document.createElement('li');
            li.textContent = w;
            evalWeaknesses.appendChild(li);
        });

        evalImprovements.innerHTML = '';
        (evaluation.improvements || []).forEach(imp => {
            const li = document.createElement('li');
            li.textContent = imp;
            evalImprovements.appendChild(li);
        });

        // Next button
        if (isCompleted) {
            nextBtnText.textContent = 'View Results →';
        } else {
            nextBtnText.textContent = 'Next Question →';
        }

        // Scroll to evaluation
        setTimeout(() => {
            evaluationSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }

    // ── API Calls ──

    async function fetchCurrentQuestion() {
        try {
            const res = await fetch(`/api/interview/${SESSION_ID}/question`);
            const data = await res.json();

            if (!data.success) {
                throw new Error(data.error?.message || 'Failed to fetch question.');
            }

            if (data.data.completed) {
                window.location.href = `/results/${SESSION_ID}`;
                return;
            }

            metaRole.textContent = data.data.role;
            metaLevel.textContent = data.data.experience_level;

            displayQuestion(data.data.current_question, data.data.current, data.data.total);
        } catch (err) {
            showToast(err.message || 'Failed to load question.');
            console.error('Fetch question error:', err);
        }
    }

    async function submitAnswer(answer) {
        setSubmitLoading(true);
        loadingText.textContent = answer
            ? 'Evaluating your answer...'
            : 'Processing skipped question...';

        try {
            const res = await fetch(`/api/interview/${SESSION_ID}/answer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer: answer }),
            });

            const data = await res.json();
            setSubmitLoading(false);

            if (!data.success) {
                throw new Error(data.error?.message || 'Failed to evaluate answer.');
            }

            const isCompleted = data.data.completed;
            displayEvaluation(data.data.evaluation, isCompleted);

            // Update progress
            const answeredCount = data.data.question_number;
            updateProgress(answeredCount, data.data.total_questions);

            // Store next question if available
            if (!isCompleted && data.data.next_question) {
                currentQuestion = data.data.next_question;
            }
        } catch (err) {
            setSubmitLoading(false);
            showToast(err.message || 'Something went wrong. Please try again.');
            console.error('Submit answer error:', err);
        }
    }

    // ── Event Listeners ──

    // Character count
    answerInput.addEventListener('input', function () {
        charCount.textContent = this.value.length;
    });

    // Submit answer
    submitBtn.addEventListener('click', function () {
        const answer = answerInput.value.trim();
        if (!answer) {
            showToast('Please write an answer before submitting, or click "Skip Question".');
            answerInput.focus();
            return;
        }
        submitAnswer(answer);
    });

    // Allow Ctrl+Enter to submit
    answerInput.addEventListener('keydown', function (e) {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            submitBtn.click();
        }
    });

    // Skip question
    skipBtn.addEventListener('click', function () {
        submitAnswer('');
    });

    // Next question / View results
    nextBtn.addEventListener('click', function () {
        const btnText = nextBtnText.textContent;
        if (btnText.includes('Results')) {
            window.location.href = `/results/${SESSION_ID}`;
        } else {
            // Show the next question using the stored question data
            if (currentQuestion) {
                displayQuestion(currentQuestion, currentNum + 1, totalQuestions);
            } else {
                fetchCurrentQuestion();
            }
        }
    });

    // ── Initialize ──
    fetchCurrentQuestion();
})();

/**
 * results.js — Results page rendering
 * Fetches complete results and renders score ring, stats, category chart,
 * expandable Q&A accordion, and insights.
 */

(function () {
    'use strict';

    const SESSION_ID = window.SESSION_ID;
    if (!SESSION_ID) {
        window.location.href = '/';
        return;
    }

    const loadingOverlay = document.getElementById('loading-overlay');
    const toastContainer = document.getElementById('toast-container');

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

    function getScoreColor(score) {
        if (score >= 9) return '#34d399';
        if (score >= 7) return '#3b82f6';
        if (score >= 5) return '#fbbf24';
        return '#f87171';
    }

    function getScoreClass(score) {
        if (score >= 9) return 'score-excellent';
        if (score >= 7) return 'score-strong';
        if (score >= 5) return 'score-adequate';
        return 'score-poor';
    }

    function getCategoryBadgeClass(category) {
        const map = {
            'technical': 'badge-technical',
            'behavioral': 'badge-behavioral',
            'situational': 'badge-situational',
            'problem-solving': 'badge-problem-solving',
        };
        return map[category] || 'badge-technical';
    }

    function getCategoryBarColor(category) {
        const map = {
            'technical': 'var(--gradient-primary)',
            'behavioral': 'var(--gradient-warm)',
            'situational': 'var(--gradient-cool)',
            'problem-solving': 'var(--gradient-warning)',
        };
        return map[category] || 'var(--gradient-primary)';
    }

    // ── Render Functions ──

    function renderScoreRing(avgScore) {
        const circle = document.getElementById('score-ring-circle');
        const display = document.getElementById('avg-score-display');
        const circumference = 2 * Math.PI * 85; // r=85
        const offset = circumference - (avgScore / 10) * circumference;

        circle.style.stroke = getScoreColor(avgScore);
        // Animate after a brief delay
        setTimeout(() => {
            circle.style.strokeDashoffset = offset;
        }, 300);

        // Animate the number
        let current = 0;
        const target = avgScore;
        const step = target / 40;
        const interval = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(interval);
            }
            display.textContent = current.toFixed(1);
            display.className = `score-ring-value ${getScoreClass(current)}`;
        }, 30);
    }

    function renderPerformanceBadge(level) {
        const badge = document.getElementById('performance-badge');
        badge.textContent = level;
        const colors = {
            'Outstanding': 'badge-easy',
            'Strong': 'badge-technical',
            'Adequate': 'badge-medium',
            'Needs Improvement': 'badge-hard',
            'Significant Gaps': 'badge-hard',
        };
        badge.className = `badge ${colors[level] || 'badge-medium'}`;
    }

    function renderStats(aggregate, answeredCount) {
        document.getElementById('stat-avg').textContent = aggregate.average_score.toFixed(1);
        document.getElementById('stat-high').textContent = aggregate.highest_score;
        document.getElementById('stat-low').textContent = aggregate.lowest_score;
        document.getElementById('stat-total').textContent = answeredCount;
    }

    function renderCategoryChart(categoryAverages) {
        const container = document.getElementById('category-bars');
        container.innerHTML = '';

        const entries = Object.entries(categoryAverages);
        entries.forEach(([category, avg], idx) => {
            const row = document.createElement('div');
            row.className = 'category-row';
            row.style.animation = `fadeInUp 0.4s ease-out ${0.1 * idx}s both`;

            const label = document.createElement('span');
            label.className = 'category-label';
            label.textContent = category.replace('-', ' ');

            const barTrack = document.createElement('div');
            barTrack.className = 'category-bar-track';

            const barFill = document.createElement('div');
            barFill.className = 'category-bar-fill';
            barFill.style.background = getCategoryBarColor(category);
            barFill.style.width = '0%';
            setTimeout(() => {
                barFill.style.width = `${(avg / 10) * 100}%`;
            }, 300 + idx * 100);

            barTrack.appendChild(barFill);

            const scoreLabel = document.createElement('span');
            scoreLabel.className = `category-score ${getScoreClass(avg)}`;
            scoreLabel.textContent = avg.toFixed(1);

            row.appendChild(label);
            row.appendChild(barTrack);
            row.appendChild(scoreLabel);
            container.appendChild(row);
        });
    }

    function renderResultsList(results) {
        const list = document.getElementById('results-list');
        list.innerHTML = '';

        results.forEach((item, idx) => {
            const q = item.question;
            const answer = item.answer;
            const ev = item.evaluation;
            const score = ev.score;

            const resultItem = document.createElement('div');
            resultItem.className = 'result-item fade-in';
            resultItem.style.animationDelay = `${0.05 * idx}s`;

            // Header
            const header = document.createElement('div');
            header.className = 'result-header';

            const headerLeft = document.createElement('div');
            headerLeft.className = 'result-header-left';

            const qNum = document.createElement('span');
            qNum.className = 'result-q-num';
            qNum.textContent = `Q${idx + 1}`;

            const qText = document.createElement('span');
            qText.className = 'result-q-text';
            qText.textContent = q.text;

            headerLeft.appendChild(qNum);
            headerLeft.appendChild(qText);

            const scoreBadge = document.createElement('span');
            scoreBadge.className = `result-score-badge`;
            scoreBadge.style.background = `${getScoreColor(score)}20`;
            scoreBadge.style.color = getScoreColor(score);
            scoreBadge.textContent = `${score}/10`;

            const toggle = document.createElement('span');
            toggle.className = 'result-toggle';
            toggle.textContent = '▼';

            header.appendChild(headerLeft);
            header.appendChild(scoreBadge);
            header.appendChild(toggle);

            // Body
            const body = document.createElement('div');
            body.className = 'result-body';

            // Question full text
            const qFull = document.createElement('div');
            qFull.innerHTML = `
                <div style="margin-top: var(--space-md);">
                    <span class="badge ${getCategoryBadgeClass(q.category)}" style="margin-right: 8px;">${q.category || 'technical'}</span>
                    <span class="badge badge-difficulty badge-${q.difficulty || 'medium'}">${q.difficulty || 'medium'}</span>
                </div>
                <p style="margin-top: var(--space-md); font-size: var(--font-base); line-height: 1.7; color: var(--text-primary);">${q.text}</p>
            `;
            body.appendChild(qFull);

            // Answer
            const ansLabel = document.createElement('div');
            ansLabel.className = 'result-answer-label';
            ansLabel.textContent = 'Your Answer';
            body.appendChild(ansLabel);

            const ansBlock = document.createElement('div');
            ansBlock.className = 'result-answer';
            ansBlock.textContent = answer || '(Skipped)';
            body.appendChild(ansBlock);

            // Evaluation
            const evalBlock = document.createElement('div');
            evalBlock.style.marginTop = 'var(--space-lg)';
            evalBlock.innerHTML = `
                <div class="evaluation-summary" style="margin-bottom: var(--space-md);">${ev.summary}</div>
                ${renderEvalSection('✅ Strengths', ev.strengths, 'strength-list')}
                ${renderEvalSection('⚠️ Weaknesses', ev.weaknesses, 'weakness-list')}
                ${renderEvalSection('💡 Suggestions', ev.improvements, 'improvement-list')}
            `;
            body.appendChild(evalBlock);

            resultItem.appendChild(header);
            resultItem.appendChild(body);

            // Toggle expand/collapse
            header.addEventListener('click', () => {
                resultItem.classList.toggle('expanded');
            });

            list.appendChild(resultItem);
        });
    }

    function renderEvalSection(title, items, listClass) {
        if (!items || items.length === 0) return '';
        const listItems = items.map(i => `<li>${escapeHtml(i)}</li>`).join('');
        return `
            <div style="margin-bottom: var(--space-md);">
                <h4 style="font-size: var(--font-sm); font-weight: 700; margin-bottom: var(--space-sm); color: var(--text-muted);">${title}</h4>
                <ul class="evaluation-list ${listClass}">${listItems}</ul>
            </div>
        `;
    }

    function renderInsights(strengths, weaknesses) {
        const strengthsList = document.getElementById('key-strengths');
        const weaknessesList = document.getElementById('key-weaknesses');

        strengthsList.innerHTML = '';
        weaknessesList.innerHTML = '';

        (strengths || []).slice(0, 6).forEach(s => {
            const li = document.createElement('li');
            li.textContent = s;
            strengthsList.appendChild(li);
        });

        (weaknesses || []).slice(0, 6).forEach(w => {
            const li = document.createElement('li');
            li.textContent = w;
            weaknessesList.appendChild(li);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ── Download Report ──

    function generateReport(data) {
        const d = data.data;
        const agg = d.aggregate;
        let report = '';
        report += '═══════════════════════════════════════════════\n';
        report += '         AI MOCK INTERVIEW REPORT\n';
        report += '═══════════════════════════════════════════════\n\n';
        report += `Role: ${d.role}\n`;
        report += `Experience Level: ${d.experience_level}\n`;
        report += `Questions Answered: ${d.answered_questions} / ${d.total_questions}\n`;
        report += `Average Score: ${agg.average_score} / 10\n`;
        report += `Performance: ${agg.performance_level}\n`;
        report += `Highest Score: ${agg.highest_score} | Lowest Score: ${agg.lowest_score}\n\n`;

        report += '── Category Averages ──\n';
        Object.entries(agg.category_averages).forEach(([cat, avg]) => {
            report += `  ${cat}: ${avg}/10\n`;
        });

        report += '\n── Score Distribution ──\n';
        Object.entries(agg.score_distribution).forEach(([range, count]) => {
            report += `  ${range}: ${count} question(s)\n`;
        });

        report += '\n\n═══════════════════════════════════════════════\n';
        report += '         DETAILED BREAKDOWN\n';
        report += '═══════════════════════════════════════════════\n\n';

        d.results.forEach((item, idx) => {
            report += `─── Question ${idx + 1} [${item.question.category}] [${item.question.difficulty}] ───\n`;
            report += `Q: ${item.question.text}\n\n`;
            report += `A: ${item.answer || '(Skipped)'}\n\n`;
            report += `Score: ${item.evaluation.score}/10\n`;
            report += `Summary: ${item.evaluation.summary}\n`;
            if (item.evaluation.strengths.length) {
                report += `Strengths:\n`;
                item.evaluation.strengths.forEach(s => report += `  • ${s}\n`);
            }
            if (item.evaluation.weaknesses.length) {
                report += `Weaknesses:\n`;
                item.evaluation.weaknesses.forEach(w => report += `  • ${w}\n`);
            }
            if (item.evaluation.improvements.length) {
                report += `Suggestions:\n`;
                item.evaluation.improvements.forEach(i => report += `  • ${i}\n`);
            }
            report += '\n';
        });

        report += '═══════════════════════════════════════════════\n';
        report += '  Key Strengths:\n';
        agg.key_strengths.forEach(s => report += `    • ${s}\n`);
        report += '\n  Areas to Improve:\n';
        agg.key_weaknesses.forEach(w => report += `    • ${w}\n`);
        report += '\n═══════════════════════════════════════════════\n';
        report += '  Generated by InterviewAI\n';
        report += '═══════════════════════════════════════════════\n';

        return report;
    }

    // ── Main ──

    async function loadResults() {
        try {
            const res = await fetch(`/api/interview/${SESSION_ID}/results`);
            const data = await res.json();

            if (!data.success) {
                throw new Error(data.error?.message || 'Failed to load results.');
            }

            const d = data.data;
            const agg = d.aggregate;

            // Set meta
            document.getElementById('meta-role').textContent = d.role;
            document.getElementById('meta-level').textContent = d.experience_level;
            document.getElementById('results-subtitle').textContent =
                `${d.role} • ${d.experience_level} • ${d.answered_questions} questions answered`;

            // Render sections
            renderScoreRing(agg.average_score);
            renderPerformanceBadge(agg.performance_level);
            renderStats(agg, d.answered_questions);
            renderCategoryChart(agg.category_averages);
            renderResultsList(d.results);
            renderInsights(agg.key_strengths, agg.key_weaknesses);

            // Download button
            document.getElementById('download-btn').addEventListener('click', () => {
                const report = generateReport(data);
                const blob = new Blob([report], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `interview-report-${d.role.replace(/\s+/g, '-').toLowerCase()}.txt`;
                a.click();
                URL.revokeObjectURL(url);
                showToast('Report downloaded!', 'success');
            });

            // Hide loading
            loadingOverlay.classList.remove('active');
        } catch (err) {
            loadingOverlay.classList.remove('active');
            showToast(err.message || 'Failed to load results.');
            console.error('Load results error:', err);
        }
    }

    loadResults();
})();

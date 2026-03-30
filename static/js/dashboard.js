/**
 * dashboard.js — Fetch and render user interview history
 */

(function () {
    'use strict';

    const greeting = document.getElementById('user-greeting');
    const tableContainer = document.getElementById('table-container');
    const table = document.getElementById('interviews-table');
    const tbody = document.getElementById('interviews-body');
    const emptyState = document.getElementById('empty-state');

    async function loadDashboard() {
        try {
            // First fetch user profile to greet them
            const meRes = await fetch('/api/auth/me');
            const meData = await meRes.json();
            if (meData.success) {
                greeting.textContent = `Hello, ${meData.data.name.split(' ')[0]}`;
            }

            // Fetch interviews
            const res = await fetch('/api/dashboard/interviews');
            const data = await res.json();

            if (!data.success) {
                throw new Error(data.error?.message || 'Failed to load interviews.');
            }

            renderInterviews(data.data.interviews);
        } catch (err) {
            console.error(err);
        }
    }

    function renderInterviews(interviews) {
        if (!interviews || interviews.length === 0) {
            table.classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        table.classList.remove('hidden');
        tbody.innerHTML = '';

        interviews.forEach(inv => {
            const tr = document.createElement('tr');
            
            // Format dates
            const date = new Date(inv.created_at);
            const dateStr = date.toLocaleDateString(undefined, {
                year: 'numeric', month: 'short', day: 'numeric'
            });

            // Handle role & level
            const roleStr = inv.role;
            const levelStr = inv.experience_level.split(' ')[0]; // E.g., "Entry"
            
            // Context badge (if CV uploaded)
            const contextStr = inv.cv_filename ? `<span class="badge badge-technical" style="font-size: 0.65rem;">CV Attached</span>` : '';

            // Status format
            let statusBadge = '';
            if (inv.status === 'completed') {
                statusBadge = `<span class="badge badge-easy" style="font-size: 0.65rem;">Completed</span>`;
            } else {
                statusBadge = `<span class="badge badge-medium" style="font-size: 0.65rem;">In Progress</span>`;
            }

            // Score format
            let scoreStr = '—';
            if (inv.status === 'completed' && inv.average_score) {
                let colorClass = 'text-primary';
                const s = inv.average_score;
                if (s >= 8.5) colorClass = 'score-excellent';
                else if (s >= 7) colorClass = 'score-strong';
                else if (s >= 5.5) colorClass = 'score-adequate';
                else colorClass = 'score-poor';

                scoreStr = `<strong class="${colorClass}">${s.toFixed(1)}</strong> <span style="font-size: 0.8em; color: var(--text-muted)">/ 10</span>`;
            }

            // Actions
            let actionHtml = '';
            if (inv.status === 'completed') {
                actionHtml = `<a href="/results/${inv.id}" class="btn btn-secondary" style="padding: 4px 12px; font-size: 0.8rem;">View Results</a>`;
            } else {
                actionHtml = `<a href="/interview/${inv.id}" class="btn btn-primary" style="padding: 4px 12px; font-size: 0.8rem;">Resume</a>`;
            }

            tr.innerHTML = `
                <td style="white-space: nowrap;">${dateStr}</td>
                <td style="font-weight: 600;">${roleStr}</td>
                <td>${levelStr}</td>
                <td>${contextStr}</td>
                <td>${statusBadge}</td>
                <td>${scoreStr}</td>
                <td>${actionHtml}</td>
            `;

            tbody.appendChild(tr);
        });
    }

    loadDashboard();
})();

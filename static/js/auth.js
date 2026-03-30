/**
 * auth.js — Auth flows (login, signup, logout)
 */

(function () {
    'use strict';

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

    // --- Signup Form ---
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        const nameInput = document.getElementById('signup-name');
        const emailInput = document.getElementById('signup-email');
        const passwordInput = document.getElementById('signup-password');
        const confirmInput = document.getElementById('signup-confirm');
        const btn = document.getElementById('signup-btn');
        const btnText = document.getElementById('signup-btn-text');
        const spinner = document.getElementById('signup-btn-spinner');

        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            btn.disabled = true;
            btnText.textContent = 'Creating Account...';
            spinner.classList.remove('hidden');

            try {
                const res = await fetch('/api/auth/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: nameInput.value,
                        email: emailInput.value,
                        password: passwordInput.value,
                        confirm_password: confirmInput.value
                    })
                });
                
                const data = await res.json();
                
                if (!data.success) {
                    throw new Error(data.error?.message || 'Signup failed');
                }
                
                showToast('Account created successfully!', 'success');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1000);
            } catch (err) {
                showToast(err.message);
                btn.disabled = false;
                btnText.textContent = 'Sign Up';
                spinner.classList.add('hidden');
            }
        });
    }

    // --- Login Form ---
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        const emailInput = document.getElementById('login-email');
        const passwordInput = document.getElementById('login-password');
        const btn = document.getElementById('login-btn');
        const btnText = document.getElementById('login-btn-text');
        const spinner = document.getElementById('login-btn-spinner');

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            btn.disabled = true;
            btnText.textContent = 'Logging In...';
            spinner.classList.remove('hidden');

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: emailInput.value,
                        password: passwordInput.value
                    })
                });
                
                const data = await res.json();
                
                if (!data.success) {
                    throw new Error(data.error?.message || 'Login failed');
                }
                
                window.location.href = '/dashboard';
            } catch (err) {
                showToast(err.message);
                btn.disabled = false;
                btnText.textContent = 'Log In';
                spinner.classList.add('hidden');
            }
        });
    }

    // --- Logout Button ---
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                await fetch('/api/auth/logout', { method: 'POST' });
                window.location.href = '/login';
            } catch (err) {
                console.error('Logout failed:', err);
            }
        });
    }

})();

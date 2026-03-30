/**
 * setup.js — Landing page logic
 * Handles form validation, file upload UI, API call to start interview, loading states.
 */

(function () {
    'use strict';

    // DOM Elements
    const form = document.getElementById('interview-setup-form');
    const roleSelect = document.getElementById('role-select');
    const levelSelect = document.getElementById('level-select');
    
    // File drop
    const fileDropArea = document.getElementById('file-drop-area');
    const fileDropText = document.getElementById('file-drop-text');
    const filePreview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    const removeFile = document.getElementById('remove-file');
    const cvUpload = document.getElementById('cv-upload');
    const jdInput = document.getElementById('jd-input');

    const startBtn = document.getElementById('start-btn');
    const startBtnText = document.getElementById('start-btn-text');
    const startBtnSpinner = document.getElementById('start-btn-spinner');
    const loadingOverlay = document.getElementById('loading-overlay');
    const toastContainer = document.getElementById('toast-container');

    let selectedFile = null;

    // Toast notification
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

    // Set loading state
    function setLoading(loading) {
        startBtn.disabled = loading;
        startBtnText.textContent = loading ? 'Generating Questions...' : 'Start Interview';
        startBtnSpinner.classList.toggle('hidden', !loading);
        loadingOverlay.classList.toggle('active', loading);
    }

    // --- File Drag & Drop Logic ---
    if (fileDropArea && cvUpload) {
        const preventDefaults = (e) => {
            e.preventDefault();
            e.stopPropagation();
        };

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, () => {
                fileDropArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, () => {
                fileDropArea.classList.remove('dragover');
            }, false);
        });

        fileDropArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }, false);

        cvUpload.addEventListener('change', function() {
            handleFiles(this.files);
        });

        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
                const validExtensions = ['.pdf', '.docx', '.txt'];
                
                const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
                
                if (validTypes.includes(file.type) || validExtensions.includes(ext)) {
                    if (file.size > 5 * 1024 * 1024) {
                        showToast('File is too large. Max size is 5MB.');
                        return;
                    }
                    selectedFile = file;
                    fileDropText.style.display = 'none';
                    filePreview.style.display = 'flex';
                    fileName.textContent = file.name;
                    cvUpload.files = files; // Sync input
                } else {
                    showToast('Unsupported file format. Please upload PDF or DOCX.');
                }
            }
        }

        removeFile.addEventListener('click', (e) => {
            e.stopPropagation(); // prevent clicking the drop area and opening file dialog
            selectedFile = null;
            cvUpload.value = ''; // clear input
            filePreview.style.display = 'none';
            fileDropText.style.display = 'block';
        });
    }


    // --- Form Submission ---
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            const role = roleSelect.value;
            const level = levelSelect.value;
            const jdText = jdInput ? jdInput.value.trim() : '';

            if (!role) {
                showToast('Please select a job role.');
                roleSelect.focus();
                return;
            }
            if (!level) {
                showToast('Please select an experience level.');
                levelSelect.focus();
                return;
            }

            setLoading(true);

            try {
                // Use FormData to support multipart file uploads
                const formData = new FormData();
                formData.append('role', role);
                formData.append('experience_level', level);
                if (jdText) {
                    formData.append('jd_text', jdText);
                }
                if (selectedFile) {
                    formData.append('cv_file', selectedFile);
                }

                const response = await fetch('/api/interview/start', {
                    method: 'POST',
                    body: formData, // No 'Content-Type' header needed for FormData; browser sets it with boundaries
                });

                const data = await response.json();

                if (!data.success) {
                    // Check if unauthorized
                    if (response.status === 401) {
                        window.location.href = '/login';
                        return;
                    }
                    throw new Error(data.error?.message || 'Failed to start interview.');
                }

                // Redirect to interview page
                const sessionId = data.data.session_id;
                window.location.href = `/interview/${sessionId}`;
            } catch (err) {
                setLoading(false);
                showToast(err.message || 'Something went wrong. Please try again.');
                console.error('Start interview error:', err);
            }
        });
    }

    // Add subtle animation to select dropdowns on change
    if (roleSelect) {
        roleSelect.addEventListener('change', function () {
            this.style.borderColor = 'var(--accent-indigo)';
            setTimeout(() => { this.style.borderColor = ''; }, 1500);
        });
    }

    if (levelSelect) {
        levelSelect.addEventListener('change', function () {
            this.style.borderColor = 'var(--accent-indigo)';
            setTimeout(() => { this.style.borderColor = ''; }, 1500);
        });
    }
})();

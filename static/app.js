/**
 * CrowdLens — Frontend controller
 * ================================
 * Handles: file selection, drag-and-drop, AJAX upload, state rendering.
 *
 * The backend contract (what /analyze returns):
 *   { count, original_url, density_map_url, processing_time }
 *
 * This file never needs to change when the real model is plugged in.
 */

'use strict';

// ── Element refs ───────────────────────────────────────────────────────────
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const dzIdle = document.getElementById('dz-idle');
const dzPreview = document.getElementById('dz-preview');
const previewImg = document.getElementById('preview-img');
const fileMeta = document.getElementById('file-meta');
const fileNameEl = document.getElementById('file-name');
const fileSizeEl = document.getElementById('file-size');
const analyzeBtn = document.getElementById('analyze-btn');
const btnLabel = analyzeBtn.querySelector('.btn__label');
const btnSpinner = analyzeBtn.querySelector('.btn__spinner');
const errorAlert = document.getElementById('error-alert');
const errorMsgEl = document.getElementById('error-msg');

const stateEmpty = document.getElementById('state-empty');
const stateLoading = document.getElementById('state-loading');
const stateResult = document.getElementById('state-result');

const statCount = document.getElementById('stat-count');
const statTime = document.getElementById('stat-time');
const resultOrig = document.getElementById('result-original');
const resultDensity = document.getElementById('result-density');
const resetBtn = document.getElementById('reset-btn');

// ── App state ──────────────────────────────────────────────────────────────
let currentFile = null;

// ── Utilities ──────────────────────────────────────────────────────────────
function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1_048_576).toFixed(1)} MB`;
}

function showError(msg) {
    errorMsgEl.textContent = msg;
    errorAlert.classList.remove('hidden');
}
function hideError() {
    errorAlert.classList.add('hidden');
}

// ── State machine ──────────────────────────────────────────────────────────
function setUIState(state) {
    // 'idle' | 'loading' | 'result'
    stateEmpty.classList.toggle('hidden', state !== 'idle');
    stateLoading.classList.toggle('hidden', state !== 'loading');
    stateResult.classList.toggle('hidden', state !== 'result');

    const busy = state === 'loading';
    analyzeBtn.disabled = busy || !currentFile;
    btnLabel.textContent = busy ? 'Đang xử lý…' : 'Phân tích ảnh';
    btnSpinner.classList.toggle('hidden', !busy);
}

// ── File handling ──────────────────────────────────────────────────────────
const ALLOWED_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/bmp']);

function applyFile(file) {
    hideError();

    if (!ALLOWED_TYPES.has(file.type)) {
        showError('Định dạng không hỗ trợ. Vui lòng chọn ảnh PNG, JPG, hoặc WEBP.');
        return;
    }
    if (file.size > 16 * 1024 * 1024) {
        showError('File vượt quá giới hạn 16 MB. Vui lòng chọn ảnh nhỏ hơn.');
        return;
    }

    currentFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = e => {
        previewImg.src = e.target.result;
        dzIdle.classList.add('hidden');
        dzPreview.classList.remove('hidden');
    };
    reader.readAsDataURL(file);

    // File meta row
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatBytes(file.size);
    fileMeta.classList.remove('hidden');

    analyzeBtn.disabled = false;
    setUIState('idle');
}

// Input change
fileInput.addEventListener('change', e => {
    if (e.target.files[0]) applyFile(e.target.files[0]);
});

// ── Drag-and-drop ──────────────────────────────────────────────────────────
dropzone.addEventListener('dragover', e => {
    e.preventDefault();
    dropzone.classList.add('drag-active');
});
['dragleave', 'dragend'].forEach(type =>
    dropzone.addEventListener(type, () => dropzone.classList.remove('drag-active'))
);
dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('drag-active');
    const file = e.dataTransfer.files[0];
    if (file) applyFile(file);
});

// Keyboard activation
dropzone.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput.click();
    }
});

// ── Analyze ────────────────────────────────────────────────────────────────
analyzeBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    hideError();
    setUIState('loading');

    const formData = new FormData();
    formData.append('image', currentFile);

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `Server returned ${response.status}`);
        }

        renderResult(data);

    } catch (err) {
        setUIState('idle');
        showError(err.message || 'Đã xảy ra lỗi. Vui lòng thử lại.');
    }
});

// ── Render result ──────────────────────────────────────────────────────────
function renderResult(data) {
    statCount.textContent = Number(data.count).toLocaleString();
    statTime.textContent = `${data.processing_time}s`;
    resultOrig.src = data.original_url;
    resultDensity.src = data.density_map_url;
    setUIState('result');
}

// ── Reset ──────────────────────────────────────────────────────────────────
resetBtn.addEventListener('click', () => {
    currentFile = null;
    fileInput.value = '';
    previewImg.src = '';

    dzPreview.classList.add('hidden');
    dzIdle.classList.remove('hidden');
    fileMeta.classList.add('hidden');
    fileNameEl.textContent = '—';
    fileSizeEl.textContent = '—';

    analyzeBtn.disabled = true;
    btnLabel.textContent = 'Phân tích ảnh';

    hideError();
    setUIState('idle');
});
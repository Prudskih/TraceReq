(() => {
  const API_BASE = '/api';

  // --- DOM ---
  const elGrid = document.getElementById('projectsGrid');
  const btnCreate = document.getElementById('btnCreate');

  const modalBackdrop = document.getElementById('modalBackdrop');
  const modalTitle = document.getElementById('modalTitle');

  const btnCloseModal = document.getElementById('btnCloseModal');
  const btnCancel = document.getElementById('btnCancel');
  const btnSave = document.getElementById('btnSave');

  const inputName = document.getElementById('projectName');
  const inputDesc = document.getElementById('projectDesc');
  const modalError = document.getElementById('modalError');

  // Если хоть что-то не найдено — JS упадёт. Лучше явно проверить:
  const required = [
    elGrid, btnCreate, modalBackdrop, modalTitle,
    btnCloseModal, btnCancel, btnSave, inputName, inputDesc, modalError
  ];
  if (required.some(x => !x)) {
    console.error('projects.js: some DOM elements not found. Check ids in login.html');
    return;
  }

  let mode = 'create'; // create | edit
  let editingId = null;

  function showError(msg) {
    modalError.textContent = msg || '';
    modalError.style.display = msg ? 'block' : 'none';
  }

  function openModalCreate() {
    mode = 'create';
    editingId = null;
    modalTitle.textContent = 'Создать проект';
    inputName.value = '';
    inputDesc.value = '';
    showError('');
    modalBackdrop.style.display = 'flex';
    inputName.focus();
  }

  function openModalEdit(p) {
    mode = 'edit';
    editingId = p.id;
    modalTitle.textContent = 'Редактировать проект';
    inputName.value = p.name || '';
    inputDesc.value = p.description || '';
    showError('');
    modalBackdrop.style.display = 'flex';
    inputName.focus();
  }

  function closeModal() {
    modalBackdrop.style.display = 'none';
  }

  async function apiJson(url, opts = {}) {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...opts,
    });

    let payload = null;
    try { payload = await res.json(); } catch (_) {}

    if (!res.ok) {
      const msg = payload?.error || payload?.message || `HTTP ${res.status}`;
      const err = new Error(msg);
      err.status = res.status;
      err.payload = payload;
      throw err;
    }
    return payload;
  }

  function escapeHtml(s) {
    return String(s ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function renderProjects(projects) {
    if (!projects.length) {
      elGrid.innerHTML = `
        <div class="muted" style="padding:20px;">
          Проектов пока нет. Нажмите «Создать проект».
        </div>
      `;
      return;
    }

    elGrid.innerHTML = projects.map(p => {
      const name = escapeHtml(p.name);
      const desc = escapeHtml(p.description || '');
      return `
        <div class="requirement-card">
          <div class="requirement-title">${name}</div>
          <div class="requirement-description">${desc}</div>

          <div class="requirement-info">
            <div>Проект #${p.id}</div>
          </div>

          <div class="actions">
            <button class="btn btn-primary btn-small" type="button"
                    data-action="open" data-id="${p.id}">Открыть</button>
            <button class="btn btn-secondary btn-small" type="button"
                    data-action="edit" data-id="${p.id}">Редактировать</button>
            <button class="btn btn-danger btn-small" type="button"
                    data-action="delete" data-id="${p.id}">Удалить</button>
          </div>
        </div>
      `;
    }).

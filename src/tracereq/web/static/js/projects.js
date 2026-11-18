const API_BASE = '/api';

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

let mode = 'create';   // create | edit
let editingId = null;

/* -------------------- helpers -------------------- */

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

function openModalEdit(project) {
  mode = 'edit';
  editingId = project.id;
  modalTitle.textContent = 'Редактировать проект';
  inputName.value = project.name || '';
  inputDesc.value = project.description || '';
  showError('');
  modalBackdrop.style.display = 'flex';
  inputName.focus();
}

function closeModal() {
  modalBackdrop.style.display = 'none';
}

async function apiJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (_) {}

  if (!response.ok) {
    const err = new Error(payload?.error || `HTTP ${response.status}`);
    err.status = response.status;
    err.payload = payload;
    throw err;
  }
  return payload;
}

function escapeHtml(text) {
  return String(text ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

/* -------------------- render -------------------- */

function renderProjectCard(project) {
  return `
    <div class="requirement-card">
      <div class="requirement-title">${escapeHtml(project.name)}</div>
      <div class="requirement-description">${escapeHtml(project.description || '')}</div>
      <div class="actions" style="margin-top:12px; display:flex; gap:8px;">
        <button class="btn btn-primary" data-action="open" data-id="${project.id}">Открыть</button>
        <button class="btn btn-secondary" data-action="edit" data-id="${project.id}">Редактировать</button>
        <button class="btn btn-danger" data-action="delete" data-id="${project.id}">Удалить</button>
      </div>
    </div>
  `;
}

async function loadProjects() {
  elGrid.innerHTML = '<p style="padding:20px;color:#7f8c8d;">Загрузка проектов...</p>';

  const projects = await apiJson(`${API_BASE}/projects`);

  if (!projects.length) {
    elGrid.innerHTML = '<p style="padding:20px;color:#7f8c8d;">Проектов пока нет</p>';
    return;
  }

  elGrid.innerHTML = projects.map(renderProjectCard).join('');
}

/* -------------------- actions -------------------- */

async function saveProject() {
  const name = inputName.value.trim();
  const description = inputDesc.value.trim();

  if (!name) {
    showError('Название проекта обязательно');
    return;
  }

  btnSave.disabled = true;
  showError('');

  try {
    if (mode === 'create') {
      await apiJson(`${API_BASE}/projects`, {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      });
    } else {
      await apiJson(`${API_BASE}/projects/${editingId}`, {
        method: 'PUT',
        body: JSON.stringify({ name, description }),
      });
    }

    closeModal();
    await loadProjects();
  } catch (e) {
    showError(e.payload?.error || 'Ошибка сохранения проекта');
  } finally {
    btnSave.disabled = false;
  }
}

async function deleteProject(id) {
  if (!confirm('Удалить проект? Это действие необратимо.')) return;

  try {
    await apiJson(`${API_BASE}/projects/${id}`, { method: 'DELETE' });
    await loadProjects();
  } catch (e) {
    alert(e.payload?.details || e.message || 'Ошибка удаления проекта');
  }
}

/* -------------------- events -------------------- */

btnCreate.addEventListener('click', openModalCreate);
btnCloseModal.addEventListener('click', closeModal);
btnCancel.addEventListener('click', closeModal);
btnSave.addEventListener('click', saveProject);

modalBackdrop.addEventListener('click', (e) => {
  if (e.target === modalBackdrop) closeModal();
});

elGrid.addEventListener('click', async (e) => {
  const btn = e.target.closest('button[data-action]');
  if (!btn) return;

  const action = btn.dataset.action;
  const id = Number(btn.dataset.id);

  if (action === 'open') {
    window.location.href = `/project/${id}`;
    return;
  }

  if (action === 'edit') {
    const projects = await apiJson(`${API_BASE}/projects`);
    const project = projects.find(p => p.id === id);
    if (project) openModalEdit(project);
    return;
  }

  if (action === 'delete') {
    await deleteProject(id);
  }
});

/* -------------------- init -------------------- */

loadProjects().catch(err => {
  elGrid.innerHTML = `<p style="padding:20px;color:#c0392b;">${escapeHtml(err.message)}</p>`;
});

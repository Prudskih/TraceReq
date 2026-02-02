 // Главный JavaScript файл для работы с требованиями

const API_BASE = '/api';

function projectApi(path) {
  const pid = window.CURRENT_PROJECT_ID;
  return `${API_BASE}/projects/${pid}${path}`;
}

let allRequirements = [];
let currentView = 'grid';
let mindMapNetwork = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    loadRequirements();
    setupEventListeners();
});


// Настройка обработчиков событий
function setupEventListeners() {
    // Кнопка добавления требования
    document.getElementById('addRequirementBtn').addEventListener('click', function() {
        openRequirementModal();
    });
    
    // Кнопки экспорта
    document.getElementById('exportBtn').addEventListener('click', function() {
        exportToExcel();
    });
    
    document.getElementById('exportMatrixBtn').addEventListener('click', function() {
        exportMatrixToExcel();
    });
    
    // Переключение представлений
    document.getElementById('gridViewBtn').addEventListener('click', function() {
        switchView('grid');
    });
    
    document.getElementById('matrixViewBtn').addEventListener('click', function() {
        switchView('matrix');
    });
    
    document.getElementById('mindMapViewBtn').addEventListener('click', function() {
        switchView('mindmap');
    });
    
    // Закрытие модальных окон
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });
    
    // Отмена в формах
    document.getElementById('cancelBtn').addEventListener('click', function() {
        document.getElementById('requirementModal').style.display = 'none';
    });
    
    document.getElementById('cancelLinkBtn').addEventListener('click', function() {
        document.getElementById('linkModal').style.display = 'none';
    });
    
    // Обработка формы требования
    document.getElementById('requirementForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveRequirement();
    });
    
    // Обработка формы связи
    document.getElementById('linkForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveLink();
    });
    
    // Закрытие модальных окон при клике вне их
    window.addEventListener('click', function(event) {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
}

// Переключение представлений
function switchView(viewName) {
    currentView = viewName;
    
    // Обновление кнопок
    document.querySelectorAll('.btn-view').forEach(btn => btn.classList.remove('active'));
    if (viewName === 'grid') {
        document.getElementById('gridViewBtn').classList.add('active');
    } else if (viewName === 'matrix') {
        document.getElementById('matrixViewBtn').classList.add('active');
    } else if (viewName === 'mindmap') {
        document.getElementById('mindMapViewBtn').classList.add('active');
    }
    
    // Переключение контейнеров
    document.querySelectorAll('.view-container').forEach(container => {
        container.classList.remove('active');
    });
    
    if (viewName === 'grid') {
        document.getElementById('gridView').classList.add('active');
        displayRequirements(allRequirements);
    } else if (viewName === 'matrix') {
        document.getElementById('matrixView').classList.add('active');
        displayMatrix();
    } else if (viewName === 'mindmap') {
        document.getElementById('mindMapView').classList.add('active');
        displayMindMap();
    }
}

// Загрузка всех требований
async function loadRequirements() {
    try {
        const response = await fetch(projectApi('/requirements'));
        allRequirements = await response.json();
        if (currentView === 'grid') {
            displayRequirements(allRequirements);
        } else if (currentView === 'matrix') {
            displayMatrix();
        } else if (currentView === 'mindmap') {
            displayMindMap();
        }
    } catch (error) {
        console.error('Ошибка загрузки требований:', error);
        alert('Ошибка загрузки требований');
    }
}

// Отображение требований в сетке
function displayRequirements(requirements) {
    const grid = document.getElementById('requirementsGrid');
    grid.innerHTML = '';
    
    if (requirements.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">Нет требований. Добавьте первое требование.</p>';
        return;
    }
    
    requirements.forEach(requirement => {
        const card = createRequirementCard(requirement);
        grid.appendChild(card);
    });
}

// Создание карточки требования
function createRequirementCard(requirement) {
    const card = document.createElement('div');
    card.className = 'requirement-card';
    card.dataset.id = requirement.id;
    card.style.cursor = 'pointer';
    card.addEventListener('click', function(e) {
        if (!e.target.closest('.requirement-actions') && !e.target.closest('button')) {
            viewRequirementDetail(requirement.id);
        }
    });
    
    const statusClass = getStatusClass(requirement.status);
    const priorityClass = getPriorityClass(requirement.priority);
    
    // Формирование списка связей
    let linksHtml = '';
    if (requirement.outgoing_links && requirement.outgoing_links.length > 0) {
        linksHtml += '<div class="requirement-links"><strong>Исходящие связи:</strong>';
        requirement.outgoing_links.forEach(link => {
            const linkClass = getLinkTypeClass(link.link_type);
            linksHtml += `<div class="link-item clickable" onclick="event.stopPropagation(); viewRequirementDetail(${link.target_requirement_id})">
                <span class="link-type ${linkClass}">${escapeHtml(link.link_type)}</span>
                → Требование #${link.target_requirement_id}
            </div>`;
        });
        linksHtml += '</div>';
    }
    
    if (requirement.incoming_links && requirement.incoming_links.length > 0) {
        linksHtml += '<div class="requirement-links"><strong>Входящие связи:</strong>';
        requirement.incoming_links.forEach(link => {
            const linkClass = getLinkTypeClass(link.link_type);
            linksHtml += `<div class="link-item clickable" onclick="event.stopPropagation(); viewRequirementDetail(${link.source_requirement_id})">
                <span class="link-type ${linkClass}">${escapeHtml(link.link_type)}</span>
                ← Требование #${link.source_requirement_id}
            </div>`;
        });
        linksHtml += '</div>';
    }
    
    card.innerHTML = `
        <div class="requirement-card-header">
            <span class="requirement-id">#${requirement.id}</span>
            <div class="requirement-actions" onclick="event.stopPropagation()">
                <button class="btn btn-small btn-primary" onclick="editRequirement(${requirement.id})">Изменить</button>
                <button class="btn btn-small btn-danger" onclick="deleteRequirement(${requirement.id})">Удалить</button>
            </div>
        </div>
        <div class="requirement-title">${escapeHtml(requirement.title)}</div>
        <div class="requirement-description">${escapeHtml(requirement.description || '')}</div>
        <div class="requirement-meta">
            <span class="badge badge-type">${escapeHtml(requirement.requirement_type)}</span>
            <span class="badge badge-status ${statusClass}">${escapeHtml(requirement.status)}</span>
            <span class="badge badge-priority ${priorityClass}">${escapeHtml(requirement.priority)}</span>
        </div>
        ${linksHtml}
        <div class="requirement-info">
            ${requirement.author ? `<div>Автор: ${escapeHtml(requirement.author)}</div>` : ''}
            ${requirement.source ? `<div>Источник: ${escapeHtml(requirement.source)}</div>` : ''}
            ${requirement.created_at ? `<div>Создано: ${formatDate(requirement.created_at)}</div>` : ''}
        </div>
        <div class="requirement-actions" style="margin-top: 10px;" onclick="event.stopPropagation()">
            <button class="btn btn-small btn-secondary" onclick="openLinkModal(${requirement.id})">Добавить связь</button>
            <button class="btn btn-small btn-secondary" onclick="viewHistory(${requirement.id})">История</button>
        </div>
    `;
    
    return card;
}

// Получение класса для типа связи
function getLinkTypeClass(linkType) {
    const classMap = {
        'Реализует': 'implements',
        'Зависит от': 'depends',
        'Противоречит': 'contradicts'
    };
    return classMap[linkType] || '';
}

// Получение класса для статуса
function getStatusClass(status) {
    const statusMap = {
        'Утверждено': 'approved',
        'В работе': 'in-progress',
        'Отклонено': 'rejected'
    };
    return statusMap[status] || '';
}

// Получение класса для приоритета
function getPriorityClass(priority) {
    const priorityMap = {
        'Критический': 'critical',
        'Высокий': 'high'
    };
    return priorityMap[priority] || '';
}

// Просмотр деталей требования
async function viewRequirementDetail(requirementId) {
    try {
        const response = await fetch(projectApi(`/requirements/${requirementId}`));
        const requirement = await response.json();
        
        const modal = document.getElementById('detailModal');
        const title = document.getElementById('detailTitle');
        const content = document.getElementById('detailContent');
        
        title.textContent = `Требование #${requirement.id}: ${requirement.title}`;
        
        // Формирование связей
        let linksHtml = '';
        if (requirement.outgoing_links && requirement.outgoing_links.length > 0) {
            linksHtml += '<div class="detail-section"><h3>Исходящие связи</h3>';
            requirement.outgoing_links.forEach(link => {
                const targetReq = allRequirements.find(r => r.id === link.target_requirement_id);
                const linkClass = getLinkTypeClass(link.link_type);
                linksHtml += `<div class="link-item clickable" onclick="viewRequirementDetail(${link.target_requirement_id}); document.getElementById('detailModal').style.display='block';">
                    <span class="link-type ${linkClass}">${escapeHtml(link.link_type)}</span>
                    → <strong>#${link.target_requirement_id}</strong>: ${escapeHtml(targetReq ? targetReq.title : 'Неизвестно')}
                </div>`;
            });
            linksHtml += '</div>';
        }
        
        if (requirement.incoming_links && requirement.incoming_links.length > 0) {
            linksHtml += '<div class="detail-section"><h3>Входящие связи</h3>';
            requirement.incoming_links.forEach(link => {
                const sourceReq = allRequirements.find(r => r.id === link.source_requirement_id);
                const linkClass = getLinkTypeClass(link.link_type);
                linksHtml += `<div class="link-item clickable" onclick="viewRequirementDetail(${link.source_requirement_id}); document.getElementById('detailModal').style.display='block';">
                    <span class="link-type ${linkClass}">${escapeHtml(link.link_type)}</span>
                    ← <strong>#${link.source_requirement_id}</strong>: ${escapeHtml(sourceReq ? sourceReq.title : 'Неизвестно')}
                </div>`;
            });
            linksHtml += '</div>';
        }
        
        content.innerHTML = `
            <div class="detail-section">
                <h3>Основная информация</h3>
                <div class="detail-field">
                    <label>Название:</label>
                    <div>${escapeHtml(requirement.title)}</div>
                </div>
                <div class="detail-field">
                    <label>Описание:</label>
                    <div>${escapeHtml(requirement.description || 'Не указано')}</div>
                </div>
                <div class="detail-field">
                    <label>Тип требования:</label>
                    <div>${escapeHtml(requirement.requirement_type)}</div>
                </div>
                <div class="detail-field">
                    <label>Статус:</label>
                    <div>${escapeHtml(requirement.status)}</div>
                </div>
                <div class="detail-field">
                    <label>Приоритет:</label>
                    <div>${escapeHtml(requirement.priority)}</div>
                </div>
                <div class="detail-field">
                    <label>Источник:</label>
                    <div>${escapeHtml(requirement.source || 'Не указано')}</div>
                </div>
                <div class="detail-field">
                    <label>Автор:</label>
                    <div>${escapeHtml(requirement.author || 'Не указано')}</div>
                </div>
                <div class="detail-field">
                    <label>Дата создания:</label>
                    <div>${formatDate(requirement.created_at)}</div>
                </div>
                <div class="detail-field">
                    <label>Дата изменения:</label>
                    <div>${formatDate(requirement.updated_at)}</div>
                </div>
            </div>
            ${linksHtml}
            <div class="form-actions">
                <button class="btn btn-primary" onclick="editRequirement(${requirement.id}); document.getElementById('detailModal').style.display='none';">Изменить</button>
                <button class="btn btn-secondary" onclick="viewHistory(${requirement.id}); document.getElementById('detailModal').style.display='none';">История</button>
            </div>
        `;
        
        modal.style.display = 'block';
    } catch (error) {
        console.error('Ошибка загрузки требования:', error);
        alert('Ошибка загрузки требования');
    }
}

// Показ описания требования
function showRequirementDescription(requirementId) {
    const requirement = allRequirements.find(r => r.id === requirementId);
    if (!requirement) {
        // Если требование не найдено в кэше, загружаем его
        fetch(projectApi(`/requirements/${requirementId}`))
            .then(response => response.json())
            .then(req => {
                showDescriptionModal(req);
            })
            .catch(error => {
                console.error('Ошибка загрузки требования:', error);
                alert('Ошибка загрузки требования');
            });
    } else {
        showDescriptionModal(requirement);
    }
}

// Показ модального окна с описанием
function showDescriptionModal(requirement) {
    const modal = document.getElementById('detailModal');
    const title = document.getElementById('detailTitle');
    const content = document.getElementById('detailContent');
    
    title.textContent = `Требование #${requirement.id}: ${requirement.title}`;
    
    content.innerHTML = `
        <div class="detail-section">
            <h3>Описание</h3>
            <div class="detail-field">
                <div style="padding: 15px; background: #f8f9fa; border-radius: 5px; white-space: pre-wrap;">${escapeHtml(requirement.description || 'Описание не указано')}</div>
            </div>
        </div>
        <div class="form-actions">
            <button class="btn btn-primary" onclick="viewRequirementDetail(${requirement.id}); document.getElementById('detailModal').style.display='block';">Показать полную информацию</button>
            <button class="btn btn-secondary" onclick="document.getElementById('detailModal').style.display='none';">Закрыть</button>
        </div>
    `;
    
    modal.style.display = 'block';
}

// Отображение таблицы пересечений
async function displayMatrix() {
    try {
        const response = await fetch(projectApi('/matrix'));
        const data = await response.json();
        
        const container = document.getElementById('matrixTable');
        const requirements = data.requirements;
        const matrix = data.matrix;
        
        // Обновляем allRequirements для доступа к описаниям
        allRequirements = requirements;
        
        if (requirements.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">Нет требований для отображения матрицы.</p>';
            return;
        }
        
        const reqDict = {};
        requirements.forEach(req => {
            reqDict[req.id] = req;
        });
        
        const reqIds = requirements.map(r => r.id).sort((a, b) => a - b);
        
        let html = '<table class="matrix-table"><thead><tr><th></th>';
        
        // Заголовки столбцов
        reqIds.forEach(reqId => {
            html += `<th class="matrix-header-clickable" title="${escapeHtml(reqDict[reqId].title)} - Кликните для просмотра описания" onclick="showRequirementDescription(${reqId})" style="cursor: pointer;">#${reqId}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        // Строки матрицы
        reqIds.forEach(sourceId => {
            html += `<tr><th class="matrix-header-clickable" title="${escapeHtml(reqDict[sourceId].title)} - Кликните для просмотра описания" onclick="showRequirementDescription(${sourceId})" style="cursor: pointer;">#${sourceId}</th>`;
            reqIds.forEach(targetId => {
                let cellClass = 'matrix-cell';
                let cellContent = '';
                
                if (sourceId === targetId) {
                    cellClass += ' diagonal';
                } else if (matrix[sourceId] && matrix[sourceId][targetId]) {
                    const linkType = matrix[sourceId][targetId];
                    cellClass += ' clickable ' + getLinkTypeClass(linkType);
                    cellContent = linkType;
                }
                
                const onclickAttr = (sourceId !== targetId && matrix[sourceId] && matrix[sourceId][targetId]) 
                    ? `onclick="viewRequirementDetail(${targetId}); document.getElementById('detailModal').style.display='block';" title="Кликните для просмотра требования #${targetId}"`
                    : '';
                
                html += `<td class="${cellClass}" ${onclickAttr}>${cellContent}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Ошибка загрузки матрицы:', error);
        document.getElementById('matrixTable').innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 40px;">Ошибка загрузки матрицы</p>';
    }
}

// Отображение Mind Map
function displayMindMap() {
    const container = document.getElementById('mindMapNetwork');
    
    if (allRequirements.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">Нет требований для отображения Mind Map.</p>';
        return;
    }
    
    // Создание узлов и связей для vis.js
    const nodes = [];
    const edges = [];
    
    allRequirements.forEach(req => {
        nodes.push({
            id: req.id,
            label: `#${req.id}\n${req.title.substring(0, 30)}${req.title.length > 30 ? '...' : ''}`,
            title: `${req.title}\nТип: ${req.requirement_type}\nСтатус: ${req.status}`,
            color: getNodeColor(req.requirement_type),
            shape: 'box'
        });
        
        // Добавление связей
        if (req.outgoing_links) {
            req.outgoing_links.forEach(link => {
                edges.push({
                    from: req.id,
                    to: link.target_requirement_id,
                    label: link.link_type,
                    color: getEdgeColor(link.link_type),
                    arrows: 'to'
                });
            });
        }
    });
    
    const data = { nodes: nodes, edges: edges };
    const options = {
        nodes: {
            font: { size: 14 },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            font: { size: 12, align: 'middle' },
            arrows: { to: { enabled: true } },
            smooth: { type: 'continuous' }
        },
        physics: {
            enabled: true,
            stabilization: { iterations: 200 }
        },
        interaction: {
            hover: true,
            tooltipDelay: 100
        }
    };
    
    // Уничтожение предыдущей сети, если она существует
    if (mindMapNetwork) {
        mindMapNetwork.destroy();
    }
    
    mindMapNetwork = new vis.Network(container, data, options);
    
    // Обработка клика на узел
    mindMapNetwork.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            viewRequirementDetail(nodeId);
        }
    });
}

// Получение цвета узла по типу требования
function getNodeColor(requirementType) {
    const colorMap = {
        'Бизнес-требование': '#3498db',
        'Функциональное требование': '#27ae60',
        'Нефункциональное требование': '#e67e22',
        'Пользовательское требование': '#9b59b6',
        'Требование к интерфейсу': '#e74c3c'
    };
    return colorMap[requirementType] || '#95a5a6';
}

// Получение цвета связи
function getEdgeColor(linkType) {
    const colorMap = {
        'Реализует': '#27ae60',
        'Зависит от': '#f39c12',
        'Противоречит': '#e74c3c'
    };
    return colorMap[linkType] || '#95a5a6';
}

// Открытие модального окна для создания/редактирования требования
function openRequirementModal(requirementId = null) {
    const modal = document.getElementById('requirementModal');
    const form = document.getElementById('requirementForm');
    const title = document.getElementById('modalTitle');
    
    if (requirementId) {
        title.textContent = 'Изменить требование';
        loadRequirementForEdit(requirementId);
    } else {
        title.textContent = 'Добавить требование';
        form.reset();
        document.getElementById('requirementId').value = '';
    }
    
    modal.style.display = 'block';
}

// Загрузка требования для редактирования
async function loadRequirementForEdit(requirementId) {
    try {
        const response = await fetch(projectApi(`/requirements/${requirementId}`));
        const requirement = await response.json();
        
        document.getElementById('requirementId').value = requirement.id;
        document.getElementById('title').value = requirement.title;
        document.getElementById('description').value = requirement.description || '';
        document.getElementById('requirementType').value = requirement.requirement_type;
        document.getElementById('status').value = requirement.status;
        document.getElementById('priority').value = requirement.priority;
        document.getElementById('source').value = requirement.source || '';
        document.getElementById('author').value = requirement.author || '';
    } catch (error) {
        console.error('Ошибка загрузки требования:', error);
        alert('Ошибка загрузки требования');
    }
}

// Сохранение требования
async function saveRequirement() {
    const requirementId = document.getElementById('requirementId').value;
    const data = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        requirement_type: document.getElementById('requirementType').value,
        status: document.getElementById('status').value,
        priority: document.getElementById('priority').value,
        source: document.getElementById('source').value,
        author: document.getElementById('author').value
    };
    
    try {
        const url = requirementId 
            ? projectApi(`/requirements/${requirementId}`)
            : projectApi('/requirements');
        
        const method = requirementId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            document.getElementById('requirementModal').style.display = 'none';
            loadRequirements();
        } else {
            const error = await response.json();
            alert('Ошибка сохранения: ' + (error.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Ошибка сохранения требования:', error);
        alert('Ошибка сохранения требования');
    }
}

// Редактирование требования
function editRequirement(requirementId) {
    openRequirementModal(requirementId);
}

// Удаление требования
async function deleteRequirement(requirementId) {
    if (!confirm('Вы уверены, что хотите удалить это требование?')) {
        return;
    }
    
    try {
        const response = await fetch(projectApi(`/requirements/${requirementId}`), {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadRequirements();
        } else {
            alert('Ошибка удаления требования');
        }
    } catch (error) {
        console.error('Ошибка удаления требования:', error);
        alert('Ошибка удаления требования');
    }
}

// Открытие модального окна для создания связи
async function openLinkModal(sourceRequirementId) {
    const modal = document.getElementById('linkModal');
    const targetSelect = document.getElementById('targetRequirementId');
    
    document.getElementById('sourceRequirementId').value = sourceRequirementId;
    
    // Загрузка списка требований для выбора цели
    try {
        const response = await fetch(projectApi('/requirements'));
        const requirements = await response.json();
        
        targetSelect.innerHTML = '<option value="">Выберите требование</option>';
        requirements.forEach(req => {
            if (req.id !== sourceRequirementId) {
                const option = document.createElement('option');
                option.value = req.id;
                option.textContent = `#${req.id} - ${req.title}`;
                targetSelect.appendChild(option);
            }
        });
        
        modal.style.display = 'block';
    } catch (error) {
        console.error('Ошибка загрузки требований:', error);
        alert('Ошибка загрузки требований');
    }
}

// Сохранение связи
async function saveLink() {
    const data = {
        source_id: parseInt(document.getElementById('sourceRequirementId').value),
        target_id: parseInt(document.getElementById('targetRequirementId').value),
        link_type: document.getElementById('linkType').value
    };
    
    try {
        const response = await fetch(projectApi('/links'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            document.getElementById('linkModal').style.display = 'none';
            loadRequirements();
        } else {
            const error = await response.json();
            alert('Ошибка создания связи: ' + (error.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Ошибка создания связи:', error);
        alert('Ошибка создания связи');
    }
}

// Просмотр истории изменений
async function viewHistory(requirementId) {
    try {
        const response = await fetch(projectApi(`/requirements/${requirementId}/history`));
        const history = await response.json();
        
        const modal = document.getElementById('historyModal');
        const content = document.getElementById('historyContent');
        
        if (history.length === 0) {
            content.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 20px;">История изменений пуста</p>';
            modal.style.display = 'block';
            return;
        }
        
        let html = '<table class="history-table"><thead><tr><th>Дата</th><th>Тип изменения</th><th>Изменено</th><th>Изменения</th></tr></thead><tbody>';
        
        history.forEach(item => {
            const changeClass = item.change_type.toLowerCase();
            let changesHtml = '';
            
            if (item.change_type === 'CREATE') {
                changesHtml = 'Создано новое требование';
            } else if (item.change_type === 'DELETE') {
                changesHtml = 'Требование удалено';
            } else if (item.change_type === 'UPDATE' && item.old_values && item.new_values) {
                const changes = [];
                Object.keys(item.new_values).forEach(key => {
                    if (key !== 'id' && item.old_values[key] !== item.new_values[key]) {
                        changes.push(`${key}: "${item.old_values[key]}" → "${item.new_values[key]}"`);
                    }
                });
                changesHtml = changes.length > 0 ? changes.join('<br>') : 'Нет изменений';
            }
            
            html += `<tr>
                <td>${formatDate(item.changed_at)}</td>
                <td><span class="history-change ${changeClass}">${item.change_type}</span></td>
                <td>${escapeHtml(item.changed_by || 'Не указано')}</td>
                <td><div class="history-values">${changesHtml}</div></td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        content.innerHTML = html;
        modal.style.display = 'block';
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
        alert('Ошибка загрузки истории');
    }
}

// Экспорт в Excel
function exportToExcel() {
    window.location.href = projectApi('/export');
}

// Экспорт матрицы в Excel
function exportMatrixToExcel() {
    window.location.href = projectApi('/export/matrix');
}

// Вспомогательные функции
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
}

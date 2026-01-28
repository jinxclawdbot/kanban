// Kanban Board Application

const API_BASE = '/api';
let token = localStorage.getItem('kanban_token');
let currentUser = null;

// Columns configuration
const COLUMNS = ['Recurring', 'Backlog', 'In Progress', 'Review', 'Done'];

// ============ Auth Functions ============

async function login(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Invalid credentials');
        }
        
        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('kanban_token', token);
        
        showApp();
    } catch (error) {
        showLoginError(error.message);
    }
}

function logout() {
    token = null;
    localStorage.removeItem('kanban_token');
    showLogin();
}

function showLoginError(message) {
    const errorDiv = document.getElementById('login-error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function showLogin() {
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('app-section').style.display = 'none';
    document.getElementById('login-error').style.display = 'none';
    document.getElementById('login-form').reset();
}

async function showApp() {
    try {
        // Verify token and get user
        const response = await fetchWithAuth(`${API_BASE}/auth/me`);
        if (!response.ok) {
            throw new Error('Invalid session');
        }
        
        currentUser = await response.json();
        document.getElementById('user-display').textContent = `👤 ${currentUser.username}`;
        
        document.getElementById('login-section').style.display = 'none';
        document.getElementById('app-section').style.display = 'block';
        
        await loadBoard();
        await loadCategories();
    } catch (error) {
        logout();
    }
}

// ============ API Functions ============

function fetchWithAuth(url, options = {}) {
    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        }
    });
}

async function loadBoard() {
    try {
        const response = await fetchWithAuth(`${API_BASE}/tasks/board`);
        if (!response.ok) throw new Error('Failed to load board');
        
        const board = await response.json();
        renderBoard(board);
    } catch (error) {
        console.error('Error loading board:', error);
    }
}

async function loadCategories() {
    try {
        const response = await fetchWithAuth(`${API_BASE}/tasks/categories`);
        if (!response.ok) return;
        
        const data = await response.json();
        const datalist = document.getElementById('categories-list');
        datalist.innerHTML = data.categories.map(c => `<option value="${c}">`).join('');
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function createTask(taskData) {
    const response = await fetchWithAuth(`${API_BASE}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create task');
    }
    
    return response.json();
}

async function updateTask(taskId, taskData) {
    const response = await fetchWithAuth(`${API_BASE}/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update task');
    }
    
    return response.json();
}

async function moveTask(taskId, column) {
    const response = await fetchWithAuth(`${API_BASE}/tasks/${taskId}/move`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ column })
    });
    
    if (!response.ok) {
        throw new Error('Failed to move task');
    }
    
    return response.json();
}

async function deleteTask(taskId) {
    const response = await fetchWithAuth(`${API_BASE}/tasks/${taskId}`, {
        method: 'DELETE'
    });
    
    if (!response.ok) {
        throw new Error('Failed to delete task');
    }
}

// ============ UI Functions ============

function renderBoard(board) {
    const boardEl = document.getElementById('board');
    boardEl.innerHTML = '';
    
    for (const column of COLUMNS) {
        const tasks = board[column] || [];
        const columnEl = createColumnElement(column, tasks);
        boardEl.appendChild(columnEl);
    }
    
    setupDragAndDrop();
}

function createColumnElement(columnName, tasks) {
    const column = document.createElement('div');
    column.className = 'column';
    column.dataset.column = columnName;
    
    column.innerHTML = `
        <div class="column-header">
            <h4>${columnName}</h4>
            <span class="column-count">${tasks.length}</span>
        </div>
        <div class="column-tasks" data-column="${columnName}">
            ${tasks.map(task => createTaskCard(task)).join('')}
        </div>
    `;
    
    return column;
}

function createTaskCard(task) {
    const priorityClass = `priority-${task.priority.toLowerCase()}`;
    const description = task.description ? `<div class="task-description">${escapeHtml(task.description)}</div>` : '';
    
    let badges = `<span class="task-badge priority ${priorityClass}">${task.priority}</span>`;
    
    if (task.category) {
        badges += `<span class="task-badge category">${escapeHtml(task.category)}</span>`;
    }
    
    if (task.due_date) {
        const dueDate = new Date(task.due_date);
        const isOverdue = dueDate < new Date();
        const dateStr = dueDate.toLocaleDateString();
        badges += `<span class="task-badge due-date ${isOverdue ? 'overdue' : ''}">📅 ${dateStr}</span>`;
    }
    
    return `
        <div class="task-card ${priorityClass}" draggable="true" data-task-id="${task.id}">
            <div class="task-title">${escapeHtml(task.title)}</div>
            ${description}
            <div class="task-meta">${badges}</div>
            <div class="task-actions">
                <button class="outline secondary" onclick="editTask('${task.id}')">Edit</button>
                <button class="outline contrast" onclick="confirmDelete('${task.id}')">Delete</button>
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============ Drag and Drop ============

function setupDragAndDrop() {
    const cards = document.querySelectorAll('.task-card');
    const dropZones = document.querySelectorAll('.column-tasks');
    
    cards.forEach(card => {
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
    });
    
    dropZones.forEach(zone => {
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('dragleave', handleDragLeave);
        zone.addEventListener('drop', handleDrop);
    });
}

let draggedCard = null;

function handleDragStart(e) {
    draggedCard = e.target;
    e.target.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
    document.querySelectorAll('.column-tasks').forEach(zone => {
        zone.classList.remove('drag-over');
    });
    draggedCard = null;
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('drag-over');
}

async function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    
    if (!draggedCard) return;
    
    const newColumn = e.currentTarget.dataset.column;
    const taskId = draggedCard.dataset.taskId;
    
    try {
        await moveTask(taskId, newColumn);
        await loadBoard();
    } catch (error) {
        console.error('Error moving task:', error);
        alert('Failed to move task');
    }
}

// ============ Modal Functions ============

function showCreateModal() {
    document.getElementById('modal-title').textContent = 'New Task';
    document.getElementById('task-form').reset();
    document.getElementById('task-id').value = '';
    document.getElementById('task-modal').showModal();
}

async function editTask(taskId) {
    try {
        const response = await fetchWithAuth(`${API_BASE}/tasks/${taskId}`);
        if (!response.ok) throw new Error('Failed to load task');
        
        const task = await response.json();
        
        document.getElementById('modal-title').textContent = 'Edit Task';
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-description').value = task.description || '';
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-category').value = task.category || '';
        document.getElementById('task-column').value = task.column;
        
        if (task.due_date) {
            const date = new Date(task.due_date);
            document.getElementById('task-due-date').value = date.toISOString().slice(0, 16);
        } else {
            document.getElementById('task-due-date').value = '';
        }
        
        document.getElementById('task-modal').showModal();
    } catch (error) {
        console.error('Error loading task:', error);
        alert('Failed to load task');
    }
}

function closeModal() {
    document.getElementById('task-modal').close();
}

async function handleTaskSubmit(event) {
    event.preventDefault();
    
    const taskId = document.getElementById('task-id').value;
    const dueDate = document.getElementById('task-due-date').value;
    
    const taskData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value || null,
        priority: document.getElementById('task-priority').value,
        category: document.getElementById('task-category').value || null,
        column: document.getElementById('task-column').value,
        due_date: dueDate ? new Date(dueDate).toISOString() : null
    };
    
    try {
        if (taskId) {
            await updateTask(taskId, taskData);
        } else {
            await createTask(taskData);
        }
        
        closeModal();
        await loadBoard();
        await loadCategories();
    } catch (error) {
        console.error('Error saving task:', error);
        alert(error.message);
    }
}

let taskToDelete = null;

function confirmDelete(taskId) {
    taskToDelete = taskId;
    document.getElementById('delete-modal').showModal();
}

function closeDeleteModal() {
    document.getElementById('delete-modal').close();
    taskToDelete = null;
}

async function handleDelete() {
    if (!taskToDelete) return;
    
    try {
        await deleteTask(taskToDelete);
        closeDeleteModal();
        await loadBoard();
    } catch (error) {
        console.error('Error deleting task:', error);
        alert('Failed to delete task');
    }
}

// ============ Initialization ============

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('login-form').addEventListener('submit', login);
    document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);
    document.getElementById('confirm-delete-btn').addEventListener('click', handleDelete);
    
    // Check for existing session
    if (token) {
        showApp();
    } else {
        showLogin();
    }
});

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
        
        // Show/hide admin features
        const usersBtn = document.getElementById('users-btn');
        if (currentUser.is_admin) {
            usersBtn.style.display = 'block';
        } else {
            usersBtn.style.display = 'none';
        }
        
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
        const select = document.getElementById('task-category');
        const currentValue = select.value;
        
        // Build options
        select.innerHTML = '<option value="">-- No Category --</option>';
        data.categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            select.appendChild(option);
        });
        
        // Restore selection if it still exists
        if (currentValue) {
            select.value = currentValue;
        }
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

async function showCreateModal() {
    document.getElementById('modal-title').textContent = 'New Task';
    document.getElementById('task-form').reset();
    document.getElementById('task-id').value = '';
    await loadCategories();
    document.getElementById('task-modal').showModal();
}

async function editTask(taskId) {
    try {
        const response = await fetchWithAuth(`${API_BASE}/tasks/${taskId}`);
        if (!response.ok) throw new Error('Failed to load task');
        
        const task = await response.json();
        
        // Load categories first to ensure dropdown is populated
        await loadCategories();
        
        document.getElementById('modal-title').textContent = 'Edit Task';
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-description').value = task.description || '';
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-category').value = task.category || '';
        document.getElementById('task-column').value = task.column;
        
        if (task.due_date) {
            const date = new Date(task.due_date);
            document.getElementById('task-due-date').value = date.toISOString().slice(0, 10);
            document.getElementById('task-due-hour').value = date.getHours().toString().padStart(2, '0');
            const roundedMinutes = Math.round(date.getMinutes() / 15) * 15 % 60;
            document.getElementById('task-due-minute').value = roundedMinutes.toString().padStart(2, '0');
        } else {
            document.getElementById('task-due-date').value = '';
            document.getElementById('task-due-hour').value = '';
            document.getElementById('task-due-minute').value = '';
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
    const dueHour = document.getElementById('task-due-hour').value;
    const dueMinute = document.getElementById('task-due-minute').value;
    
    // Combine date, hour, and minute
    let dueDateISO = null;
    if (dueDate) {
        const hour = dueHour || '00';
        const minute = dueMinute || '00';
        dueDateISO = new Date(`${dueDate}T${hour}:${minute}:00`).toISOString();
    }
    
    const taskData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value || null,
        priority: document.getElementById('task-priority').value,
        category: document.getElementById('task-category').value || null,
        column: document.getElementById('task-column').value,
        due_date: dueDateISO
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

// ============ Category Management Functions ============

async function showCategoriesModal() {
    document.getElementById('create-category-form').reset();
    document.getElementById('create-category-error').style.display = 'none';
    document.getElementById('create-category-success').style.display = 'none';
    await loadCategoriesList();
    document.getElementById('categories-modal').showModal();
}

function closeCategoriesModal() {
    document.getElementById('categories-modal').close();
}

async function loadCategoriesList() {
    try {
        const response = await fetchWithAuth(`${API_BASE}/tasks/categories`);
        if (!response.ok) throw new Error('Failed to load categories');
        
        const data = await response.json();
        const listEl = document.getElementById('categories-list');
        
        if (data.categories.length === 0) {
            listEl.innerHTML = '<p style="color: var(--pico-muted-color);">No categories yet. Create one above!</p>';
            return;
        }
        
        listEl.innerHTML = '';
        data.categories.forEach(cat => {
            const div = document.createElement('div');
            div.className = 'category-item';
            div.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border-bottom: 1px solid var(--pico-muted-border-color);';
            
            const span = document.createElement('span');
            span.textContent = '🏷️ ' + cat;
            
            const btn = document.createElement('button');
            btn.className = 'outline contrast small';
            btn.textContent = 'Delete';
            btn.onclick = () => deleteCategory(cat);
            
            div.appendChild(span);
            div.appendChild(btn);
            listEl.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function handleCreateCategory(event) {
    event.preventDefault();
    
    const name = document.getElementById('new-category-name').value.trim();
    
    const errorDiv = document.getElementById('create-category-error');
    const successDiv = document.getElementById('create-category-success');
    
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    try {
        const response = await fetchWithAuth(`${API_BASE}/tasks/categories?name=${encodeURIComponent(name)}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create category');
        }
        
        successDiv.textContent = `Category "${name}" created!`;
        successDiv.style.display = 'block';
        document.getElementById('create-category-form').reset();
        await loadCategoriesList();
        await loadCategories(); // Refresh the datalist in task form
        
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    }
}

async function deleteCategory(name) {
    if (!confirm(`Delete category "${name}"? Tasks using this category will keep it.`)) return;
    
    try {
        const response = await fetchWithAuth(`${API_BASE}/tasks/categories/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete category');
        }
        
        await loadCategoriesList();
        await loadCategories(); // Refresh the datalist in task form
    } catch (error) {
        alert(error.message);
    }
}

// ============ User Management Functions (Admin Only) ============

async function showUsersModal() {
    document.getElementById('create-user-form').reset();
    document.getElementById('create-user-error').style.display = 'none';
    document.getElementById('create-user-success').style.display = 'none';
    await loadUsersList();
    document.getElementById('users-modal').showModal();
}

function closeUsersModal() {
    document.getElementById('users-modal').close();
}

async function loadUsersList() {
    try {
        const response = await fetchWithAuth(`${API_BASE}/auth/users`);
        if (!response.ok) throw new Error('Failed to load users');
        
        const data = await response.json();
        const listEl = document.getElementById('users-list');
        
        listEl.innerHTML = data.users.map(user => `
            <div class="user-item" style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border-bottom: 1px solid var(--pico-muted-border-color);">
                <span>
                    ${user.username}
                    ${user.is_admin ? '<small style="color: var(--pico-primary);">(admin)</small>' : ''}
                </span>
                ${user.username !== 'admin' ? `<button class="outline contrast small" onclick="deleteUser('${user.username}')">Delete</button>` : '<small style="color: var(--pico-muted-color);">protected</small>'}
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function handleCreateUser(event) {
    event.preventDefault();
    
    const username = document.getElementById('new-username').value;
    const password = document.getElementById('new-user-password').value;
    
    const errorDiv = document.getElementById('create-user-error');
    const successDiv = document.getElementById('create-user-success');
    
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    try {
        const response = await fetchWithAuth(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create user');
        }
        
        successDiv.textContent = `User "${username}" created!`;
        successDiv.style.display = 'block';
        document.getElementById('create-user-form').reset();
        await loadUsersList();
        
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    }
}

async function deleteUser(username) {
    if (!confirm(`Delete user "${username}"?`)) return;
    
    try {
        const response = await fetchWithAuth(`${API_BASE}/auth/users/${username}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete user');
        }
        
        await loadUsersList();
    } catch (error) {
        alert(error.message);
    }
}

// ============ Password Change Functions ============

function showPasswordModal() {
    document.getElementById('password-form').reset();
    document.getElementById('password-error').style.display = 'none';
    document.getElementById('password-success').style.display = 'none';
    document.getElementById('password-modal').showModal();
}

function closePasswordModal() {
    document.getElementById('password-modal').close();
}

async function handlePasswordChange(event) {
    event.preventDefault();
    
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    const errorDiv = document.getElementById('password-error');
    const successDiv = document.getElementById('password-success');
    
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    // Validate passwords match
    if (newPassword !== confirmPassword) {
        errorDiv.textContent = 'New passwords do not match';
        errorDiv.style.display = 'block';
        return;
    }
    
    // Validate password length
    if (newPassword.length < 8) {
        errorDiv.textContent = 'Password must be at least 8 characters';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        const response = await fetchWithAuth(`${API_BASE}/auth/change-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to change password');
        }
        
        successDiv.textContent = 'Password changed successfully!';
        successDiv.style.display = 'block';
        
        // Close modal after 2 seconds
        setTimeout(() => {
            closePasswordModal();
        }, 2000);
        
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    }
}

// ============ Initialization ============

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('login-form').addEventListener('submit', login);
    document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);
    document.getElementById('confirm-delete-btn').addEventListener('click', handleDelete);
    document.getElementById('password-form').addEventListener('submit', handlePasswordChange);
    document.getElementById('create-user-form').addEventListener('submit', handleCreateUser);
    document.getElementById('create-category-form').addEventListener('submit', handleCreateCategory);
    
    // Check for existing session
    if (token) {
        showApp();
    } else {
        showLogin();
    }
});

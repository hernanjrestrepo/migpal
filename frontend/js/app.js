// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Auth utilities
const auth = {
    getToken() {
        return localStorage.getItem('token');
    },
    
    setToken(token) {
        localStorage.setItem('token', token);
    },
    
    removeToken() {
        localStorage.removeItem('token');
    },
    
    isAuthenticated() {
        return !!this.getToken();
    },
    
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    },
    
    logout() {
        this.removeToken();
        window.location.href = '/login.html';
    }
};

// API utilities
const api = {
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...auth.getHeaders(),
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                if (response.status === 401) {
                    auth.logout();
                }
                throw new Error(data.detail || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// Auth API
const authAPI = {
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE_URL}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }
        
        return data;
    },
    
    async register(userData) {
        return api.post('/users', userData);
    },
    
    async getCurrentUser() {
        return api.get('/users/me');
    }
};

// UI utilities
const ui = {
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
        }
    },
    
    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<div class="alert alert-error">${message}</div>`;
        }
    },
    
    showSuccess(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<div class="alert alert-success">${message}</div>`;
        }
    },
    
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    getStatusBadge(status) {
        const badges = {
            'completed': 'badge-success',
            'pending': 'badge-warning',
            'failed': 'badge-danger',
            'processing': 'badge-info',
            'cancelled': 'badge-danger',
            'verified': 'badge-success',
            'rejected': 'badge-danger'
        };
        const badgeClass = badges[status] || 'badge-info';
        return `<span class="badge ${badgeClass}">${status}</span>`;
    }
};

// Check authentication on protected pages
function requireAuth() {
    if (!auth.isAuthenticated()) {
        window.location.href = '/login.html';
    }
}

// Initialize user info in header
async function initUserInfo() {
    if (!auth.isAuthenticated()) return;
    
    try {
        const user = await authAPI.getCurrentUser();
        const userInfoElement = document.getElementById('user-info');
        if (userInfoElement) {
            userInfoElement.innerHTML = `
                <span>Bienvenido, ${user.username}</span>
                <button onclick="auth.logout()" class="btn btn-sm btn-secondary">Salir</button>
            `;
        }
    } catch (error) {
        console.error('Failed to load user info:', error);
    }
}

// Export for use in other scripts
window.auth = auth;
window.api = api;
window.authAPI = authAPI;
window.ui = ui;
window.requireAuth = requireAuth;
window.initUserInfo = initUserInfo;

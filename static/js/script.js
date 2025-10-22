class ExpenseTracker {
    constructor() {
        this.currentFilters = {
            startDate: '',
            endDate: '',
            category: 'All',
            search: ''
        };
        this.categoryChart = null;
        this.trendChart = null;
        this.editingId = null;
        this.categories = [];
        this.init();
    }

    async init() {
        this.setCurrentDate();
        await this.loadCategories();
        this.bindEvents();
        this.loadExpenses();
        this.loadStats();
        this.setupCharts();
    }

    setCurrentDate() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('date').value = today;
        document.getElementById('currentDate').textContent = new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        // Set default end date to today
        document.getElementById('endDate').value = today;
        
        // Set default start date to 30 days ago
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        document.getElementById('startDate').value = thirtyDaysAgo.toISOString().split('T')[0];
    }

    async loadCategories() {
        try {
            const response = await fetch('/api/categories');
            this.categories = await response.json();
            this.populateCategorySelects();
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    populateCategorySelects() {
        const categoryFilter = document.getElementById('categoryFilter');
        const categorySelect = document.getElementById('category');
        
        this.categories.forEach(category => {
            categoryFilter.innerHTML += `<option value="${category}">${category}</option>`;
            categorySelect.innerHTML += `<option value="${category}">${category}</option>`;
        });
    }

    bindEvents() {
        // Form submission
        document.getElementById('expenseForm').addEventListener('submit', (e) => {
            e.preventDefault();
            if (this.editingId) {
                this.updateExpense(this.editingId);
            } else {
                this.addExpense();
            }
        });

        // Quick add form
        document.getElementById('quickAddForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.quickAddExpense();
        });

        // Filter events
        document.getElementById('applyFilters').addEventListener('click', () => {
            this.applyFilters();
        });

        document.getElementById('resetFilters').addEventListener('click', () => {
            this.resetFilters();
        });

        // Quick add button
        document.getElementById('quickAdd').addEventListener('click', () => {
            this.openQuickAdd();
        });

        // Cancel button
        document.getElementById('cancelButton').addEventListener('click', () => {
            this.cancelEdit();
        });

        // Export CSV
        document.getElementById('exportCSV').addEventListener('click', () => {
            this.exportCSV();
        });

        // Real-time search
        document.getElementById('searchFilter').addEventListener('input', (e) => {
            this.currentFilters.search = e.target.value;
            this.debounce(() => this.loadExpenses(), 300);
        });
    }

    debounce(func, wait) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(func, wait);
    }

    // CREATE - Add new expense
    async addExpense() {
        const formData = this.getFormData();
        if (!this.validateForm(formData)) return;

        try {
            const response = await fetch('/api/expenses', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const expense = await response.json();
                this.resetForm();
                this.loadExpenses();
                this.loadStats();
                this.showNotification('Expense added successfully! 🎉', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to add expense', 'error');
            }
        } catch (error) {
            this.showNotification('Network error occurred', 'error');
        }
    }

    // READ - Load and display expenses
    async loadExpenses() {
        this.showLoading(true);
        try {
            const params = new URLSearchParams();
            if (this.currentFilters.startDate) params.append('start_date', this.currentFilters.startDate);
            if (this.currentFilters.endDate) params.append('end_date', this.currentFilters.endDate);
            if (this.currentFilters.category && this.currentFilters.category !== 'All') {
                params.append('category', this.currentFilters.category);
            }
            if (this.currentFilters.search) {
                params.append('search', this.currentFilters.search);
            }

            const response = await fetch(`/api/expenses?${params}`);
            const expenses = await response.json();

            this.renderExpenses(expenses);
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading expenses:', error);
            this.showNotification('Error loading expenses', 'error');
            this.showLoading(false);
        }
    }

    renderExpenses(expenses) {
        const tbody = document.getElementById('expensesTable');
        const countElement = document.getElementById('expensesCount');
        
        countElement.textContent = `Showing ${expenses.length} expense${expenses.length !== 1 ? 's' : ''}`;

        if (expenses.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-12">
                        <div class="flex flex-col items-center justify-center">
                            <i class="fas fa-receipt text-4xl text-gray-300 mb-4"></i>
                            <p class="text-gray-500 text-lg mb-2">No expenses found</p>
                            <p class="text-gray-400">Try adjusting your filters or add a new expense</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = expenses.map(expense => `
            <tr class="hover:bg-gray-50 transition duration-150 group" data-id="${expense.id}">
                <td class="py-4 px-6 whitespace-nowrap">
                    <div class="font-semibold text-gray-900">${this.formatDate(expense.date)}</div>
                    <div class="text-sm text-gray-500">${this.formatTime(expense.created_at)}</div>
                </td>
                <td class="py-4 px-6">
                    <div class="font-medium text-gray-900">${this.escapeHtml(expense.description)}</div>
                </td>
                <td class="py-4 px-6 whitespace-nowrap">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold category-${expense.category.toLowerCase()}">
                        <i class="fas fa-tag mr-2"></i>${this.escapeHtml(expense.category)}
                    </span>
                </td>
                <td class="py-4 px-6 whitespace-nowrap">
                    <div class="font-bold text-lg text-green-600">$${parseFloat(expense.amount).toFixed(2)}</div>
                </td>
                <td class="py-4 px-6 whitespace-nowrap">
                    <div class="flex space-x-2 opacity-0 group-hover:opacity-100 transition duration-200">
                        <button onclick="expenseTracker.editExpense(${expense.id})" 
                                class="bg-blue-500 text-white px-3 py-2 rounded-lg hover:bg-blue-600 transition duration-200 font-semibold text-sm">
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button onclick="expenseTracker.deleteExpense(${expense.id})" 
                                class="bg-red-500 text-white px-3 py-2 rounded-lg hover:bg-red-600 transition duration-200 font-semibold text-sm">
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    // UPDATE - Edit existing expense
    async editExpense(id) {
        try {
            const response = await fetch(`/api/expenses/${id}`);
            const expense = await response.json();
            
            // Populate form with existing data
            document.getElementById('description').value = expense.description;
            document.getElementById('amount').value = expense.amount;
            document.getElementById('date').value = expense.date;
            document.getElementById('category').value = expense.category;
            
            // Change to edit mode
            this.editingId = id;
            document.getElementById('formTitle').innerHTML = '<i class="fas fa-edit mr-3 text-yellow-500"></i>Edit Expense';
            document.getElementById('submitButton').innerHTML = '<i class="fas fa-save mr-2"></i>Update Expense';
            document.getElementById('submitButton').className = 'flex-1 bg-yellow-500 text-white py-4 rounded-xl hover:bg-yellow-600 transition duration-200 font-semibold text-lg';
            document.getElementById('cancelButton').classList.remove('hidden');
            
            // Scroll to form
            document.getElementById('expenseFormSection').scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            this.showNotification('Error loading expense for editing', 'error');
        }
    }

    async updateExpense(id) {
        const formData = this.getFormData();
        if (!this.validateForm(formData)) return;

        try {
            const response = await fetch(`/api/expenses/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const updatedExpense = await response.json();
                this.cancelEdit();
                this.loadExpenses();
                this.loadStats();
                this.showNotification('Expense updated successfully! ✨', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to update expense', 'error');
            }
        } catch (error) {
            this.showNotification('Network error occurred', 'error');
        }
    }

    cancelEdit() {
        this.editingId = null;
        document.getElementById('formTitle').innerHTML = '<i class="fas fa-plus-circle mr-3 text-primary"></i>Add New Expense';
        document.getElementById('submitButton').innerHTML = '<i class="fas fa-plus mr-2"></i>Add Expense';
        document.getElementById('submitButton').className = 'flex-1 bg-primary text-white py-4 rounded-xl hover:bg-blue-700 transition duration-200 font-semibold text-lg';
        document.getElementById('cancelButton').classList.add('hidden');
        this.resetForm();
    }

    // DELETE - Remove expense
    async deleteExpense(id) {
        if (!confirm('Are you sure you want to delete this expense? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/expenses/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.loadExpenses();
                this.loadStats();
                this.showNotification('Expense deleted successfully! 🗑️', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to delete expense', 'error');
            }
        } catch (error) {
            this.showNotification('Network error occurred', 'error');
        }
    }

    // Quick Add functionality
    openQuickAdd() {
        document.getElementById('quickAddModal').classList.remove('hidden');
        document.getElementById('quickDescription').focus();
    }

    closeQuickAdd() {
        document.getElementById('quickAddModal').classList.add('hidden');
        document.getElementById('quickAddForm').reset();
    }

    async quickAddExpense() {
        const description = document.getElementById('quickDescription').value.trim();
        const amount = parseFloat(document.getElementById('quickAmount').value);

        if (!description || !amount || amount <= 0) {
            this.showNotification('Please fill all fields with valid data', 'error');
            return;
        }

        const formData = {
            description: description,
            amount: amount,
            date: new Date().toISOString().split('T')[0],
            category: 'Other'
        };

        try {
            const response = await fetch('/api/expenses', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.closeQuickAdd();
                this.loadExpenses();
                this.loadStats();
                this.showNotification('Expense added quickly! ⚡', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to add expense', 'error');
            }
        } catch (error) {
            this.showNotification('Network error occurred', 'error');
        }
    }

    // Stats and Charts
    async loadStats() {
        try {
            const params = new URLSearchParams();
            if (this.currentFilters.startDate) params.append('start_date', this.currentFilters.startDate);
            if (this.currentFilters.endDate) params.append('end_date', this.currentFilters.endDate);
            if (this.currentFilters.category && this.currentFilters.category !== 'All') {
                params.append('category', this.currentFilters.category);
            }

            const response = await fetch(`/api/expenses/stats?${params}`);
            const stats = await response.json();

            this.renderStats(stats);
            this.updateCharts(stats);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    renderStats(stats) {
        document.getElementById('totalAmount').textContent = `$${stats.total.toFixed(2)}`;
        document.getElementById('totalExpenses').textContent = stats.count;
        
        const avgExpense = stats.count > 0 ? (stats.total / stats.count) : 0;
        document.getElementById('avgExpense').textContent = `$${avgExpense.toFixed(2)}`;
        
        // Find top category
        let topCategory = '-';
        let maxAmount = 0;
        for (const [category, amount] of Object.entries(stats.by_category)) {
            if (amount > maxAmount) {
                maxAmount = amount;
                topCategory = category;
            }
        }
        document.getElementById('topCategory').textContent = topCategory;
    }

    setupCharts() {
        this.setupCategoryChart();
        this.setupTrendChart();
    }

    setupCategoryChart() {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        this.categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#10B981', '#3B82F6', '#8B5CF6', '#F59E0B',
                        '#EF4444', '#EC4899', '#06B6D4', '#84CC16', '#6B7280'
                    ],
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                family: 'Inter',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    setupTrendChart() {
        const ctx = document.getElementById('trendChart').getContext('2d');
        this.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Monthly Spending',
                    data: [],
                    borderColor: '#8B5CF6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#8B5CF6',
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            },
                            font: {
                                family: 'Inter'
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: 'Inter'
                            }
                        }
                    }
                }
            }
        });
    }

    updateCharts(stats) {
        // Update category chart
        const categories = Object.keys(stats.by_category);
        const amounts = Object.values(stats.by_category);
        
        this.categoryChart.data.labels = categories;
        this.categoryChart.data.datasets[0].data = amounts;
        this.categoryChart.update();

        // Update trend chart
        const months = Object.keys(stats.monthly_trend);
        const trendData = Object.values(stats.monthly_trend);
        
        this.trendChart.data.labels = months.map(month => {
            const [year, monthNum] = month.split('-');
            return new Date(year, monthNum - 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        });
        this.trendChart.data.datasets[0].data = trendData;
        this.trendChart.update();
    }

    // Helper methods
    getFormData() {
        return {
            description: document.getElementById('description').value.trim(),
            amount: parseFloat(document.getElementById('amount').value),
            date: document.getElementById('date').value,
            category: document.getElementById('category').value
        };
    }

    validateForm(formData) {
        if (!formData.description) {
            this.showNotification('Please enter a description', 'error');
            return false;
        }
        if (!formData.amount || formData.amount <= 0) {
            this.showNotification('Please enter a valid amount', 'error');
            return false;
        }
        if (!formData.date) {
            this.showNotification('Please select a date', 'error');
            return false;
        }
        if (!formData.category) {
            this.showNotification('Please select a category', 'error');
            return false;
        }
        return true;
    }

    resetForm() {
        document.getElementById('expenseForm').reset();
        this.setCurrentDate();
        document.getElementById('category').selectedIndex = 0;
    }

    applyFilters() {
        this.currentFilters = {
            startDate: document.getElementById('startDate').value,
            endDate: document.getElementById('endDate').value,
            category: document.getElementById('categoryFilter').value,
            search: document.getElementById('searchFilter').value
        };

        this.loadExpenses();
        this.loadStats();
    }

    resetFilters() {
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        document.getElementById('categoryFilter').value = 'All';
        document.getElementById('searchFilter').value = '';
        
        this.currentFilters = {
            startDate: '',
            endDate: '',
            category: 'All',
            search: ''
        };

        this.setCurrentDate();
        this.loadExpenses();
        this.loadStats();
    }

    async exportCSV() {
        try {
            const params = new URLSearchParams();
            if (this.currentFilters.startDate) params.append('start_date', this.currentFilters.startDate);
            if (this.currentFilters.endDate) params.append('end_date', this.currentFilters.endDate);
            if (this.currentFilters.category && this.currentFilters.category !== 'All') {
                params.append('category', this.currentFilters.category);
            }

            const response = await fetch(`/api/expenses/export?${params}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `expenses-${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification('CSV exported successfully! 📊', 'success');
            } else {
                this.showNotification('Failed to export CSV', 'error');
            }
        } catch (error) {
            this.showNotification('Network error occurred', 'error');
        }
    }

    showLoading(show) {
        const loadingElement = document.getElementById('loadingExpenses');
        const tableBody = document.getElementById('expensesTable');
        
        if (show) {
            loadingElement.classList.remove('hidden');
            tableBody.innerHTML = '';
        } else {
            loadingElement.classList.add('hidden');
        }
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    formatTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    showNotification(message, type) {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification fixed top-4 right-4 px-6 py-4 rounded-xl shadow-lg text-white font-semibold transform translate-x-full transition-transform duration-300 z-50 ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} mr-3"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Remove after 4 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 4000);
    }
}

// Initialize the expense tracker when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.expenseTracker = new ExpenseTracker();
});
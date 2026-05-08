const API = {
    base: '/api',

    async request(url, options = {}) {
        const config = {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        };
        const res = await fetch(this.base + url, config);
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: res.statusText }));
            throw new Error(err.error || '请求失败');
        }
        if (res.status === 204) return null;
        return res.json();
    },

    // Repositories
    getRepositories() {
        return this.request('/repositories');
    },

    addRepository(name, localPath) {
        return this.request('/repositories', {
            method: 'POST',
            body: JSON.stringify({ name, localPath }),
        });
    },

    deleteRepository(id) {
        return this.request(`/repositories/${id}`, { method: 'DELETE' });
    },

    // Reports
    getMonthlyReports(month, repositoryId) {
        const rid = repositoryId || 0;
        return this.request(`/reports?month=${month}&repositoryId=${rid}`);
    },

    getReportByDate(date, repositoryId) {
        const rid = repositoryId || 0;
        return this.request(`/reports/${date}?repositoryId=${rid}`);
    },

    createReport(date, repositoryId, data) {
        return this.request('/reports', {
            method: 'POST',
            body: JSON.stringify({ date, repositoryId: repositoryId || 0, ...data }),
        });
    },

    generateReport(date, repositoryId) {
        return this.request('/reports/generate', {
            method: 'POST',
            body: JSON.stringify({ date, repositoryId }),
        });
    },

    updateReport(id, data) {
        return this.request(`/reports/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    deleteReport(id) {
        return this.request(`/reports/${id}`, { method: 'DELETE' });
    },

    // Settings
    getSettings() {
        return this.request('/settings');
    },

    updateSettings(settings) {
        return this.request('/settings', {
            method: 'PUT',
            body: JSON.stringify(settings),
        });
    },
};

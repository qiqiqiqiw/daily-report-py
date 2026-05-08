const WeeklyAPI = {
    base: '/api/weekly-reports',

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

    getReport(date) {
        return this.request(`/${date}`);
    },

    generateReport(date) {
        return this.request('/generate', {
            method: 'POST',
            body: JSON.stringify({ date }),
        });
    },

    updateReport(id, data) {
        return this.request(`/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    deleteReport(id) {
        return this.request(`/${id}`, { method: 'DELETE' });
    },
};

const WeekApp = {
    currentMonday: null,
    currentReport: null,
    isEditing: false,

    init() {
        const today = new Date();
        const day = today.getDay();
        const diff = day === 0 ? -6 : 1 - day;
        this.currentMonday = new Date(today);
        this.currentMonday.setDate(today.getDate() + diff);

        this.bindEvents();
        this.loadWeek();
    },

    bindEvents() {
        document.getElementById('btnPrevWeek').addEventListener('click', () => this.prevWeek());
        document.getElementById('btnNextWeek').addEventListener('click', () => this.nextWeek());
        document.getElementById('btnGenerateWeek').addEventListener('click', () => this.generateReport());
        document.getElementById('btnEditWeek').addEventListener('click', () => this.enterEditMode());
        document.getElementById('btnCopyWeek').addEventListener('click', () => this.copyReport());
        document.getElementById('btnDeleteWeek').addEventListener('click', () => this.deleteReport());
        document.getElementById('btnSaveWeek').addEventListener('click', () => this.saveReport());
        document.getElementById('btnCancelWeekEdit').addEventListener('click', () => this.exitEditMode());
    },

    formatDate(d) {
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    },

    getMondayStr() {
        return this.formatDate(this.currentMonday);
    },

    getSundayStr() {
        const sunday = new Date(this.currentMonday);
        sunday.setDate(sunday.getDate() + 6);
        return this.formatDate(sunday);
    },

    updateTitle() {
        const m = this.currentMonday;
        const s = new Date(m);
        s.setDate(s.getDate() + 6);
        const fmt = `${m.getMonth() + 1}月${m.getDate()}日 - ${s.getMonth() + 1}月${s.getDate()}日`;
        document.getElementById('weekTitle').textContent = fmt;
    },

    async prevWeek() {
        this.currentMonday.setDate(this.currentMonday.getDate() - 7);
        this.loadWeek();
    },

    async nextWeek() {
        this.currentMonday.setDate(this.currentMonday.getDate() + 7);
        this.loadWeek();
    },

    async loadWeek() {
        this.updateTitle();
        this.isEditing = false;
        this.setWeekState('loading');

        try {
            const report = await WeeklyAPI.getReport(this.getMondayStr());
            if (report) {
                this.currentReport = report;
                this.renderContent(report.content);
                this.setWeekState('view');
            } else {
                this.setWeekState('empty');
            }
        } catch (e) {
            this.setWeekState('empty');
        }
    },

    renderContent(text) {
        const el = document.getElementById('weekContent');
        // 简单 markdown 渲染：# 标题, ## 子标题, 列表
        let html = text
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
            .replace(/(<li>.*<\/li>\n?)+/g, '<ol>$&</ol>')
            .replace(/^- (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        el.innerHTML = '<p>' + html + '</p>';
    },

    setWeekState(mode) {
        const loading = document.getElementById('weekLoading');
        const content = document.getElementById('weekContent');
        const empty = document.getElementById('weekEmpty');
        const actions = document.getElementById('weekActions');
        const editArea = document.getElementById('weekEditArea');
        const btnDelete = document.getElementById('btnDeleteWeek');

        loading.style.display = 'none';
        content.style.display = 'none';
        empty.style.display = 'none';
        actions.style.display = 'none';
        editArea.style.display = 'none';

        if (mode === 'loading') {
            loading.style.display = '';
            return;
        }

        actions.style.display = '';

        if (mode === 'view') {
            content.style.display = '';
            btnDelete.style.display = '';
        } else if (mode === 'empty') {
            empty.style.display = '';
            btnDelete.style.display = 'none';
            document.getElementById('btnEditWeek').style.display = 'none';
            document.getElementById('btnCopyWeek').style.display = 'none';
        } else if (mode === 'edit') {
            editArea.style.display = '';
            actions.style.display = 'none';
            document.getElementById('weekEditText').value = this.currentReport ? this.currentReport.content : '';
        }
    },

    enterEditMode() {
        this.isEditing = true;
        this.setWeekState('edit');
    },

    exitEditMode() {
        this.isEditing = false;
        if (this.currentReport) {
            this.renderContent(this.currentReport.content);
            this.setWeekState('view');
        } else {
            this.setWeekState('empty');
        }
    },

    async generateReport() {
        this.setWeekState('loading');
        try {
            const report = await WeeklyAPI.generateReport(this.getMondayStr());
            this.currentReport = report;
            this.renderContent(report.content);
            this.setWeekState('view');
            this.showToast('周报生成成功');
        } catch (e) {
            this.showToast('生成失败: ' + e.message, 'error');
            this.setWeekState('empty');
        }
    },

    async saveReport() {
        if (!this.currentReport) {
            this.showToast('请先生成周报', 'error');
            return;
        }
        try {
            const report = await WeeklyAPI.updateReport(this.currentReport.id, {
                content: document.getElementById('weekEditText').value,
            });
            this.currentReport = report;
            this.isEditing = false;
            this.renderContent(report.content);
            this.setWeekState('view');
            this.showToast('保存成功');
        } catch (e) {
            this.showToast('保存失败: ' + e.message, 'error');
        }
    },

    async deleteReport() {
        if (!this.currentReport) return;
        if (!confirm('确定删除该周报？')) return;
        try {
            await WeeklyAPI.deleteReport(this.currentReport.id);
            this.currentReport = null;
            this.setWeekState('empty');
            this.showToast('已删除');
        } catch (e) {
            this.showToast('删除失败: ' + e.message, 'error');
        }
    },

    copyReport() {
        const text = this.currentReport ? this.currentReport.content : '';
        if (!text) return;
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('已复制到剪贴板');
        }).catch(() => {
            this.showToast('复制失败，请手动复制', 'error');
        });
    },

    showToast(msg, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.className = 'toast show';
        toast.style.display = 'block';
        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => {
            toast.className = 'toast hide';
            setTimeout(() => { toast.style.display = 'none'; }, 200);
        }, 2500);
    },
};

document.addEventListener('DOMContentLoaded', () => WeekApp.init());

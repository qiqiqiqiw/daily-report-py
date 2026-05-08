const MonthlyAPI = {
    base: '/api/monthly-reports',

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

    getReport(year, month) {
        return this.request(`/${year}/${month}`);
    },

    generateReport(year, month) {
        return this.request('/generate', {
            method: 'POST',
            body: JSON.stringify({ year, month }),
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

const MonthApp = {
    currentYear: null,
    currentMonth: null,
    currentReport: null,
    isEditing: false,

    init() {
        const today = new Date();
        this.currentYear = today.getFullYear();
        this.currentMonth = today.getMonth() + 1;

        this.bindEvents();
        this.loadMonth();
    },

    bindEvents() {
        document.getElementById('btnPrevMonth').addEventListener('click', () => this.prevMonth());
        document.getElementById('btnNextMonth').addEventListener('click', () => this.nextMonth());
        document.getElementById('btnGenerateMonth').addEventListener('click', () => this.generateReport());
        document.getElementById('btnEditMonth').addEventListener('click', () => this.enterEditMode());
        document.getElementById('btnCopyMonth').addEventListener('click', () => this.copyReport());
        document.getElementById('btnDeleteMonth').addEventListener('click', () => this.deleteReport());
        document.getElementById('btnSaveMonth').addEventListener('click', () => this.saveReport());
        document.getElementById('btnCancelMonthEdit').addEventListener('click', () => this.exitEditMode());
    },

    updateTitle() {
        document.getElementById('monthTitle').textContent = `${this.currentYear}年${this.currentMonth}月`;
    },

    prevMonth() {
        this.currentMonth--;
        if (this.currentMonth < 1) {
            this.currentMonth = 12;
            this.currentYear--;
        }
        this.loadMonth();
    },

    nextMonth() {
        this.currentMonth++;
        if (this.currentMonth > 12) {
            this.currentMonth = 1;
            this.currentYear++;
        }
        this.loadMonth();
    },

    async loadMonth() {
        this.updateTitle();
        this.isEditing = false;
        this.setMonthState('loading');

        try {
            const report = await MonthlyAPI.getReport(this.currentYear, this.currentMonth);
            if (report) {
                this.currentReport = report;
                this.renderContent(report.content);
                this.setMonthState('view');
            } else {
                this.setMonthState('empty');
            }
        } catch (e) {
            this.setMonthState('empty');
        }
    },

    renderContent(text) {
        const el = document.getElementById('monthContent');
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

    setMonthState(mode) {
        const loading = document.getElementById('monthLoading');
        const content = document.getElementById('monthContent');
        const empty = document.getElementById('monthEmpty');
        const actions = document.getElementById('monthActions');
        const editArea = document.getElementById('monthEditArea');
        const btnDelete = document.getElementById('btnDeleteMonth');

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
            document.getElementById('btnEditMonth').style.display = 'none';
            document.getElementById('btnCopyMonth').style.display = 'none';
        } else if (mode === 'edit') {
            editArea.style.display = '';
            actions.style.display = 'none';
            document.getElementById('monthEditText').value = this.currentReport ? this.currentReport.content : '';
        }
    },

    enterEditMode() {
        this.isEditing = true;
        this.setMonthState('edit');
    },

    exitEditMode() {
        this.isEditing = false;
        if (this.currentReport) {
            this.renderContent(this.currentReport.content);
            this.setMonthState('view');
        } else {
            this.setMonthState('empty');
        }
    },

    async generateReport() {
        this.setMonthState('loading');
        try {
            const report = await MonthlyAPI.generateReport(this.currentYear, this.currentMonth);
            this.currentReport = report;
            this.renderContent(report.content);
            this.setMonthState('view');
            this.showToast('月报生成成功');
        } catch (e) {
            this.showToast('生成失败: ' + e.message, 'error');
            this.setMonthState('empty');
        }
    },

    async saveReport() {
        if (!this.currentReport) {
            this.showToast('请先生成月报', 'error');
            return;
        }
        try {
            const report = await MonthlyAPI.updateReport(this.currentReport.id, {
                content: document.getElementById('monthEditText').value,
            });
            this.currentReport = report;
            this.isEditing = false;
            this.renderContent(report.content);
            this.setMonthState('view');
            this.showToast('保存成功');
        } catch (e) {
            this.showToast('保存失败: ' + e.message, 'error');
        }
    },

    async deleteReport() {
        if (!this.currentReport) return;
        if (!confirm('确定删除该月报？')) return;
        try {
            await MonthlyAPI.deleteReport(this.currentReport.id);
            this.currentReport = null;
            this.setMonthState('empty');
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

document.addEventListener('DOMContentLoaded', () => MonthApp.init());

const CombinedAPI = {
    base: '/api/combined-reports',

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

    getMonthlyReports(month, type = 'combined', repositoryId = null) {
        let url = `?month=${month}&type=${type}`;
        if (repositoryId) url += `&repositoryId=${repositoryId}`;
        return this.request(url);
    },

    getReportByDate(date, type = 'combined', repositoryId = null) {
        let url = `/${date}?type=${type}`;
        if (repositoryId) url += `&repositoryId=${repositoryId}`;
        return this.request(url);
    },

    generateReport(date, type = 'combined', repositoryId = null) {
        const body = { date, type };
        if (repositoryId) body.repositoryId = repositoryId;
        return this.request('/generate', {
            method: 'POST',
            body: JSON.stringify(body),
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

const App = {
    repositories: [],
    currentReport: null,
    currentManagerReport: null,
    selectedDate: null,
    isEditing: false,
    menuOpen: false,
    viewMode: 'combined', // 'combined' | 'manager'

    async init() {
        await this.loadRepositories();
        await this.loadSettings();
        Calendar.init((dateStr, el) => this.onDateClick(dateStr, el));
        Calendar.onMonthChange = () => this.loadCalendarData();
        this.bindEvents();
        await this.loadCalendarData();
    },

    bindEvents() {
        // Menu
        document.getElementById('btnMenu').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleMenu();
        });
        document.getElementById('btnAddRepo').addEventListener('click', () => {
            this.closeMenu();
            this.openModalEl('repoModal', 'repoModalContent');
        });
        document.getElementById('btnManageRepos').addEventListener('click', () => {
            this.closeMenu();
            this.openManageRepos();
        });
        document.getElementById('btnSettings').addEventListener('click', () => {
            this.closeMenu();
            this.openSettings();
        });

        // Mode toggle
        document.getElementById('btnModeCombined').addEventListener('click', () => this.switchMode('combined'));
        document.getElementById('btnModeManager').addEventListener('click', () => this.switchMode('manager'));
        document.getElementById('headerRepoSelect').addEventListener('change', () => this.loadCalendarData());

        // Report Modal
        document.getElementById('btnCloseReport').addEventListener('click', () => this.closeModal('reportModal', 'reportModalContent'));
        document.getElementById('reportModal').querySelector('.modal-overlay').addEventListener('click', () => this.closeModal('reportModal', 'reportModalContent'));
        document.getElementById('btnGenerateReport').addEventListener('click', () => this.generateReport());
        document.getElementById('btnEditReport').addEventListener('click', () => this.enterEditMode());
        document.getElementById('btnSaveReport').addEventListener('click', () => this.saveReport());
        document.getElementById('btnCancelEdit').addEventListener('click', () => this.exitEditMode());
        document.getElementById('btnCopyReport').addEventListener('click', () => this.copyReport());
        document.getElementById('btnDeleteReport').addEventListener('click', () => this.deleteReport());

        // Manager Modal
        document.getElementById('btnCloseManager').addEventListener('click', () => this.closeModal('managerModal', 'managerModalContent'));
        document.getElementById('managerModal').querySelector('.modal-overlay').addEventListener('click', () => this.closeModal('managerModal', 'managerModalContent'));
        document.getElementById('btnGenerateManager').addEventListener('click', () => this.generateManagerReport());
        document.getElementById('btnEditManager').addEventListener('click', () => this.enterManagerEditMode());
        document.getElementById('btnSaveManager').addEventListener('click', () => this.saveManagerReport());
        document.getElementById('btnCancelManagerEdit').addEventListener('click', () => this.exitManagerEditMode());
        document.getElementById('btnCopyManager').addEventListener('click', () => this.copyManagerReport());
        document.getElementById('btnDeleteManager').addEventListener('click', () => this.deleteManagerReport());

        // Repo Modal
        document.getElementById('btnCloseRepo').addEventListener('click', () => this.closeModal('repoModal', 'repoModalContent'));
        document.getElementById('repoModal').querySelector('.modal-overlay').addEventListener('click', () => this.closeModal('repoModal', 'repoModalContent'));
        document.getElementById('btnConfirmAddRepo').addEventListener('click', () => this.addRepository());
        document.getElementById('btnCancelAddRepo').addEventListener('click', () => this.closeModal('repoModal', 'repoModalContent'));

        // Manage Repos Modal
        document.getElementById('btnCloseManageRepos').addEventListener('click', () => this.closeModal('manageReposModal', 'manageReposModalContent'));
        document.getElementById('manageReposModal').querySelector('.modal-overlay').addEventListener('click', () => this.closeModal('manageReposModal', 'manageReposModalContent'));

        // Settings Modal
        document.getElementById('btnCloseSettings').addEventListener('click', () => this.closeModal('settingsModal', 'settingsModalContent'));
        document.getElementById('settingsModal').querySelector('.modal-overlay').addEventListener('click', () => this.closeModal('settingsModal', 'settingsModalContent'));
        document.getElementById('btnSaveSettings').addEventListener('click', () => this.saveSettings());
        document.getElementById('btnCancelSettings').addEventListener('click', () => this.closeModal('settingsModal', 'settingsModalContent'));
        document.getElementById('btnToggleApiKey').addEventListener('click', () => this.toggleApiKeyVisibility());

        // Close menu on outside click
        document.addEventListener('click', (e) => {
            if (this.menuOpen && !e.target.closest('.menu-wrapper')) {
                this.closeMenu();
            }
        });
    },

    // === Mode Toggle ===

    switchMode(mode) {
        this.viewMode = mode;
        document.getElementById('btnModeCombined').classList.toggle('active', mode === 'combined');
        document.getElementById('btnModeManager').classList.toggle('active', mode === 'manager');
        const repoSelect = document.getElementById('headerRepoSelect');
        if (mode === 'manager') {
            this.populateHeaderRepoSelect();
            repoSelect.style.display = '';
        } else {
            repoSelect.style.display = 'none';
        }
        this.loadCalendarData();
    },

    // === Menu ===

    toggleMenu() {
        this.menuOpen = !this.menuOpen;
        document.getElementById('dropdownMenu').classList.toggle('open', this.menuOpen);
    },

    closeMenu() {
        this.menuOpen = false;
        document.getElementById('dropdownMenu').classList.remove('open');
    },

    // === Repositories ===

    async loadRepositories() {
        try {
            this.repositories = await API.getRepositories();
        } catch (e) {
            // ignore
        }
    },

    async addRepository() {
        const path = document.getElementById('inputRepoPath').value.trim();
        if (!path) {
            this.showToast('请输入仓库路径', 'error');
            return;
        }
        if (!path.startsWith('/') && !/^[A-Za-z]:/.test(path)) {
            this.showToast('请输入完整的绝对路径，例如 /Users/you/code/project', 'error');
            return;
        }
        const name = path.replace(/[\\/]+$/, '').split(/[\\/]/).pop() || path;
        try {
            await API.addRepository(name, path);
            this.closeModal('repoModal', 'repoModalContent');
            document.getElementById('inputRepoPath').value = '';
            await this.loadRepositories();
            this.showToast('仓库添加成功');
        } catch (e) {
            this.showToast('添加失败: ' + e.message, 'error');
        }
    },

    async openManageRepos() {
        await this.loadRepositories();
        const list = document.getElementById('repoList');
        if (this.repositories.length === 0) {
            list.innerHTML = '<p class="repo-list-empty">暂无仓库</p>';
        } else {
            list.innerHTML = this.repositories.map(r => `
                <div class="repo-list-item">
                    <div>
                        <div class="repo-name">${r.name}</div>
                        <div class="repo-path">${r.localPath}</div>
                    </div>
                    <button class="btn-icon" onclick="App.removeRepository(${r.id}, '${r.name}')">
                        <svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                    </button>
                </div>
            `).join('');
        }
        this.openModalEl('manageReposModal', 'manageReposModalContent');
    },

    async removeRepository(id, name) {
        if (!confirm(`确定删除仓库「${name}」？`)) return;
        try {
            await API.deleteRepository(id);
            await this.loadRepositories();
            this.openManageRepos();
            this.showToast('仓库已删除');
        } catch (e) {
            this.showToast('删除失败: ' + e.message, 'error');
        }
    },

    // === Settings ===

    async loadSettings() {
        try {
            await API.getSettings();
        } catch (e) {
            // ignore
        }
    },

    async openSettings() {
        try {
            const settings = await API.getSettings();
            document.getElementById('inputAutoGenerate').checked = settings.autoGenerateEnabled === 'true';
            if (settings.autoGenerateCron) {
                const parts = settings.autoGenerateCron.split(' ');
                const h = parts[1].padStart(2, '0');
                const m = parts[0].padStart(2, '0');
                document.getElementById('inputCronTime').value = `${h}:${m}`;
            }
            document.getElementById('inputAiApiUrl').value = settings.aiApiUrl || '';
            document.getElementById('inputAiApiKey').value = settings.aiApiKey || '';
            document.getElementById('inputAiModelName').value = settings.aiModelName || '';
        } catch (e) {
            // ignore
        }
        this.openModalEl('settingsModal', 'settingsModalContent');
    },

    async saveSettings() {
        const time = document.getElementById('inputCronTime').value;
        const [h, m] = time.split(':');
        const cron = `${Number(m)} ${Number(h)} * * ?`;

        const settings = {
            autoGenerateEnabled: document.getElementById('inputAutoGenerate').checked ? 'true' : 'false',
            autoGenerateCron: cron,
            aiApiUrl: document.getElementById('inputAiApiUrl').value.trim(),
            aiApiKey: document.getElementById('inputAiApiKey').value.trim(),
            aiModelName: document.getElementById('inputAiModelName').value.trim(),
        };
        try {
            await API.updateSettings(settings);
            this.closeModal('settingsModal', 'settingsModalContent');
            this.showToast('设置已保存');
        } catch (e) {
            this.showToast('保存失败: ' + e.message, 'error');
        }
    },

    // === Calendar ===

    async loadCalendarData() {
        const month = Calendar.getDateStr();
        const repositoryId = this.viewMode === 'manager' ? document.getElementById('headerRepoSelect').value : null;
        try {
            const reports = await CombinedAPI.getMonthlyReports(month, this.viewMode, repositoryId);
            Calendar.setReports(reports);
        } catch (e) {
            this.showToast('加载日历数据失败', 'error');
        }
    },

    // === Date Click ===

    async onDateClick(dateStr, cellEl) {
        this.selectedDate = dateStr;
        this.currentReport = null;
        this.currentManagerReport = null;
        this.isEditing = false;

        const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        const parts = dateStr.split('-');
        const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        const dateTitle = `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${weekdays[d.getDay()]}`;

        if (this.viewMode === 'manager') {
            document.getElementById('managerDateTitle').textContent = dateTitle + ' 团队日报';
            const repositoryId = document.getElementById('headerRepoSelect').value || null;
            this.setManagerState('loading');
            this.openModalEl('managerModal', 'managerModalContent', cellEl);
            try {
                const report = await CombinedAPI.getReportByDate(dateStr, 'manager', repositoryId);
                if (report) {
                    this.currentManagerReport = report;
                    this.setManagerState('view');
                } else {
                    this.setManagerState('empty');
                }
            } catch (e) {
                this.setManagerState('empty');
            }
        } else {
            document.getElementById('modalDateTitle').textContent = dateTitle + ' 日报';
            this.setReportState('loading');
            this.openModalEl('reportModal', 'reportModalContent', cellEl);
            try {
                const report = await CombinedAPI.getReportByDate(dateStr, 'combined');
                if (report) {
                    this.currentReport = report;
                    this.setReportState('view');
                } else {
                    this.setReportState('empty');
                }
            } catch (e) {
                this.setReportState('empty');
            }
        }
    },

    // === Combined Report (原有逻辑) ===

    setReportState(mode) {
        const view = document.getElementById('reportView');
        const editor = document.getElementById('reportEditor');
        const empty = document.getElementById('reportEmpty');
        const loading = document.getElementById('loadingSpinner');
        const viewActions = document.getElementById('viewActions');
        const editActions = document.getElementById('editActions');
        const status = document.getElementById('reportStatus');
        const btnDelete = document.getElementById('btnDeleteReport');
        const btnEdit = document.getElementById('btnEditReport');
        const btnCopy = document.getElementById('btnCopyReport');
        const btnGenerate = document.getElementById('btnGenerateReport');

        view.style.display = 'none';
        editor.style.display = 'none';
        empty.style.display = 'none';
        loading.style.display = 'none';
        viewActions.style.display = 'none';
        editActions.style.display = 'none';

        if (mode === 'loading') {
            loading.style.display = '';
            return;
        }

        viewActions.style.display = '';

        if (mode === 'view') {
            view.style.display = '';
            document.getElementById('viewCompleted').textContent = this.currentReport.completedTasks || '';
            document.getElementById('viewInProgress').textContent = this.currentReport.inProgressTasks || '';
            document.getElementById('viewNotes').textContent = this.currentReport.notes || '';
            status.textContent = this.currentReport.isEdited ? '手动编辑' : 'AI 汇总';
            btnDelete.style.display = '';
            btnEdit.style.display = '';
            btnCopy.style.display = '';
            btnGenerate.style.display = '';
        } else if (mode === 'empty') {
            empty.style.display = '';
            status.textContent = '';
            btnDelete.style.display = 'none';
            btnCopy.style.display = 'none';
            btnEdit.style.display = 'none';
            btnGenerate.style.display = '';
        } else if (mode === 'edit') {
            editor.style.display = '';
            viewActions.style.display = 'none';
            editActions.style.display = '';
            if (this.currentReport) {
                document.getElementById('editCompleted').value = this.currentReport.completedTasks || '';
                document.getElementById('editInProgress').value = this.currentReport.inProgressTasks || '';
                document.getElementById('editNotes').value = this.currentReport.notes || '';
            } else {
                document.getElementById('editCompleted').value = '';
                document.getElementById('editInProgress').value = '';
                document.getElementById('editNotes').value = '';
            }
        }
    },

    enterEditMode() {
        this.isEditing = true;
        this.setReportState('edit');
    },

    exitEditMode() {
        this.isEditing = false;
        if (this.currentReport) {
            this.setReportState('view');
        } else {
            this.setReportState('empty');
        }
    },

    async generateReport() {
        this.setReportState('loading');
        try {
            const report = await CombinedAPI.generateReport(this.selectedDate, 'combined');
            this.currentReport = report;
            this.setReportState('view');
            this.loadCalendarData();
            this.showToast('日报生成成功');
        } catch (e) {
            this.showToast('生成失败: ' + e.message, 'error');
            this.setReportState('empty');
        }
    },

    async saveReport() {
        const data = {
            completedTasks: document.getElementById('editCompleted').value,
            inProgressTasks: document.getElementById('editInProgress').value,
            notes: document.getElementById('editNotes').value,
        };
        try {
            if (this.currentReport) {
                const report = await CombinedAPI.updateReport(this.currentReport.id, data);
                this.currentReport = report;
            } else {
                this.showToast('请先生成日报', 'error');
                return;
            }
            this.isEditing = false;
            this.setReportState('view');
            this.loadCalendarData();
            this.showToast('保存成功');
        } catch (e) {
            this.showToast('保存失败: ' + e.message, 'error');
        }
    },

    async deleteReport() {
        if (!this.currentReport) return;
        if (!confirm('确定删除该日报？')) return;
        try {
            await CombinedAPI.deleteReport(this.currentReport.id);
            this.currentReport = null;
            this.isEditing = false;
            this.setReportState('empty');
            this.loadCalendarData();
            this.showToast('已删除');
        } catch (e) {
            this.showToast('删除失败: ' + e.message, 'error');
        }
    },

    copyReport() {
        let completed, inProgress, notes;
        if (this.isEditing) {
            completed = document.getElementById('editCompleted').value;
            inProgress = document.getElementById('editInProgress').value;
            notes = document.getElementById('editNotes').value;
        } else if (this.currentReport) {
            completed = this.currentReport.completedTasks;
            inProgress = this.currentReport.inProgressTasks;
            notes = this.currentReport.notes;
        } else {
            return;
        }

        const d = new Date(this.selectedDate);
        const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        const title = `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${weekdays[d.getDay()]} 日报`;
        const text = `${title}\n\n今日完成：\n${completed || '无'}\n\n进行中：\n${inProgress || '无'}\n\n备注：\n${notes || '无'}`;

        navigator.clipboard.writeText(text).then(() => {
            this.showToast('已复制到剪贴板');
        }).catch(() => {
            this.showToast('复制失败，请手动复制', 'error');
        });
    },

    // === Manager Report (管理者模式) ===

    populateHeaderRepoSelect() {
        const select = document.getElementById('headerRepoSelect');
        select.innerHTML = '<option value="">全部仓库</option>';
        for (const r of this.repositories) {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.textContent = r.name;
            select.appendChild(opt);
        }
    },

    renderManagerContent(text) {
        const el = document.getElementById('managerView');
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

    setManagerState(mode) {
        const view = document.getElementById('managerView');
        const editor = document.getElementById('managerEditor');
        const empty = document.getElementById('managerEmpty');
        const loading = document.getElementById('managerLoading');
        const viewActions = document.getElementById('managerViewActions');
        const editActions = document.getElementById('managerEditActions');
        const status = document.getElementById('managerStatus');
        const btnDelete = document.getElementById('btnDeleteManager');
        const btnEdit = document.getElementById('btnEditManager');
        const btnCopy = document.getElementById('btnCopyManager');
        const btnGenerate = document.getElementById('btnGenerateManager');

        view.style.display = 'none';
        editor.style.display = 'none';
        empty.style.display = 'none';
        loading.style.display = 'none';
        viewActions.style.display = 'none';
        editActions.style.display = 'none';

        if (mode === 'loading') {
            loading.style.display = '';
            return;
        }

        viewActions.style.display = '';

        if (mode === 'view') {
            view.style.display = '';
            this.renderManagerContent(this.currentManagerReport.completedTasks || '');
            status.textContent = this.currentManagerReport.isEdited ? '手动编辑' : 'AI 汇总';
            btnDelete.style.display = '';
            btnEdit.style.display = '';
            btnCopy.style.display = '';
            btnGenerate.style.display = '';
        } else if (mode === 'empty') {
            empty.style.display = '';
            status.textContent = '';
            btnDelete.style.display = 'none';
            btnCopy.style.display = 'none';
            btnEdit.style.display = 'none';
            btnGenerate.style.display = '';
        } else if (mode === 'edit') {
            editor.style.display = '';
            viewActions.style.display = 'none';
            editActions.style.display = '';
            document.getElementById('managerEditText').value = this.currentManagerReport ? this.currentManagerReport.completedTasks || '' : '';
        }
    },

    enterManagerEditMode() {
        this.isEditing = true;
        this.setManagerState('edit');
    },

    exitManagerEditMode() {
        this.isEditing = false;
        if (this.currentManagerReport) {
            this.setManagerState('view');
        } else {
            this.setManagerState('empty');
        }
    },

    async generateManagerReport() {
        this.setManagerState('loading');
        const repositoryId = document.getElementById('headerRepoSelect').value || null;
        try {
            const report = await CombinedAPI.generateReport(this.selectedDate, 'manager', repositoryId);
            this.currentManagerReport = report;
            this.setManagerState('view');
            this.loadCalendarData();
            this.showToast('团队日报生成成功');
        } catch (e) {
            this.showToast('生成失败: ' + e.message, 'error');
            this.setManagerState('empty');
        }
    },

    async saveManagerReport() {
        if (!this.currentManagerReport) {
            this.showToast('请先生成日报', 'error');
            return;
        }
        try {
            const report = await CombinedAPI.updateReport(this.currentManagerReport.id, {
                completedTasks: document.getElementById('managerEditText').value,
            });
            this.currentManagerReport = report;
            this.isEditing = false;
            this.setManagerState('view');
            this.loadCalendarData();
            this.showToast('保存成功');
        } catch (e) {
            this.showToast('保存失败: ' + e.message, 'error');
        }
    },

    async deleteManagerReport() {
        if (!this.currentManagerReport) return;
        if (!confirm('确定删除该团队日报？')) return;
        try {
            await CombinedAPI.deleteReport(this.currentManagerReport.id);
            this.currentManagerReport = null;
            this.isEditing = false;
            this.setManagerState('empty');
            this.loadCalendarData();
            this.showToast('已删除');
        } catch (e) {
            this.showToast('删除失败: ' + e.message, 'error');
        }
    },

    copyManagerReport() {
        const text = this.currentManagerReport ? this.currentManagerReport.completedTasks || '' : '';
        if (!text) return;
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('已复制到剪贴板');
        }).catch(() => {
            this.showToast('复制失败，请手动复制', 'error');
        });
    },

    // === Modal ===

    openModalEl(modalId, contentId, sourceEl) {
        const modal = document.getElementById(modalId);
        const content = document.getElementById(contentId);

        if (sourceEl) {
            const rect = sourceEl.getBoundingClientRect();
            const cx = window.innerWidth / 2;
            const cy = window.innerHeight / 2;
            content.style.setProperty('--morph-x', `${rect.left + rect.width / 2 - cx}px`);
            content.style.setProperty('--morph-y', `${rect.top + rect.height / 2 - cy}px`);
        } else {
            content.style.setProperty('--morph-x', '0px');
            content.style.setProperty('--morph-y', '20px');
        }

        content.classList.remove('morph-out');
        content.classList.add('morph-in');
        modal.style.display = 'flex';
    },

    closeModal(modalId, contentId) {
        const modal = document.getElementById(modalId);
        const content = document.getElementById(contentId);
        content.classList.remove('morph-in');
        content.classList.add('morph-out');
        setTimeout(() => {
            modal.style.display = 'none';
            content.classList.remove('morph-out');
        }, 200);
    },

    // === UI Helpers ===

    toggleApiKeyVisibility() {
        const input = document.getElementById('inputAiApiKey');
        const btn = document.getElementById('btnToggleApiKey');
        const eyeOpen = '<svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>';
        const eyeClosed = '<svg viewBox="0 0 24 24"><path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>';
        if (input.type === 'password') {
            input.type = 'text';
            btn.innerHTML = eyeClosed;
        } else {
            input.type = 'password';
            btn.innerHTML = eyeOpen;
        }
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

document.addEventListener('DOMContentLoaded', () => App.init());

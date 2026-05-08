const Calendar = {
    year: null,
    month: null,
    reportDates: new Set(),
    animating: false,
    onDateClick: null,

    init(onDateClick) {
        const now = new Date();
        this.year = now.getFullYear();
        this.month = now.getMonth();
        this.onDateClick = onDateClick;

        document.getElementById('btnPrev').addEventListener('click', () => this.prev());
        document.getElementById('btnNext').addEventListener('click', () => this.next());
    },

    render() {
        const grid = document.getElementById('calendarGrid');
        grid.innerHTML = '';

        const title = document.getElementById('calendarTitle');
        title.textContent = `${this.year}年${this.month + 1}月`;

        const firstDay = new Date(this.year, this.month, 1);
        let startDay = firstDay.getDay() - 1;
        if (startDay < 0) startDay = 6;

        const daysInMonth = new Date(this.year, this.month + 1, 0).getDate();
        const daysInPrevMonth = new Date(this.year, this.month, 0).getDate();

        const today = new Date();
        const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

        const cells = [];

        // Previous month trailing days
        for (let i = startDay - 1; i >= 0; i--) {
            const d = daysInPrevMonth - i;
            const m = this.month === 0 ? 12 : this.month;
            const y = this.month === 0 ? this.year - 1 : this.year;
            const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            cells.push({ day: d, dateStr, classes: ['other-month'] });
        }

        // Current month days
        for (let d = 1; d <= daysInMonth; d++) {
            const dateStr = `${this.year}-${String(this.month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const classes = [];
            if (dateStr === todayStr) classes.push('today');
            const dayOfWeek = new Date(this.year, this.month, d).getDay();
            if (dayOfWeek === 0 || dayOfWeek === 6) classes.push('weekend');
            cells.push({ day: d, dateStr, classes });
        }

        // Next month leading days
        const remaining = 42 - cells.length;
        for (let d = 1; d <= remaining; d++) {
            const m = this.month === 11 ? 1 : this.month + 2;
            const y = this.month === 11 ? this.year + 1 : this.year;
            const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            cells.push({ day: d, dateStr, classes: ['other-month'] });
        }

        // Render cells with stagger animation
        cells.forEach((cell, index) => {
            const div = document.createElement('div');
            div.className = 'day-cell ' + cell.classes.join(' ');
            div.dataset.date = cell.dateStr;
            div.textContent = cell.day;

            div.style.opacity = '0';
            div.style.animation = `staggerFadeIn 0.3s ease forwards`;
            div.style.animationDelay = `${index * 8}ms`;

            if (this.reportDates.has(cell.dateStr)) {
                const dot = document.createElement('span');
                dot.className = 'report-dot';
                div.appendChild(dot);
            }

            div.addEventListener('click', () => {
                if (this.onDateClick && !div.classList.contains('other-month')) {
                    this.onDateClick(cell.dateStr, div);
                }
            });

            grid.appendChild(div);
        });
    },

    getDateStr() {
        return `${this.year}-${String(this.month + 1).padStart(2, '0')}`;
    },

    setReports(reports) {
        this.reportDates = new Set(reports.map(r => r.reportDate));
        this.render();
    },

    prev() {
        if (this.animating) return;
        this.animating = true;
        const grid = document.getElementById('calendarGrid');
        grid.classList.add('slide-right');
        setTimeout(() => {
            this.month--;
            if (this.month < 0) { this.month = 11; this.year--; }
            grid.classList.remove('slide-right');
            this.render();
            this.animating = false;
            if (this.onMonthChange) this.onMonthChange();
        }, 250);
    },

    next() {
        if (this.animating) return;
        this.animating = true;
        const grid = document.getElementById('calendarGrid');
        grid.classList.add('slide-left');
        setTimeout(() => {
            this.month++;
            if (this.month > 11) { this.month = 0; this.year++; }
            grid.classList.remove('slide-left');
            this.render();
            this.animating = false;
            if (this.onMonthChange) this.onMonthChange();
        }, 250);
    },

    onMonthChange: null,
};

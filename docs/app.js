const supabase = {
    async fetch(endpoint, options = {}) {
        const url = `${SUPABASE_URL}${endpoint}`;
        const headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        const response = await fetch(url, { ...options, headers });
        if (!response.ok) {
            console.error('Supabase fetch error:', response.status, await response.text());
            throw new Error(`API error: ${response.status}`);
        }
        return response.json();
    }
};

async function fetchUserStats() {
    try {
        const data = await supabase.fetch(`/rest/v1/user_progress_stats?user_id=eq.${USER_ID}`);
        if (data && data.length > 0) {
            return data[0];
        }
        return null;
    } catch (error) {
        console.error('Error fetching user stats:', error);
        return null;
    }
}

async function fetchCompletedLessons() {
    try {
        const data = await supabase.fetch(
            `/rest/v1/completed_lesson?user_id=eq.${USER_ID}&select=*,lesson(title,topic_category,created_at)&order=completed_at.desc`
        );
        return data || [];
    } catch (error) {
        console.error('Error fetching completed lessons:', error);
        return [];
    }
}

async function fetchAttempts() {
    try {
        const data = await supabase.fetch(
            `/rest/v1/attempt?user_id=eq.${USER_ID}&select=*,question(difficulty,concept_tag,lesson_id)&order=answered_at.desc&limit=100`
        );
        return data || [];
    } catch (error) {
        console.error('Error fetching attempts:', error);
        return [];
    }
}

function updateStatsCards(stats) {
    document.getElementById('lessonsCompleted').textContent = stats?.lessons_completed || 0;
    document.getElementById('totalXP').textContent = stats?.total_xp || 0;
    document.getElementById('currentStreak').textContent = stats?.current_streak || 0;

    const accuracy = stats?.total_questions > 0
        ? Math.round((stats.correct_answers / stats.total_questions) * 100)
        : 0;
    document.getElementById('accuracy').textContent = `${accuracy}%`;
}

function generateHeatmap(completedLessons) {
    const heatmapEl = document.getElementById('heatmap');
    heatmapEl.innerHTML = '';

    const dateMap = {};
    completedLessons.forEach(lesson => {
        const date = new Date(lesson.completed_at).toISOString().split('T')[0];
        dateMap[date] = (dateMap[date] || 0) + 1;
    });

    const today = new Date();
    const weeks = 12;
    const months = {};

    for (let i = weeks * 7 - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        const monthKey = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

        if (!months[monthKey]) {
            months[monthKey] = [];
        }

        const count = dateMap[dateStr] || 0;
        let level = 0;
        if (count > 0) level = 1;
        if (count >= 2) level = 2;
        if (count >= 3) level = 3;
        if (count >= 5) level = 4;

        months[monthKey].push({
            date: dateStr,
            count,
            level
        });
    }

    Object.entries(months).forEach(([month, days]) => {
        const monthDiv = document.createElement('div');
        monthDiv.className = 'heatmap-month';

        const label = document.createElement('div');
        label.className = 'month-label';
        label.textContent = month;
        monthDiv.appendChild(label);

        const grid = document.createElement('div');
        grid.className = 'heatmap-grid';

        days.forEach(day => {
            const dayEl = document.createElement('div');
            dayEl.className = `heatmap-day level-${day.level}`;
            dayEl.setAttribute('data-date', day.date);
            dayEl.setAttribute('data-count', day.count);
            grid.appendChild(dayEl);
        });

        monthDiv.appendChild(grid);
        heatmapEl.appendChild(monthDiv);
    });
}

function createXPChart(completedLessons) {
    const ctx = document.getElementById('xpChart').getContext('2d');

    const xpByDate = {};
    let cumulativeXP = 0;

    completedLessons
        .slice()
        .reverse()
        .forEach(lesson => {
            const date = new Date(lesson.completed_at).toISOString().split('T')[0];
            cumulativeXP += lesson.xp_earned || 0;
            xpByDate[date] = cumulativeXP;
        });

    const dates = Object.keys(xpByDate).slice(-30);
    const xpValues = dates.map(date => xpByDate[date]);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
            datasets: [{
                label: 'Cumulative XP',
                data: xpValues,
                borderColor: '#10B981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#94A3B8'
                    },
                    grid: {
                        color: '#334155'
                    }
                },
                x: {
                    ticks: {
                        color: '#94A3B8'
                    },
                    grid: {
                        color: '#334155'
                    }
                }
            }
        }
    });
}

function createAccuracyChart(attempts) {
    const ctx = document.getElementById('accuracyChart').getContext('2d');

    const accuracyByDate = {};

    attempts.forEach(attempt => {
        const date = new Date(attempt.answered_at).toISOString().split('T')[0];
        if (!accuracyByDate[date]) {
            accuracyByDate[date] = { correct: 0, total: 0 };
        }
        accuracyByDate[date].total++;
        if (attempt.is_correct) {
            accuracyByDate[date].correct++;
        }
    });

    const dates = Object.keys(accuracyByDate).sort().slice(-30);
    const accuracyValues = dates.map(date => {
        const { correct, total } = accuracyByDate[date];
        return Math.round((correct / total) * 100);
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
            datasets: [{
                label: 'Accuracy %',
                data: accuracyValues,
                backgroundColor: '#4F46E5',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: '#94A3B8',
                        callback: value => value + '%'
                    },
                    grid: {
                        color: '#334155'
                    }
                },
                x: {
                    ticks: {
                        color: '#94A3B8'
                    },
                    grid: {
                        color: '#334155'
                    }
                }
            }
        }
    });
}

function displayTopicMastery(completedLessons) {
    const topicEl = document.getElementById('topicMastery');

    const topicCounts = {};
    completedLessons.forEach(lesson => {
        const topic = lesson.lesson?.topic_category || 'General';
        topicCounts[topic] = (topicCounts[topic] || 0) + 1;
    });

    if (Object.keys(topicCounts).length === 0) {
        topicEl.innerHTML = '<p class="loading">No topics completed yet</p>';
        return;
    }

    const sorted = Object.entries(topicCounts).sort((a, b) => b[1] - a[1]);
    const maxCount = sorted[0][1];

    topicEl.innerHTML = sorted.map(([topic, count]) => `
        <div class="topic-item">
            <div class="topic-name">${topic}</div>
            <div class="topic-progress">
                <div class="topic-progress-bar" style="width: ${(count / maxCount) * 100}%"></div>
            </div>
            <div class="topic-count">${count} lesson${count !== 1 ? 's' : ''}</div>
        </div>
    `).join('');
}

function displayRecentActivity(completedLessons) {
    const activityEl = document.getElementById('recentActivity');

    if (completedLessons.length === 0) {
        activityEl.innerHTML = '<p class="loading">No lessons completed yet</p>';
        return;
    }

    const recent = completedLessons.slice(0, 10);

    activityEl.innerHTML = recent.map(lesson => {
        const date = new Date(lesson.completed_at);
        const timeAgo = formatTimeAgo(date);
        const score = `${lesson.questions_correct}/${lesson.total_questions}`;

        return `
            <div class="activity-item">
                <div class="activity-icon">📚</div>
                <div class="activity-content">
                    <div class="activity-title">${lesson.lesson?.title || 'Lesson'}</div>
                    <div class="activity-meta">${timeAgo} • ${lesson.lesson?.topic_category || 'General'}</div>
                </div>
                <div class="activity-stats">
                    <div class="activity-xp">+${lesson.xp_earned} XP</div>
                    <div class="activity-score">${score} correct</div>
                </div>
            </div>
        `;
    }).join('');
}

function formatTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };

    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval !== 1 ? 's' : ''} ago`;
        }
    }

    return 'Just now';
}

async function initDashboard() {
    console.log('Initializing dashboard...');

    try {
        const [stats, completedLessons, attempts] = await Promise.all([
            fetchUserStats(),
            fetchCompletedLessons(),
            fetchAttempts()
        ]);

        console.log('Stats:', stats);
        console.log('Completed lessons:', completedLessons.length);
        console.log('Attempts:', attempts.length);

        if (stats) {
            updateStatsCards(stats);
        }

        generateHeatmap(completedLessons);
        createXPChart(completedLessons);
        createAccuracyChart(attempts);
        displayTopicMastery(completedLessons);
        displayRecentActivity(completedLessons);

        document.getElementById('lastUpdated').textContent = new Date().toLocaleString();

        console.log('Dashboard initialized successfully!');
    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
}

document.addEventListener('DOMContentLoaded', initDashboard);
setInterval(initDashboard, 5 * 60 * 1000);

// DailyCommit Dashboard — GitHub Pages frontend
// Fetches public data from Supabase using the anon key

const SUPABASE_URL = 'YOUR_SUPABASE_URL'; // Replace during setup
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY'; // Replace during setup

async function fetchPublicStats() {
    try {
        const response = await fetch(`${SUPABASE_URL}/rest/v1/v_public_stats`, {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch stats');
        }

        const data = await response.json();
        const stats = data[0] || {};

        document.getElementById('current-streak').textContent = stats.current_streak || '0';
        document.getElementById('longest-streak').textContent = stats.longest_streak || '0';
        document.getElementById('level').textContent = stats.level || '1';
        document.getElementById('xp').textContent = stats.xp || '0';
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchRecentLessons() {
    try {
        const response = await fetch(`${SUPABASE_URL}/rest/v1/v_recent_lessons?limit=10`, {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch lessons');
        }

        const lessons = await response.json();
        const container = document.getElementById('recent-lessons');

        if (lessons.length === 0) {
            container.innerHTML = '<p class="placeholder">No lessons yet</p>';
            return;
        }

        container.innerHTML = lessons.map(lesson => `
            <div class="lesson-card">
                <div class="lesson-title">${lesson.title}</div>
                <div class="lesson-meta">
                    ${lesson.topic || 'General'} •
                    ${lesson.lesson_date} •
                    Difficulty: ${'⭐'.repeat(lesson.difficulty)}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error fetching lessons:', error);
        document.getElementById('recent-lessons').innerHTML =
            '<p class="placeholder">Failed to load lessons</p>';
    }
}

async function fetchActivityHeatmap() {
    try {
        const response = await fetch(`${SUPABASE_URL}/rest/v1/daily_activity?order=activity_date.desc&limit=90`, {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch activity');
        }

        const activities = await response.json();
        const container = document.getElementById('heatmap');

        if (activities.length === 0) {
            container.innerHTML = '<p class="placeholder">No activity yet</p>';
            return;
        }

        // Simple visualization (can be enhanced with a heatmap library)
        const activityDays = activities.filter(a => a.completed).length;
        container.innerHTML = `<p style="text-align: center; font-size: 1.2rem;">
            ${activityDays} active days in the last 90 days 🔥
        </p>`;
    } catch (error) {
        console.error('Error fetching activity:', error);
        document.getElementById('heatmap').innerHTML =
            '<p class="placeholder">Failed to load activity</p>';
    }
}

// Load data on page load
document.addEventListener('DOMContentLoaded', () => {
    fetchPublicStats();
    fetchRecentLessons();
    fetchActivityHeatmap();
});

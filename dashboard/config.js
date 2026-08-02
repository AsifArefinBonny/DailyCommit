// Supabase Configuration
const SUPABASE_URL = 'https://ybblpzymovvngtllrsbn.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU2MDUyNTgsImV4cCI6MjEwMTE4MTI1OH0.Pc20OJMYQs7PJ1-WXVR3qKJRVwvTDBjLxb67w03c1NI';

// Get user ID from URL parameter or localStorage
function getUserId() {
    const urlParams = new URLSearchParams(window.location.search);
    const userParam = urlParams.get('user');

    if (userParam) {
        // Store in localStorage for future visits
        localStorage.setItem('dailycommit_user_id', userParam);
        return userParam;
    }

    // Check localStorage
    const stored = localStorage.getItem('dailycommit_user_id');
    if (stored) {
        return stored;
    }

    // Default fallback
    return '6676414504';
}

const USER_ID = getUserId();

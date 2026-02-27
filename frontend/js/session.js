// Session Management Utility

const Session = {
    // Save user session to localStorage
    save(userData) {
        localStorage.setItem('hospital_user', JSON.stringify(userData));
    },

    // Get current user session
    get() {
        const data = localStorage.getItem('hospital_user');
        return data ? JSON.parse(data) : null;
    },

    // Clear session (logout)
    clear() {
        localStorage.removeItem('hospital_user');
    },

    // Check if user is authenticated
    isAuthenticated() {
        return this.get() !== null;
    },

    // Require authentication - redirect to login if not authenticated
    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    },

    // Require specific role - redirect to login if wrong role
    requireRole(role) {
        const user = this.get();
        if (!user || user.role !== role) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    },

    // Logout and redirect to login
    logout() {
        this.clear();
        window.location.href = '/login.html';
    }
};

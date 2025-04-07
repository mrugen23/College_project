// Common Navbar Component

class Navbar {
    constructor(activeLink = null) {
        this.activeLink = activeLink;
    }

    render() {
        // Get current user info
        const username = localStorage.getItem('username') || 'User';
        const token = localStorage.getItem('token');
        
        // Check if user is logged in
        if (!token) {
            return this.renderAuthNavbar();
        }
        
        const navbarHTML = `
            <nav class="navbar">
                <a href="home.html" class="navbar-brand">
                    <img src="wealth.png" alt="Personal Finance Tracker">
                    <span>Finance Tracker</span>
                </a>
                <ul class="navbar-nav">
                    <li><a href="home.html" class="nav-link ${this.activeLink === 'home' ? 'active' : ''}">Dashboard</a></li>
                    <li><a href="expenses.html" class="nav-link ${this.activeLink === 'expenses' ? 'active' : ''}">Expenses</a></li>
                    <li><a href="budgets.html" class="nav-link ${this.activeLink === 'budgets' ? 'active' : ''}">Budgets</a></li>
                    <li><a href="groups.html" class="nav-link ${this.activeLink === 'groups' ? 'active' : ''}">Groups</a></li>
                    <li><a href="profile.html" class="nav-link ${this.activeLink === 'profile' ? 'active' : ''}">Profile</a></li>
                </ul>
                <button class="navbar-mobile-toggle" id="navbarToggle">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
            </nav>
        `;
        
        this.initNavbarToggle();
        return navbarHTML;
    }
    
    renderAuthNavbar() {
        return `
            <nav class="navbar">
                <a href="login.html" class="navbar-brand">
                    <img src="wealth.png" alt="Personal Finance Tracker">
                    <span>Finance Tracker</span>
                </a>
                <ul class="navbar-nav">
                    <li><a href="login.html" class="nav-link ${this.activeLink === 'login' ? 'active' : ''}">Login</a></li>
                    <li><a href="register.html" class="nav-link ${this.activeLink === 'register' ? 'active' : ''}">Register</a></li>
                </ul>
            </nav>
        `;
    }
    
    initNavbarToggle() {
        // Add event listener for mobile toggle
        document.addEventListener('DOMContentLoaded', () => {
            const toggleButton = document.getElementById('navbarToggle');
            const navbarNav = document.querySelector('.navbar-nav');
            
            if (toggleButton && navbarNav) {
                toggleButton.addEventListener('click', () => {
                    navbarNav.classList.toggle('active');
                });
            }
        });
    }
}

// Function to add navbar to page
function addNavbar(activeLink) {
    const navbar = new Navbar(activeLink);
    
    // Create a container for the navbar if it doesn't exist
    let navbarContainer = document.getElementById('navbar-container');
    if (!navbarContainer) {
        navbarContainer = document.createElement('div');
        navbarContainer.id = 'navbar-container';
        document.body.prepend(navbarContainer);
    }
    
    navbarContainer.innerHTML = navbar.render();
}

// Export the function
window.addNavbar = addNavbar; 
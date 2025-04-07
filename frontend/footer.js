// Common Footer Component

class Footer {
    constructor() {
        // Constructor can be used for any initialization
    }

    render() {
        const currentYear = new Date().getFullYear();
        const footerHTML = `
            <footer class="site-footer">
                <div class="footer-content">
                    <div class="footer-section">
                        <h3>Personal Finance Tracker</h3>
                        <p>Take control of your finances with our simple and effective tools.</p>
                    </div>
                    <div class="footer-section">
                        <h3>Quick Links</h3>
                        <ul>
                            <li><a href="home.html">Dashboard</a></li>
                            <li><a href="expenses.html">Expenses</a></li>
                            <li><a href="budgets.html">Budgets</a></li>
                            <li><a href="groups.html">Groups</a></li>
                        </ul>
                    </div>
                    <div class="footer-section">
                        <h3>Contact</h3>
                        <p>Email: support@finance-tracker.com</p>
                        <p>Phone: +91 1234567890</p>
                    </div>
                </div>
                <div class="footer-bottom">
                    <p>&copy; ${currentYear} Personal Finance Tracker. All rights reserved.</p>
                </div>
            </footer>
        `;
        
        return footerHTML;
    }
}

// Function to add footer to page
function addFooter() {
    const footer = new Footer();
    
    // Create a container for the footer if it doesn't exist
    let footerContainer = document.getElementById('footer-container');
    if (!footerContainer) {
        footerContainer = document.createElement('div');
        footerContainer.id = 'footer-container';
        document.body.appendChild(footerContainer);
    }
    
    footerContainer.innerHTML = footer.render();
}

// Export the function
window.addFooter = addFooter; 
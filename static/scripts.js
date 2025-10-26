document.addEventListener('DOMContentLoaded', function() {
    // Hamburger Menu Toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            menuToggle.classList.toggle('active');
            mobileMenu.classList.toggle('active');
        });
    }

    // Auto-hide Alerts
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // Form Validation for Registration
    const registerForm = document.querySelector('form[action*="/register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', e => {
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirm_password');
            if (password && confirmPassword && password.value !== confirmPassword.value) {
                e.preventDefault();
                alert('Passwords do not match!');
            }
        });
    }

    // Form Validation for Edit Account
    const editForm = document.querySelector('form[action*="/edit_account"]');
    if (editForm) {
        editForm.addEventListener('submit', e => {
            const password = document.querySelector('input[name="password"]');
            const confirmPassword = document.querySelector('input[name="confirm_password"]');
            if (password && confirmPassword && password.value !== confirmPassword.value) {
                e.preventDefault();
                alert('Passwords do not match!');
            }
        });
    }

    // Loading State for Buttons
    document.querySelectorAll('.btn, button[type="submit"]').forEach(button => {
        button.addEventListener('click', function() {
            if (this.form) {
                this.classList.add('loading');
            }
        });
    });

    // Smooth Scrolling
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Logout Confirmation
    const logoutLink = document.querySelector('a[href*="logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', e => {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    }

    // File Upload Preview
    const fileInput = document.querySelector('input[name="valid_id"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const allowedTypes = ['image/png', 'image/jpg', 'image/jpeg', 'application/pdf'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Please select a valid file (PNG, JPG, JPEG, or PDF).');
                    this.value = '';
                } else if (file.size > 5 * 1024 * 1024) {
                    alert('File size must be less than 5MB.');
                    this.value = '';
                }
            }
        });
    }

    // Language Switcher Confirmation
    document.querySelectorAll('a[href*="set_language"]').forEach(link => {
        link.addEventListener('click', e => {
            if (!confirm('Switching language will reload the page. Continue?')) {
                e.preventDefault();
            }
        });
    });

    // Table Row Highlight
    document.querySelectorAll('table tr').forEach(row => {
        row.addEventListener('click', () => {
            row.classList.toggle('selected');
        });
    });

    // Dynamic Stats Update
    document.querySelectorAll('.stat-card p').forEach(card => {
        const originalText = card.textContent;
        card.addEventListener('mouseenter', function() {
            this.textContent = 'Updating...';
            setTimeout(() => {
                this.textContent = originalText;
            }, 1000);
        });
    });

    // Keyboard Navigation
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            if (mobileMenu && mobileMenu.classList.contains('active')) {
                menuToggle.classList.remove('active');
                mobileMenu.classList.remove('active');
            }
        }
    });

    // Prevent Form Resubmission
    if (window.history.replaceState) {
        window.history.replaceState(null, null, window.location.href);
    }

    console.log('Barangay e-Document System JS Loaded');
});
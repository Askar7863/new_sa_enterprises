document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const messageDiv = document.getElementById('message');

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent default form submission

            // Clear previous messages
            messageDiv.textContent = '';
            messageDiv.className = 'message'; // Reset classes
            messageDiv.style.display = 'none';

            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();

            // Client-side validation
            if (!name || !email || !password) {
                displayMessage('All fields are required.', 'error');
                return;
            }

            if (!validateEmail(email)) {
                displayMessage('Please enter a valid email address.', 'error');
                return;
            }

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, email, password })
                });

                const data = await response.json();

                if (response.ok) {
                    displayMessage(data.message, 'success');
                    // In a real application, you might redirect the user or store a token
                    console.log('User logged in:', data.user);
                    // Example: setTimeout(() => window.location.href = '/dashboard', 2000);
                } else {
                    displayMessage(data.message || 'Login failed', 'error');
                }
            } catch (error) {
                console.error('Error during login:', error);
                displayMessage('An error occurred. Please try again later.', 'error');
            }
        });
    }

    function displayMessage(message, type) {
        messageDiv.textContent = message;
        messageDiv.style.display = 'block';
        messageDiv.classList.add(type); // 'success' or 'error'
    }

    function validateEmail(email) {
        const re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }
});

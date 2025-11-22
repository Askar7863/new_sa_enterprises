/**
 * app.js
 * This file defines the client-side logic for a login page.
 * It creates a dynamic login form, handles user input, performs basic validation,
 * simulates an API call for login, and updates the UI based on the login status.
 *
 * To use this file, ensure you have an index.html with a div element like:
 * <div id="app-root"></div>
 * And include this script in your HTML:
 * <script src="app.js"></script>
 */

class LoginPage {
    /**
     * Initializes the LoginPage component.
     * @param {string} rootElementId - The ID of the HTML element where the login page should be rendered.
     */
    constructor(rootElementId) {
        this.root = document.getElementById(rootElementId);
        if (!this.root) {
            console.error(`Root element with ID '${rootElementId}' not found. Cannot initialize LoginPage.`);
            return;
        }

        this.state = {
            username: '',
            password: '',
            error: '',
            isLoggedIn: false,
            loading: false,
        };
        this.render(); // Initial render of the login form
    }

    /**
     * Updates the component's state and triggers a re-render.
     * @param {object} newState - An object containing the state properties to update.
     */
    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.render();
    }

    /**
     * Handles changes in input fields (username, password).
     * Updates the corresponding state property and clears any existing error messages.
     * @param {Event} event - The DOM event object from the input change.
     */
    handleChange = (event) => {
        try {
            const { name, value } = event.target;
            this.setState({ [name]: value, error: '' }); // Clear error on input change
        } catch (error) {
            console.error('Error handling input change:', error);
            this.setState({ error: 'An internal error occurred during input processing.' });
        }
    };

    /**
     * Handles the form submission for login.
     * Prevents default form submission, performs validation, and simulates an API call.
     * @param {Event} event - The DOM event object from the form submission.
     */
    handleSubmit = async (event) => {
        event.preventDefault();
        this.setState({ loading: true, error: '' }); // Show loading state, clear previous errors

        const { username, password } = this.state;

        // Client-side validation
        if (!username.trim() || !password.trim()) {
            this.setState({ error: 'Please enter both username and password.', loading: false });
            return;
        }

        try {
            // Simulate API call to a backend service
            const response = await this.mockLoginApi(username, password);

            if (response.success) {
                this.setState({ isLoggedIn: true, error: '', loading: false });
                alert(`Login successful! Welcome ${username}.`);
                // In a real application, you would store authentication tokens (e.g., in localStorage),
                // redirect the user to a dashboard, or update the application state for authenticated access.
            } else {
                this.setState({ error: response.message || 'Login failed. Please try again.', loading: false });
            }
        } catch (err) {
            console.error('Login submission error:', err);
            this.setState({ error: 'An unexpected network error occurred. Please try again later.', loading: false });
        }
    };

    /**
     * Simulates an asynchronous API call to a login endpoint.
     * This function mimics network delay and backend authentication logic.
     * @param {string} username - The username provided by the user.
     * @param {string} password - The password provided by the user.
     * @returns {Promise<object>} A promise that resolves with an object indicating success or failure.
     */
    mockLoginApi = (username, password) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                if (username === 'user' && password === 'pass') {
                    resolve({ success: true, message: 'Logged in successfully' });
                } else {
                    resolve({ success: false, message: 'Invalid username or password' });
                }
            }, 1500); // Simulate network delay of 1.5 seconds
        });
    };

    /**
     * Renders the login page HTML based on the current component state.
     * This method dynamically updates the content of the root element.
     */
    render() {
        if (!this.root) {
            // If root element was not found during constructor, prevent further errors
            return;
        }

        const { username, password, error, isLoggedIn, loading } = this.state;

        // Clear previous content to prepare for re-rendering
        this.root.innerHTML = '';

        if (isLoggedIn) {
            // Render success message if logged in
            this.root.innerHTML = `
                <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin-top: 50px; padding: 20px; background-color: #e6ffe6; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: fit-content; margin-left: auto; margin-right: auto;">
                    <h2 style="color: #28a745;">Welcome, ${username}!</h2>
                    <p style="color: #333;">You have successfully logged in.</p>
                    <p style="color: #666; font-size: 0.9em;">This is a client-side mock. In a real app, you'd be redirected.</p>
                    <button 
                        onclick="window.location.reload()" 
                        style="padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1em; margin-top: 15px;"
                    >
                        Logout / Try Again
                    </button>
                </div>
            `;
            return;
        }

        // Render the login form
        const formHtml = `
            <div style="width: 320px; margin: 60px auto; padding: 25px; border: 1px solid #e0e0e0; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); background-color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <h2 style="text-align: center; color: #333; margin-bottom: 25px;">Login to Your Account</h2>
                ${error ? `<p style="color: #dc3545; text-align: center; margin-bottom: 15px; font-size: 0.9em; padding: 8px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;">${error}</p>` : ''}
                <form id="login-form">
                    <div style="margin-bottom: 20px;">
                        <label for="username" style="display: block; margin-bottom: 8px; color: #555; font-size: 0.95em;">Username:</label>
                        <input
                            type="text"
                            id="username"
                            name="username"
                            value="${username}"
                            placeholder="Enter username (e.g., user)"
                            style="width: 100%; padding: 12px; border: 1px solid #ced4da; border-radius: 6px; box-sizing: border-box; font-size: 1em;"
                            required
                            autocomplete="username"
                        />
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label for="password" style="display: block; margin-bottom: 8px; color: #555; font-size: 0.95em;">Password:</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            value="${password}"
                            placeholder="Enter password (e.g., pass)"
                            style="width: 100%; padding: 12px; border: 1px solid #ced4da; border-radius: 6px; box-sizing: border-box; font-size: 1em;"
                            required
                            autocomplete="current-password"
                        />
                    </div>
                    <button
                        type="submit"
                        id="submit-button"
                        style="width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1.1em; font-weight: 600; transition: background-color 0.2s ease;"
                        ${loading ? 'disabled' : ''}
                    >
                        ${loading ? 'Logging in...' : 'Login'}
                    </button>
                     <p style="text-align: center; margin-top: 20px; font-size: 0.85em; color: #777;">Hint: Use username 'user' and password 'pass'</p>
                </form>
            </div>
        `;

        this.root.innerHTML = formHtml;

        // Attach event listeners after the HTML elements have been added to the DOM
        const form = this.root.querySelector('#login-form');
        const usernameInput = this.root.querySelector('#username');
        const passwordInput = this.root.querySelector('#password');

        if (form && usernameInput && passwordInput) {
            form.addEventListener('submit', this.handleSubmit);
            usernameInput.addEventListener('input', this.handleChange);
            passwordInput.addEventListener('input', this.handleChange);
        } else {
            console.error('Failed to find form elements after rendering. Event listeners not attached.');
        }
    }
}

// Initialize the LoginPage when the DOM is fully loaded.
// It expects an HTML element with id="app-root" to exist in the document.
document.addEventListener('DOMContentLoaded', () => {
    new LoginPage('app-root');
});

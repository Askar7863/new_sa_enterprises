from flask import Flask, render_template, request, redirect, url_for, flash, session
import os

app = Flask(__name__)

# CRITICAL: A strong secret key is essential for production.
# It's used for securely signing the session cookie, protecting against data tampering.
# For production, load this from an environment variable (e.g., os.environ.get('SECRET_KEY'))
# rather than hardcoding it or generating it dynamically on each run.
app.config['SECRET_KEY'] = os.urandom(24) # Generates a random 24-byte key for demonstration

# --- A simple in-memory "database" for user credentials (FOR DEMONSTRATION ONLY) ---
# In a real-world application, user data would be stored in a secure database (e.g., PostgreSQL, MySQL)
# and passwords would NEVER be stored in plain text. Instead, they would be securely hashed
# using a strong, industry-standard algorithm like bcrypt.
USERS = {
    "user1": "password123",
    "admin": "securepass"
}

@app.route('/')
def index():
    """Redirects the root URL to the login page."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login requests.

    - On GET: Renders the login form.
    - On POST: Processes the submitted login credentials.
    """
    # If the user is already logged in, redirect them to the dashboard.
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Basic input validation: check if fields are empty
        if not username or not password:
            flash('Both username and password are required.', 'error')
            return render_template('login.html')

        # --- Credential validation (AGAIN, DO NOT use plain text passwords in production) ---
        # In a production app, you would hash the provided password and compare it
        # to the stored hash from your database.
        if username in USERS and USERS[username] == password:
            session['username'] = username  # Store username in the session to indicate logged-in state
            flash(f'Login successful! Welcome, {username}.', 'success')
            return redirect(url_for('dashboard'))
        else:
            # For security, avoid giving specific hints (e.g., 'username not found' or 'incorrect password').
            flash('Invalid username or password.', 'error')
            return render_template('login.html')

    # For GET requests, simply render the login page.
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Displays a simple dashboard page for logged-in users."""
    # Ensure only authenticated users can access the dashboard.
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        flash('Please log in to access the dashboard.', 'info')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logs out the current user by clearing their session."""
    session.pop('username', None)  # Remove the username from the session
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # In debug mode, the server will reload on code changes and provide a debugger.
    # For production environments, set debug=False and use a production-ready WSGI server (e.g., Gunicorn, uWSGI).
    app.run(debug=True, host='0.0.0.0', port=5000)

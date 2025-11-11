from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# In a real application, users would be stored in a database.
# For demonstration, we'll use a simple dictionary.
# Passwords here are hashed for security even in this mock setup.
mock_users = {
    "user@example.com": {
        "name": "Test User",
        "password_hash": generate_password_hash("password123"),
        "email": "user@example.com"
    },
    "admin@example.com": {
        "name": "Admin",
        "password_hash": generate_password_hash("adminpass"),
        "email": "admin@example.com"
    }
}

@app.route('/')
def index():
    """Serves the login page."""
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    """Handles login requests."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid JSON"}), 400

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not all([name, email, password]):
            return jsonify({"message": "Missing name, email, or password"}), 400

        # In a real app, 'name' might be used for registration or just display after login.
        # For login, email is the primary identifier.
        user = mock_users.get(email)

        if user and check_password_hash(user['password_hash'], password):
            # Successfully logged in. In a real app, a session token would be issued here.
            return jsonify({"message": "Login successful!", "user": {"name": user['name'], "email": user['email']}}), 200
        else:
            # User not found or password incorrect
            return jsonify({"message": "Invalid email or password"}), 401

    except Exception as e:
        # Log the exception for debugging in a real application
        app.logger.error(f"Login error: {e}")
        return jsonify({"message": "An internal server error occurred"}), 500

if __name__ == '__main__':
    # Use a secure secret key in production
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_super_secret_key_for_dev_only')
    app.run(debug=True, port=5000)

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# --- Chatbot Logic ---
# A simple rule-based chatbot for demonstration purposes
chatbot_rules = {
    "hi": "Hello there! How can I assist you today?",
    "hello": "Hi! What can I do for you?",
    "how are you": "I'm a bot, so I don't have feelings, but I'm ready to help!",
    "what is your purpose": "I'm here to assist you with information and tasks within this project.",
    "help": "Sure, I can help. What do you need assistance with?",
    "report an issue": "Please use the 'Report an Issue' section to submit your concerns.",
    "thank you": "You're welcome!",
    "bye": "Goodbye! Have a great day!",
    "default": "I'm not sure how to respond to that. Can you please rephrase or ask something else?"
}

def get_chatbot_response(message):
    """Generates a response based on predefined chatbot rules."""
    message = message.lower().strip()
    for keyword, response in chatbot_rules.items():
        if keyword in message:
            return response
    return chatbot_rules["default"]

# --- Report Section Logic ---
REPORTS_FILE = 'reports.json'
ADMIN_EMAIL = 'admin@example.com' # Placeholder: In a real app, configure actual admin email here

def save_report(subject, description):
    """Saves the issue report to a JSON file and simulates sending to admin."""
    report_data = {
        "id": str(datetime.now().timestamp()), # Unique ID based on timestamp
        "timestamp": datetime.now().isoformat(),
        "subject": subject,
        "description": description,
        "status": "pending" # Initial status
    }

    reports = []
    if os.path.exists(REPORTS_FILE):
        try:
            with open(REPORTS_FILE, 'r') as f:
                reports = json.load(f)
        except json.JSONDecodeError:
            app.logger.warning(f"Could not decode {REPORTS_FILE}. Initializing with an empty reports list.")
            reports = [] # If file is corrupted, start fresh
        except IOError as e:
            app.logger.error(f"Error reading {REPORTS_FILE}: {e}")
            return False, f"Failed to read existing reports: {e}"

    reports.append(report_data)

    try:
        with open(REPORTS_FILE, 'w') as f:
            json.dump(reports, f, indent=4) # Save with pretty-print indentation
        app.logger.info(f"Report saved: {report_data}")
        # In a production application, you would integrate an email sending service here
        # e.g., using Flask-Mail or a direct SMTP library.
        app.logger.info(f"Simulating email notification to admin at {ADMIN_EMAIL} for report: '{subject}'")
        return True, "Report submitted successfully. The admin has been notified."
    except IOError as e:
        app.logger.error(f"Error writing to {REPORTS_FILE}: {e}")
        return False, f"Failed to save report: {e}"

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main application page with chatbot and report sections."""
    return render_template('index.html')

@app.route('/chatbot', methods=['POST'])
def chatbot_api():
    """API endpoint for handling chatbot messages."""
    try:
        data = request.get_json()
        user_message = data.get('message')

        if not user_message:
            return jsonify({"error": "Message content is required"}), 400

        bot_response = get_chatbot_response(user_message)
        return jsonify({"response": bot_response}), 200
    except Exception as e:
        app.logger.error(f"Chatbot API error: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/report', methods=['POST'])
def report_issue():
    """API endpoint for submitting issue reports."""
    try:
        data = request.get_json()
        subject = data.get('subject')
        description = data.get('description')

        if not subject or not description:
            return jsonify({"error": "Subject and description are required"}), 400

        success, message = save_report(subject, description)
        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        app.logger.error(f"Report API error: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

if __name__ == '__main__':
    # Initialize reports.json if it doesn't exist to prevent errors on first run
    if not os.path.exists(REPORTS_FILE):
        try:
            with open(REPORTS_FILE, 'w') as f:
                json.dump([], f) # Initialize with an empty list
        except IOError as e:
            app.logger.error(f"Could not create {REPORTS_FILE}: {e}")
            # If the file cannot be created, the reporting functionality might fail.

    app.run(debug=True) # Set debug=False in production for security and performance

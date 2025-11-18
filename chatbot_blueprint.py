from flask import Blueprint, render_template, request, jsonify, current_app
import os
import json
from datetime import datetime

chatbot_bp = Blueprint('chatbot_bp', __name__, template_folder='templates', static_folder='static')

# --- Chatbot Logic ---
chatbot_rules = {
    "hi": "Hello there! How can I assist you today?",
    "hello": "Hi! What can I do for you?",
    "how are you": "I'm a bot, so I don't have feelings, but I'm ready to help!",
    "what is your purpose": "I'm here to answer necessary questions related to SA Enterprises, our company.",
    "company info": "SA Enterprises is an e-commerce platform offering a wide range of products. Our goal is to provide a seamless shopping experience for our customers.",
    "contact": "You can reach us via email at abc@gmail.com or call us at 00000000000. These details are also in the footer of our main pages.",
    "products": "You can browse all our products on the 'Products' page, accessible from the navigation bar.",
    "help": "Sure, I can help. What do you need assistance with?",
    "report an issue": "Please use the 'Report an Issue' form on this page to submit your concerns.",
    "thank you": "You're welcome!",
    "bye": "Goodbye! Have a great day!",
    "default": "I'm not sure how to respond to that. Can you please rephrase or ask something else? For company info, try 'company info' or 'contact'."
}

def get_chatbot_response(message):
    """Generates a response based on predefined chatbot rules."""
    message = message.lower().strip()
    for keyword, response in chatbot_rules.items():
        if keyword in message:
            return response
    return chatbot_rules["default"]

# --- Report Section Logic ---
REPORTS_FILE = 'reports.json' # This file will be in the project root if path not specified.
                              # Consider moving to a data/ directory or using a proper database.

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
    # Use app.root_path to ensure reports.json is stored consistently
    reports_file_path = os.path.join(current_app.root_path, REPORTS_FILE)

    if os.path.exists(reports_file_path):
        try:
            with open(reports_file_path, 'r') as f:
                reports = json.load(f)
        except json.JSONDecodeError:
            current_app.logger.warning(f"Could not decode {reports_file_path}. Initializing with an empty reports list.")
            reports = [] # If file is corrupted, start fresh
        except IOError as e:
            current_app.logger.error(f"Error reading {reports_file_path}: {e}")
            return False, f"Failed to read existing reports: {e}"

    reports.append(report_data)

    try:
        with open(reports_file_path, 'w') as f:
            json.dump(reports, f, indent=4) # Save with pretty-print indentation
        current_app.logger.info(f"Report saved: {report_data}")
        # In a production application, you would integrate an email sending service here
        # e.g., using Flask-Mail or a direct SMTP library.
        # Get admin email from app config
        admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@example.com')
        current_app.logger.info(f"Simulating email notification to admin at {admin_email} for report: '{subject}'")
        return True, "Report submitted successfully. The admin has been notified."
    except IOError as e:
        current_app.logger.error(f"Error writing to {reports_file_path}: {e}")
        return False, f"Failed to save report: {e}"

# --- Flask Routes for Chatbot Blueprint ---

@chatbot_bp.route('/company-chatbot')
def company_chatbot_page():
    """Renders the standalone chatbot and report page."""
    # Ensure REPORTS_FILE is initialized
    reports_file_path = os.path.join(current_app.root_path, REPORTS_FILE)
    if not os.path.exists(reports_file_path):
        try:
            with open(reports_file_path, 'w') as f:
                json.dump([], f)
        except IOError as e:
            current_app.logger.error(f"Could not create {reports_file_path}: {e}")
    
    return render_template('company_chatbot.html')

@chatbot_bp.route('/company-chatbot/api/message', methods=['POST'])
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
        current_app.logger.error(f"Chatbot API error: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@chatbot_bp.route('/company-chatbot/api/report', methods=['POST'])
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
        current_app.logger.error(f"Report API error: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

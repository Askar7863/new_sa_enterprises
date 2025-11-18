# SA Enterprises E-commerce Website

This repository contains the codebase for SA Enterprises, a fully functional e-commerce platform built with Flask. It features user authentication, product browsing, shopping cart, checkout process, order management, and an admin panel for managing products and orders.

## Project Description
This project has been transformed into a modern, user-friendly e-commerce website named SA Enterprises. It boasts an attractive user interface designed to enhance the shopping experience. Key functionalities include:
- User registration and login
- Secure shopping cart and checkout
- Product listing and detailed views
- User order history
- Admin dashboard for product and order management
- Integrated reporting mechanism (via Contact Us page)
- Display of essential contact information.

## Contact Information
Email: abcd@gmail.com
Phone: 000000000000

## Setup and Usage

### Prerequisites
- Python 3.x
- pip (Python package installer)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install Flask Flask-SQLAlchemy Flask-WTF Flask-Login Werkzeug
    ```
    (Note: Additional dependencies might be needed if not specified, e.g., Bootstrap-Flask for some forms, but current templates use raw forms.)

### Database Initialization (First Time Setup)
Before running the application for the first time, you need to initialize the database:
```bash
python -c "from app import create_app, db; app = create_app(); with app.app_context(): db.create_all()"
```

### Running the Application
```bash
export FLASK_APP=app.py
export FLASK_ENV=development # For development, use 'production' for deployment
flask run
```
Access the application at `http://127.0.0.1:5000/` in your web browser.

## TODO
- Implement robust payment gateway integration (currently simulated).
- Enhance search and filtering capabilities.
- Add user profile management.
- Implement product reviews and ratings.
- Improve error handling and logging.
- Add comprehensive unit and integration tests.

**Generated:** 2025-11-12 12:50:55

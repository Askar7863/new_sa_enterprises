import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here_for_dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ecommerce.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'abcd@gmail.com' # Updated admin email
    SHOP_NAME = "SA Enterprises" # Added shop name
    CONTACT_EMAIL = "abcd@gmail.com" # Added contact email
    CONTACT_PHONE = "000000000000" # Added contact phone number
    FLASK_VERSION = "2.3.2" # Example, update if specific version is known

import os
import json
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# Import forms and models
from forms import RegistrationForm, LoginForm, ProductForm, CheckoutForm
from models import db, User, Product, CartItem, Order, OrderItem
from config import Config

# --- Chatbot Logic (moved from old app.py) ---
chatbot_rules = {
    "hi": "Hello there! How can I assist you today at SA Enterprises?",
    "hello": "Hi! What can I do for you at SA Enterprises?",
    "how are you": "I'm a bot, so I don't have feelings, but I'm ready to help you with SA Enterprises!",
    "what is your purpose": "I'm here to assist you with information and tasks related to SA Enterprises e-commerce website.",
    "help": "Sure, I can help. What do you need assistance with regarding SA Enterprises?",
    "report an issue": "Please use the 'Report an Issue' form below to submit your concerns to SA Enterprises support.",
    "thank you": "You're welcome! Happy to help at SA Enterprises!",
    "bye": "Goodbye! Have a great day shopping with SA Enterprises!",
    "default": "I'm not sure how to respond to that. Can you please rephrase or ask something else? For specific questions about SA Enterprises products or orders, please try to be more direct."
}

def get_chatbot_response(message):
    message = message.lower().strip()
    for keyword, response in chatbot_rules.items():
        if keyword in message:
            return response
    return chatbot_rules["default"]

# --- Report Section Logic (moved from old app.py) ---
REPORTS_FILE = 'reports.json' # This file path is relative to the app.py location
# Note: For a production app, this should be an absolute path or configured via app.instance_path
# and actual email sending should be integrated, not just logging.

def save_report(subject, description, user_email=None):
    report_data = {
        "id": str(datetime.now().timestamp()),
        "timestamp": datetime.now().isoformat(),
        "subject": subject,
        "description": description,
        "status": "pending",
        "reported_by_email": user_email if user_email else "anonymous"
    }

    reports = []
    # Ensure reports.json is created if it doesn't exist
    if not os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, 'w') as f:
            json.dump([], f)

    try:
        with open(REPORTS_FILE, 'r') as f:
            reports = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not decode {REPORTS_FILE}. Initializing with an empty reports list.")
        reports = []
    except IOError as e:
        print(f"Error reading {REPORTS_FILE}: {e}")
        return False, f"Failed to read existing reports: {e}"

    reports.append(report_data)

    try:
        with open(REPORTS_FILE, 'w') as f:
            json.dump(reports, f, indent=4)
        print(f"Report saved: {report_data}")
        # Simulate email notification
        print(f"Simulating email notification to admin at {Config.ADMIN_EMAIL} for report: '{subject}' from {report_data['reported_by_email']}")
        return True, "Report submitted successfully. The admin has been notified."
    except IOError as e:
        print(f"Error writing to {REPORTS_FILE}: {e}")
        return False, f"Failed to save report: {e}"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login' # Redirect to login page if unauthenticated

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Decorators ---
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.is_admin:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function

    # --- Error Handlers ---
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html', title='Forbidden', shop_name=Config.SHOP_NAME), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html', title='Page Not Found', shop_name=Config.SHOP_NAME), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/generic.html', title='Internal Server Error', code=500, name='Internal Server Error', description='Something went wrong on our side.', shop_name=Config.SHOP_NAME), 500


    # --- General Routes ---
    @app.route('/')
    def index():
        # Display some featured products or a welcome message
        featured_products = Product.query.order_by(db.func.random()).limit(3).all()
        return render_template('index.html', title='Welcome', featured_products=featured_products, shop_name=Config.SHOP_NAME)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data)
            user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', title='Register', form=form, shop_name=Config.SHOP_NAME)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page or url_for('index'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        return render_template('login.html', title='Login', form=form, shop_name=Config.SHOP_NAME)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/products')
    def products():
        all_products = Product.query.all()
        return render_template('products.html', title='Products', products=all_products, shop_name=Config.SHOP_NAME)

    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        return render_template('product_detail.html', title=product.name, product=product, shop_name=Config.SHOP_NAME)

    @app.route('/add_to_cart/<int:product_id>', methods=['POST'])
    @login_required
    def add_to_cart(product_id):
        product = Product.query.get_or_404(product_id)
        quantity = int(request.form.get('quantity', 1))

        if quantity <= 0:
            flash('Quantity must be at least 1.', 'danger')
            return redirect(url_for('product_detail', product_id=product.id))

        if quantity > product.stock:
            flash(f'Cannot add {quantity} of {product.name}. Only {product.stock} available.', 'danger')
            return redirect(url_for('product_detail', product_id=product.id))

        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()

        if cart_item:
            if cart_item.quantity + quantity > product.stock:
                flash(f'Adding {quantity} more of {product.name} would exceed available stock ({product.stock}). You currently have {cart_item.quantity} in cart.', 'danger')
                return redirect(url_for('product_detail', product_id=product.id))
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=quantity)
            db.session.add(cart_item)
        db.session.commit()
        flash(f'{quantity} x {product.name} added to cart!', 'success')
        return redirect(url_for('cart'))

    @app.route('/cart')
    @login_required
    def cart():
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        total_price = sum(item.quantity * item.product.price for item in cart_items)
        return render_template('cart.html', title='Shopping Cart', cart_items=cart_items, total_price=total_price, shop_name=Config.SHOP_NAME)

    @app.route('/update_cart/<int:product_id>', methods=['POST'])
    @login_required
    def update_cart(product_id):
        product = Product.query.get_or_404(product_id)
        new_quantity = int(request.form.get('quantity', 1))

        if new_quantity <= 0:
            flash('Quantity must be at least 1. To remove, use the trash icon.', 'danger')
            return redirect(url_for('cart'))

        if new_quantity > product.stock:
            flash(f'Cannot update to {new_quantity} of {product.name}. Only {product.stock} available.', 'danger')
            return redirect(url_for('cart'))

        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()
        if cart_item:
            cart_item.quantity = new_quantity
            db.session.commit()
            flash(f'Cart updated for {product.name}.', 'success')
        else:
            flash('Item not found in your cart.', 'warning')
        return redirect(url_for('cart'))

    @app.route('/remove_from_cart/<int:product_id>')
    @login_required
    def remove_from_cart(product_id):
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first_or_404()
        db.session.delete(cart_item)
        db.session.commit()
        flash(f'{cart_item.product.name} removed from cart.', 'info')
        return redirect(url_for('cart'))

    @app.route('/checkout', methods=['GET', 'POST'])
    @login_required
    def checkout():
        form = CheckoutForm()
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            flash('Your cart is empty. Please add items before checking out.', 'warning')
            return redirect(url_for('products'))

        total_amount = sum(item.quantity * item.product.price for item in cart_items)

        if form.validate_on_submit():
            # Construct shipping address
            shipping_address = (
                f"{form.full_name.data}\n"
                f"{form.address_line1.data}\n"
                f"{form.address_line2.data}\n"
                f"{form.city.data}, {form.state.data} {form.zip_code.data}\n"
                f"{form.country.data}"
            )

            # Create new order
            new_order = Order(
                user_id=current_user.id,
                total_amount=total_amount,
                shipping_address=shipping_address,
                status='Pending' # Payment is simulated, so set to Pending
            )
            db.session.add(new_order)
            db.session.flush() # To get the new_order.id before committing

            # Move cart items to order items and update product stock
            for item in cart_items:
                if item.quantity > item.product.stock:
                    # This scenario should ideally be prevented earlier (e.g., in cart/update_cart)
                    # For safety, abort checkout or rollback.
                    db.session.rollback()
                    flash(f'Not enough stock for {item.product.name}. Only {item.product.stock} available.', 'danger')
                    return redirect(url_for('cart'))

                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=item.product.id,
                    quantity=item.quantity,
                    price=item.product.price
                )
                db.session.add(order_item)
                item.product.stock -= item.quantity # Deduct from stock
                db.session.delete(item) # Remove from cart

            db.session.commit()
            flash(f'Order #{new_order.id} placed successfully!', 'success')
            return redirect(url_for('orders'))

        return render_template('checkout.html', title='Checkout', form=form, cart_items=cart_items, total_amount=total_amount, shop_name=Config.SHOP_NAME)

    @app.route('/orders')
    @login_required
    def orders():
        user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
        return render_template('orders.html', title='My Orders', orders=user_orders, shop_name=Config.SHOP_NAME)

    # --- Contact Page with Chatbot and Reporting ---
    @app.route('/contact')
    def contact():
        return render_template('contact.html', title='Contact Us', shop_name=Config.SHOP_NAME,
                               contact_email=Config.CONTACT_EMAIL, contact_phone=Config.CONTACT_PHONE)

    @app.route('/api/chatbot', methods=['POST'])
    def chatbot_api():
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

    @app.route('/api/report', methods=['POST'])
    def report_issue_api():
        try:
            data = request.get_json()
            subject = data.get('subject')
            description = data.get('description')
            user_email = current_user.email if current_user.is_authenticated else None

            if not subject or not description:
                return jsonify({"error": "Subject and description are required"}), 400

            success, message = save_report(subject, description, user_email)
            if success:
                return jsonify({"message": message}), 200
            else:
                return jsonify({"error": message}), 500
        except Exception as e:
            app.logger.error(f"Report API error: {e}")
            return jsonify({"error": "An internal server error occurred"}), 500


    # --- Admin Routes ---
    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        total_users = User.query.count()
        total_products = Product.query.count()
        total_orders = Order.query.count()
        latest_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
        return render_template('admin/dashboard.html', title='Admin Dashboard',
                               total_users=total_users, total_products=total_products,
                               total_orders=total_orders, latest_orders=latest_orders,
                               config=app.config, shop_name=Config.SHOP_NAME)

    @app.route('/admin/products')
    @admin_required
    def admin_products():
        all_products = Product.query.all()
        return render_template('admin/products.html', title='Manage Products', products=all_products, shop_name=Config.SHOP_NAME)

    @app.route('/admin/product/new', methods=['GET', 'POST'])
    @admin_required
    def admin_new_product():
        form = ProductForm()
        if form.validate_on_submit():
            product = Product(
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                image_url=form.image_url.data,
                stock=form.stock.data
            )
            db.session.add(product)
            db.session.commit()
            flash('Product created successfully!', 'success')
            return redirect(url_for('admin_products'))
        return render_template('admin/product_form.html', title='Add New Product', form=form, shop_name=Config.SHOP_NAME)

    @app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_product(product_id):
        product = Product.query.get_or_404(product_id)
        form = ProductForm(obj=product) # Populate form with existing product data
        if form.validate_on_submit():
            product.name = form.name.data
            product.description = form.description.data
            product.price = form.price.data
            product.image_url = form.image_url.data
            product.stock = form.stock.data
            product.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))
        return render_template('admin/product_form.html', title='Edit Product', form=form, product_id=product.id, shop_name=Config.SHOP_NAME)

    @app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
    @admin_required
    def admin_delete_product(product_id):
        product = Product.query.get_or_404(product_id)
        # Check for associated cart items or order items before deleting
        if CartItem.query.filter_by(product_id=product.id).first() or OrderItem.query.filter_by(product_id=product.id).first():
            flash('Cannot delete product: It is associated with existing carts or orders.', 'danger')
        else:
            db.session.delete(product)
            db.session.commit()
            flash('Product deleted successfully!', 'success')
        return redirect(url_for('admin_products'))

    @app.route('/admin/orders')
    @admin_required
    def admin_orders():
        all_orders = Order.query.order_by(Order.order_date.desc()).all()
        return render_template('admin/orders.html', title='Manage Orders', orders=all_orders, shop_name=Config.SHOP_NAME)

    @app.route('/admin/order/<int:order_id>')
    @admin_required
    def admin_order_detail(order_id):
        order = Order.query.get_or_404(order_id)
        return render_template('admin/order_detail.html', title=f'Order #{order.id} Details', order=order, shop_name=Config.SHOP_NAME)

    @app.route('/admin/order/<int:order_id>/status', methods=['POST'])
    @admin_required
    def admin_update_order_status(order_id):
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        valid_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']

        if new_status and new_status in valid_statuses:
            order.status = new_status
            db.session.commit()
            flash(f'Order #{order.id} status updated to {new_status}.', 'success')
        else:
            flash('Invalid status provided.', 'danger')
        return redirect(url_for('admin_order_detail', order_id=order.id))

    # Initial setup for reports.json
    @app.before_first_request
    def create_reports_file():
        if not os.path.exists(REPORTS_FILE):
            try:
                with open(REPORTS_FILE, 'w') as f:
                    json.dump([], f)
                app.logger.info(f"{REPORTS_FILE} created successfully.")
            except IOError as e:
                app.logger.error(f"Could not create {REPORTS_FILE}: {e}")

    return app

if __name__ == '__main__':
    app = create_app()
    # To create database tables, run `python -c "from app import create_app, db; app = create_app(); with app.app_context(): db.create_all()"`
    # or uncomment db.create_all() for development, but remove in production
    # with app.app_context():
    #    db.create_all()
    #    # Example: Add an admin user if not exists
    #    if not User.query.filter_by(email='admin@example.com').first():
    #        admin_user = User(username='admin', email='admin@example.com', is_admin=True)
    #        admin_user.set_password('adminpassword') # CHANGE THIS IN PRODUCTION!
    #        db.session.add(admin_user)
    #        db.session.commit()
    #        print("Admin user 'admin@example.com' created with password 'adminpassword'")
    #    # Example: Add some dummy products if none exist
    #    if not Product.query.first():
    #        p1 = Product(name='Premium Widget', description='A high-quality widget for all your needs.', price=29.99, image_url='https://via.placeholder.com/300x200?text=Premium+Widget', stock=50)
    #        p2 = Product(name='Super Gadget', description='The ultimate gadget to simplify your life.', price=99.50, image_url='https://via.placeholder.com/300x200?text=Super+Gadget', stock=25)
    #        p3 = Product(name='Eco-Friendly Item', description='Sustainable and environmentally conscious product.', price=15.00, image_url='https://via.placeholder.com/300x200?text=Eco+Item', stock=100)
    #        db.session.add_all([p1, p2, p3])
    #        db.session.commit()
    #        print("Dummy products added.")
    app.run(debug=True)

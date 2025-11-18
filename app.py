from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from functools import wraps # For admin_required decorator

from config import Config
from models import db, User, Product, CartItem, Order, OrderItem
from forms import RegistrationForm, LoginForm, ProductForm, CheckoutForm

# Import the new chatbot blueprint
from chatbot_blueprint import chatbot_bp

# --- App Initialization ---
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # The route name for the login page
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Blueprint Registration ---
app.register_blueprint(chatbot_bp)

# --- Error Handlers ---
@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('errors/generic.html', code=500, name="Internal Server Error", description="The server encountered an internal error and was unable to complete your request."), 500


# --- E-commerce Routes ---

@app.route('/')
def index():
    # New e-commerce homepage
    return render_template('index.html', title='Welcome to SA Enterprises')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email or username already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('That email is already registered. Please choose a different one.', 'danger')
        elif User.query.filter_by(username=form.username.data).first():
            flash('That username is taken. Please choose a different one.', 'danger')
        else:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

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
            flash('Logged in successfully!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', title='Products', products=all_products)

@app.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', title=product.name, product=product)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))

    if quantity <= 0:
        flash('Quantity must be at least 1.', 'danger')
        return redirect(url_for('product_detail', product_id=product.id))

    if product.stock < quantity:
        flash(f'Not enough stock for {product.name}. Available: {product.stock}', 'danger')
        return redirect(url_for('product_detail', product_id=product.id))

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if cart_item:
        if product.stock < (cart_item.quantity + quantity):
             flash(f'Adding {quantity} to cart would exceed available stock. Current in cart: {cart_item.quantity}, Available: {product.stock}.', 'danger')
        else:
            cart_item.quantity += quantity
            flash(f'{quantity} more of {product.name} added to cart!', 'success')
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)
        flash(f'{product.name} added to cart!', 'success')
    
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.quantity * item.product.price for item in cart_items)
    return render_template('cart.html', title='Your Cart', cart_items=cart_items, total_price=total_price)

@app.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if not cart_item:
        flash('Item not found in cart.', 'danger')
        return redirect(url_for('cart'))
    
    product = Product.query.get(product_id)
    if not product:
        flash('Product not found.', 'danger')
        db.session.delete(cart_item)
        db.session.commit()
        return redirect(url_for('cart'))

    if quantity <= 0:
        db.session.delete(cart_item)
        db.session.commit()
        flash(f'{product.name} removed from cart.', 'info')
    elif quantity > product.stock:
        flash(f'Cannot set quantity to {quantity} for {product.name}. Only {product.stock} available.', 'danger')
        cart_item.quantity = product.stock # Set to max available
        db.session.commit()
    else:
        cart_item.quantity = quantity
        db.session.commit()
        flash(f'Quantity for {product.name} updated to {quantity}.', 'success')
        
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'success')
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
        shipping_address = f"{form.full_name.data}\n{form.address_line1.data}\n{form.address_line2.data}\n{form.city.data}, {form.state.data} {form.zip_code.data}\n{form.country.data}"
        
        # Create Order
        new_order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            shipping_address=shipping_address,
            status='Pending' # Simulated payment, so starts as Pending
        )
        db.session.add(new_order)
        db.session.flush() # To get new_order.id before committing

        # Add Order Items and update product stock
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product.id,
                quantity=item.quantity,
                price=item.product.price
            )
            item.product.stock -= item.quantity # Deduct stock
            db.session.add(order_item)
            db.session.delete(item) # Clear cart item
        
        db.session.commit()
        flash('Your order has been placed successfully!', 'success')
        return redirect(url_for('orders'))

    return render_template('checkout.html', title='Checkout', form=form, cart_items=cart_items, total_amount=total_amount)

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', title='My Orders', orders=user_orders)

# --- Admin Routes ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    latest_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    # Passing app.config to templates for system info
    config_display = {
        'FLASK_VERSION': '2.x.x (placeholder)', # Actual version not easily available this way
        'SQLALCHEMY_DATABASE_URI': app.config['SQLALCHEMY_DATABASE_URI'],
        'ADMIN_EMAIL': app.config['ADMIN_EMAIL']
    }
    return render_template('admin/dashboard.html', title='Admin Dashboard', 
                           total_users=total_users, total_products=total_products, 
                           total_orders=total_orders, latest_orders=latest_orders,
                           config=config_display)

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', title='Manage Products', products=all_products)

@app.route('/admin/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_new_product():
    form = ProductForm()
    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_url=form.image_url.data,
            stock=form.stock.data
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', title='Add New Product', form=form, product_id=None)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.image_url = form.image_url.data
        product.stock = form.stock.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    elif request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.price.data = product.price
        form.image_url.data = product.image_url
        form.stock.data = product.stock
    return render_template('admin/product_form.html', title='Edit Product', form=form, product_id=product.id)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    all_orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', title='Manage Orders', orders=all_orders)

@app.route('/admin/orders/<int:order_id>')
@login_required
@admin_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', title=f'Order #{order.id} Details', order=order)

@app.route('/admin/orders/<int:order_id>/update_status', methods=['POST'])
@login_required
@admin_required
def admin_update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status in ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status}.', 'success')
    else:
        flash('Invalid status provided.', 'danger')
    return redirect(url_for('admin_order_detail', order_id=order.id))


if __name__ == '__main__':
    # Initial setup for database creation - should ideally be done via migrations
    with app.app_context():
        db.create_all()
        # Optional: Add some dummy data if db is empty for testing
        if User.query.count() == 0:
            admin_user = User(username='admin', email='admin@example.com', is_admin=True)
            admin_user.set_password('password')
            db.session.add(admin_user)
            user1 = User(username='testuser', email='user@example.com', is_admin=False)
            user1.set_password('password')
            db.session.add(user1)
            db.session.commit()
            print("Added default admin and test user.")
        
        if Product.query.count() == 0:
            dummy_products = [
                Product(name="Smartphone X", description="Latest model with advanced features.", price=699.99, image_url="https://via.placeholder.com/150/0000FF/FFFFFF?text=SmartphoneX", stock=50),
                Product(name="Laptop Pro", description="High-performance laptop for professionals.", price=1200.00, image_url="https://via.placeholder.com/150/FF0000/FFFFFF?text=LaptopPro", stock=30),
                Product(name="Wireless Earbuds", description="Premium sound quality with noise cancellation.", price=99.50, image_url="https://via.placeholder.com/150/00FF00/FFFFFF?text=Earbuds", stock=100),
                Product(name="Smartwatch Z", description="Track your fitness and stay connected.", price=199.00, image_url="https://via.placeholder.com/150/FFFF00/000000?text=SmartwatchZ", stock=75)
            ]
            db.session.add_all(dummy_products)
            db.session.commit()
            print("Added dummy products.")

    app.run(debug=True)

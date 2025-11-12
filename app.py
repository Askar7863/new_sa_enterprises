from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException
import os

from config import Config
from models import db, User, Product, CartItem, Order, OrderItem
from forms import RegistrationForm, LoginForm, ProductForm, CheckoutForm

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_first_request
    def create_tables_and_admin():
        try:
            db.create_all()
            # Create an admin user if not exists
            if not User.query.filter_by(email=app.config['ADMIN_EMAIL']).first():
                admin_user = User(username='admin', email=app.config['ADMIN_EMAIL'], is_admin=True)
                admin_user.set_password('adminpassword') # Consider using environment variable for prod
                db.session.add(admin_user)
                db.session.commit()
                print(f"Admin user '{admin_user.username}' created.")

            # Add some sample products if none exist
            if not Product.query.first():
                sample_products = [
                    Product(name='Wireless Headphones', description='High-quality sound with noise cancellation.', price=79.99, image_url='https://via.placeholder.com/150/0000FF/FFFFFF?text=Headphones', stock=50),
                    Product(name='Smartwatch', description='Track your fitness and receive notifications.', price=129.99, image_url='https://via.placeholder.com/150/FF0000/FFFFFF?text=Smartwatch', stock=30),
                    Product(name='Gaming Mouse', description='Precision gaming mouse with customizable RGB lighting.', price=49.99, image_url='https://via.placeholder.com/150/00FF00/FFFFFF?text=Mouse', stock=100),
                    Product(name='USB-C Hub', description='Multiport adapter for modern laptops.', price=29.99, image_url='https://via.placeholder.com/150/FFFF00/000000?text=USBHub', stock=75),
                    Product(name='Mechanical Keyboard', description='Tactile and clicky keys for an excellent typing experience.', price=99.99, image_url='https://via.placeholder.com/150/FF00FF/FFFFFF?text=Keyboard', stock=40)
                ]
                db.session.add_all(sample_products)
                db.session.commit()
                print("Sample products added.")

        except Exception as e:
            app.logger.error(f"Error during database initialization or admin creation: {e}")

    # Custom decorator for admin required routes
    def admin_required(f):
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_admin:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function

    # Error Handlers
    @app.errorhandler(401)
    def unauthorized_error(error):
        flash('You need to log in to access this page.', 'warning')
        return redirect(url_for('login', next=request.path))

    @app.errorhandler(403)
    def forbidden_error(error):
        flash('You do not have permission to access this resource.', 'danger')
        return render_template('errors/403.html', title='Forbidden'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html', title='Page Not Found'), 404

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return render_template('errors/generic.html', code=e.code, name=e.name, description=e.description), e.code
        return render_template('errors/generic.html', code=500, name='Internal Server Error', description='Something went wrong.'), 500

    @app.errorhandler(Exception)
    def handle_all_exceptions(e):
        app.logger.error(f"Unhandled Exception: {e}")
        return render_template('errors/generic.html', code=500, name='Internal Server Error', description='An unexpected error occurred.'), 500


    # --- Routes --- #

    @app.route('/')
    def index():
        products = Product.query.order_by(Product.created_at.desc()).limit(4).all() # Show 4 latest products
        return render_template('index.html', products=products)

    @app.route('/products')
    def products():
        all_products = Product.query.order_by(Product.name).all()
        return render_template('products.html', products=all_products)

    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        return render_template('product_detail.html', product=product)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = form.password.data # password hashing is handled by User.set_password
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(hashed_password)
            try:
                db.session.add(user)
                db.session.commit()
                flash('Your account has been created! You are now able to log in', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred during registration: {e}', 'danger')
                app.logger.error(f"Registration error: {e}")
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=True)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                return redirect(next_page or url_for('index'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/cart/add/<int:product_id>', methods=['POST'])
    @login_required
    def add_to_cart(product_id):
        product = Product.query.get_or_404(product_id)
        quantity = int(request.form.get('quantity', 1))

        if quantity <= 0:
            flash('Quantity must be at least 1.', 'warning')
            return redirect(url_for('product_detail', product_id=product.id))

        if product.stock < quantity:
            flash(f'Not enough stock for {product.name}. Available: {product.stock}', 'warning')
            return redirect(url_for('product_detail', product_id=product.id))

        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        try:
            if cart_item:
                # Check stock before increasing
                if product.stock < cart_item.quantity + quantity:
                    flash(f'Adding {quantity} more would exceed available stock for {product.name}. Available: {product.stock}', 'warning')
                    return redirect(url_for('product_detail', product_id=product.id))
                cart_item.quantity += quantity
            else:
                cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
                db.session.add(cart_item)
            db.session.commit()
            flash(f'{quantity} x {product.name} added to cart!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding {product.name} to cart: {e}', 'danger')
            app.logger.error(f"Cart add error: {e}")
        return redirect(url_for('cart'))

    @app.route('/cart/update/<int:product_id>', methods=['POST'])
    @login_required
    def update_cart(product_id):
        new_quantity = int(request.form.get('quantity', 1))
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first_or_404()
        product = Product.query.get_or_404(product_id)

        if new_quantity <= 0:
            try:
                db.session.delete(cart_item)
                db.session.commit()
                flash(f'{product.name} removed from cart.', 'info')
            except Exception as e:
                db.session.rollback()
                flash(f'Error removing item: {e}', 'danger')
                app.logger.error(f"Cart remove error: {e}")
            return redirect(url_for('cart'))

        if product.stock < new_quantity:
            flash(f'Cannot update quantity to {new_quantity}. Only {product.stock} available for {product.name}.', 'warning')
            return redirect(url_for('cart'))

        try:
            cart_item.quantity = new_quantity
            db.session.commit()
            flash(f'Quantity for {product.name} updated to {new_quantity}.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating quantity: {e}', 'danger')
            app.logger.error(f"Cart update error: {e}")
        return redirect(url_for('cart'))

    @app.route('/cart/remove/<int:product_id>')
    @login_required
    def remove_from_cart(product_id):
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first_or_404()
        product_name = cart_item.product.name # Get name before deleting item
        try:
            db.session.delete(cart_item)
            db.session.commit()
            flash(f'{product_name} removed from cart.', 'info')
        except Exception as e:
            db.session.rollback()
            flash(f'Error removing {product_name} from cart: {e}', 'danger')
            app.logger.error(f"Cart remove error: {e}")
        return redirect(url_for('cart'))

    @app.route('/cart')
    @login_required
    def cart():
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        total_price = sum(item.quantity * item.product.price for item in cart_items)
        return render_template('cart.html', cart_items=cart_items, total_price=total_price)

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

            try:
                new_order = Order(
                    user_id=current_user.id,
                    total_amount=total_amount,
                    shipping_address=shipping_address,
                    status='Pending'
                )
                db.session.add(new_order)
                db.session.flush() # To get the order.id before commit

                for item in cart_items:
                    # Check product stock again at the moment of order placement
                    product = Product.query.get(item.product_id)
                    if product.stock < item.quantity:
                        db.session.rollback()
                        flash(f'Not enough stock for {product.name}. Available: {product.stock}. Please adjust your cart.', 'danger')
                        return redirect(url_for('cart'))

                    order_item = OrderItem(
                        order_id=new_order.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        price=item.product.price
                    )
                    db.session.add(order_item)
                    product.stock -= item.quantity # Deduct stock

                # Clear the cart after successful order creation
                for item in cart_items:
                    db.session.delete(item)

                db.session.commit()
                flash('Your order has been placed successfully!', 'success')
                return redirect(url_for('orders'))
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred during checkout: {e}', 'danger')
                app.logger.error(f"Checkout error: {e}")

        return render_template('checkout.html', form=form, cart_items=cart_items, total_amount=total_amount)

    @app.route('/orders')
    @login_required
    def orders():
        user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
        return render_template('orders.html', orders=user_orders)

    # --- Admin Routes --- #

    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        total_users = User.query.count()
        total_products = Product.query.count()
        total_orders = Order.query.count()
        latest_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
        return render_template('admin/dashboard.html', 
                               total_users=total_users, 
                               total_products=total_products, 
                               total_orders=total_orders,
                               latest_orders=latest_orders)

    @app.route('/admin/products')
    @admin_required
    def admin_products():
        products = Product.query.order_by(Product.name).all()
        return render_template('admin/products.html', products=products)

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
            try:
                db.session.add(product)
                db.session.commit()
                flash('Product created successfully!', 'success')
                return redirect(url_for('admin_products'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating product: {e}', 'danger')
                app.logger.error(f"Product creation error: {e}")
        return render_template('admin/product_form.html', form=form, title='Add New Product')

    @app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
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
            try:
                db.session.commit()
                flash('Product updated successfully!', 'success')
                return redirect(url_for('admin_products'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating product: {e}', 'danger')
                app.logger.error(f"Product update error: {e}")
        elif request.method == 'GET':
            form.name.data = product.name
            form.description.data = product.description
            form.price.data = product.price
            form.image_url.data = product.image_url
            form.stock.data = product.stock
        return render_template('admin/product_form.html', form=form, title='Edit Product', product_id=product.id)

    @app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
    @admin_required
    def admin_delete_product(product_id):
        product = Product.query.get_or_404(product_id)
        try:
            db.session.delete(product)
            db.session.commit()
            flash('Product deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting product: {e}', 'danger')
            app.logger.error(f"Product deletion error: {e}")
        return redirect(url_for('admin_products'))

    @app.route('/admin/orders')
    @admin_required
    def admin_orders():
        all_orders = Order.query.order_by(Order.order_date.desc()).all()
        return render_template('admin/orders.html', orders=all_orders)

    @app.route('/admin/order/<int:order_id>')
    @admin_required
    def admin_order_detail(order_id):
        order = Order.query.get_or_404(order_id)
        return render_template('admin/order_detail.html', order=order)

    @app.route('/admin/order/update_status/<int:order_id>', methods=['POST'])
    @admin_required
    def admin_update_order_status(order_id):
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        if new_status and new_status in ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']:
            try:
                order.status = new_status
                db.session.commit()
                flash(f'Order {order.id} status updated to {new_status}.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating order status: {e}', 'danger')
                app.logger.error(f"Order status update error: {e}")
        else:
            flash('Invalid status provided.', 'danger')
        return redirect(url_for('admin_order_detail', order_id=order.id))


    return app

if __name__ == '__main__':
    app = create_app()
    # For development, you might want to run with debug=True, but disable in production.
    # Also, use a production-ready WSGI server like Gunicorn in production.
    app.run(debug=True)

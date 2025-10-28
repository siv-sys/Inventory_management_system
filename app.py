import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import random

# ------------------------------------------------------------------------------
# Flask App Configuration
# ------------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'inventory-system-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------

class User(db.Model):
    __tablename__ = 'users'
   
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), default='/static/images/default-avatar.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Product(db.Model):
    __tablename__ = 'products'
   
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Sale(db.Model):
    __tablename__ = 'sales'
   
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    sale_price = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='sales')

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Delivered, Pending, Checkback
    tracking_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
UPLOAD_FOLDER = 'static/uploads/profile_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------------------------------------------------------------
# Database Initialization
# ------------------------------------------------------------------------------

def init_db():
    """Initialize the database on first run."""
    with app.app_context():
        db.create_all()
        
        # Create a default user for testing
        if not User.query.filter_by(email='demo@example.com').first():
            default_user = User(
                name='Demo User',
                email='demo@example.com',
                image_url='/static/images/default-avatar.png'
            )
            default_user.set_password('password123')
            db.session.add(default_user)
            db.session.commit()
            
            # Add sample products for demo
            sample_products = [
                Product(name='MacBook Pro 15"', category='Electronics', price=2499.99, quantity=15, description='High-performance laptop for professionals'),
                Product(name='iMac Pro 2019', category='Electronics', price=4999.99, quantity=8, description='All-in-one desktop computer'),
                Product(name='iPad Pro with Apple Pencil', category='Electronics', price=1299.99, quantity=25, description='Professional tablet with stylus'),
                Product(name='MacBook Pro 13"', category='Electronics', price=1799.99, quantity=20, description='Compact professional laptop'),
                Product(name='iPhone 14 Pro', category='Electronics', price=999.99, quantity=50, description='Latest smartphone with advanced camera'),
                Product(name='AirPods Pro', category='Electronics', price=249.99, quantity=75, description='Wireless noise-cancelling earbuds'),
                Product(name='Apple Watch Series 8', category='Electronics', price=399.99, quantity=30, description='Advanced smartwatch with health tracking'),
                Product(name='Gaming Laptop', category='Electronics', price=1299.99, quantity=8, description='High-performance gaming laptop with RGB keyboard'),
                Product(name='Cotton T-Shirt', category='Clothing', price=24.99, quantity=45, description='Comfortable 100% cotton t-shirt'),
                Product(name='Python Programming Book', category='Books', price=39.99, quantity=25, description='Learn Python programming from scratch'),
            ]
            
            for product in sample_products:
                db.session.add(product)
            
            # Add sample orders
            sample_orders = [
                Order(order_id='#2018078', customer_name='Brentia Hoyas', order_date=datetime(2019, 8, 21), amount=8216.00, status='Delivered', tracking_number='DCRUY'),
                Order(order_id='#2018078', customer_name='Ted Holder', order_date=datetime(2019, 6, 24), amount=5456.00, status='Checkback', tracking_number='JHKKL'),
                Order(order_id='#2018083', customer_name='Share W&C', order_date=datetime(2019, 8, 29), amount=5654.00, status='Delivered', tracking_number='KJKQ'),
                Order(order_id='#2018084', customer_name='Duelal Mask', order_date=datetime(2019, 12, 10), amount=5554.00, status='Pending', tracking_number='BOJKL'),
                Order(order_id='#2018085', customer_name='Earth Mujian', order_date=datetime(2019, 11, 21), amount=5624.00, status='Delivered', tracking_number='WKUX'),
            ]
            
            for order in sample_orders:
                db.session.add(order)
            
            # Add sample sales data
            for product in sample_products[:8]:  # Only add sales for first 8 products
                for i in range(random.randint(5, 15)):
                    sale = Sale(
                        product_id=product.id,
                        quantity_sold=random.randint(1, 3),
                        sale_price=product.price * random.uniform(0.85, 0.95),
                        sale_date=datetime.utcnow() - timedelta(days=random.randint(1, 180))
                    )
                    db.session.add(sale)
            
            db.session.commit()
        
        print("Database initialized successfully!")
        print("Tables created: users, products, sales, orders")

# Create tables if not exist
init_db()

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def get_existing_categories():
    """Get all existing categories from the database"""
    categories = db.session.query(Product.category).distinct().all()
    return [category[0] for category in categories]

def get_dashboard_data():
    """Generate comprehensive dashboard data"""
    # Get all products
    products = Product.query.order_by(Product.created_at.desc()).all()
    
    # Product statistics
    total_products = len(products)
    total_stock = sum(p.quantity for p in products)
    out_of_stock = len([p for p in products if p.quantity == 0])
    
    # Sales data
    sales = Sale.query.all()
    total_orders = len(sales)
    total_revenue = sum(sale.quantity_sold * sale.sale_price for sale in sales)
    
    # Customer count
    total_customers = User.query.count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    # Category distribution
    categories = {}
    for product in products:
        if product.category not in categories:
            categories[product.category] = 0
        categories[product.category] += 1
    
    # Product performance data (based on sales)
    product_performance = []
    top_products = db.session.query(
        Product.name,
        db.func.sum(Sale.quantity_sold).label('total_sold')
    ).join(Sale).group_by(Product.id).order_by(db.func.sum(Sale.quantity_sold).desc()).limit(4).all()
    
    if top_products:
        max_sales = max([p.total_sold for p in top_products]) if top_products else 1
        
        for product in top_products:
            percentage = int((product.total_sold / max_sales) * 100) if max_sales > 0 else 0
            product_performance.append({
                'name': product.name,
                'percentage': percentage
            })
    
    # Fill with default data if not enough products
    default_products = [
        {'name': 'MacBook Pro 15"', 'percentage': 49},
        {'name': 'iMac Pro 2019', 'percentage': 19},
        {'name': 'iPad Pro with Apple Pencil', 'percentage': 29},
        {'name': 'MacBook Pro 13"', 'percentage': 56}
    ]
    
    while len(product_performance) < 4:
        product_performance.append(default_products[len(product_performance)])
    
    # Email statistics
    email_stats = [
        {'type': 'Marketing', 'percentage': 70},
        {'type': 'Promotions', 'percentage': 45},
        {'type': 'Newsletter', 'percentage': 45}
    ]
    
    # Delivery statistics
    delivery_stats = [
        {'status': 'Pending', 'percentage': 23},
        {'status': 'In Transit', 'percentage': 45},
        {'status': 'Delivered', 'percentage': 32}
    ]
    
    # Monthly revenue data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    income_data = [12000, 19000, 15000, 25000, 22000, 30000, 28000, 32000, 30000, 35000, 33000, 38000]
    expense_data = [8000, 12000, 10000, 18000, 15000, 22000, 20000, 25000, 23000, 28000, 26000, 30000]
    
    return {
        'products': products[:5],  # Only send first 5 products for recent activities
        'total_products': total_products,
        'total_stock': total_stock,
        'out_of_stock': out_of_stock,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
        'product_performance': product_performance,
        'email_stats': email_stats,
        'delivery_stats': delivery_stats,
        'categories': categories,
        'months': months,
        'income_data': income_data,
        'expense_data': expense_data
    }

def reset_database():
    """Delete old DB and recreate tables."""
    db_path = os.path.join(os.path.dirname(__file__), 'inventory_new.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Old database deleted.")
   
    with app.app_context():
        db.create_all()
        print("New database created with updated schema.")
   
    print("Database reset complete!")

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------------- Authentication -------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
       
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_image'] = user.image_url
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
   
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
       
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered! Please use a different email.', 'error')
            return render_template('register.html')
       
        new_user = User(name=name, email=email)
        new_user.set_password(password)
       
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
   
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# ------------------------- Profile Image Upload --------------------------------

@app.route('/upload-profile-image', methods=['POST'])
def upload_profile_image():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    if 'profileImage' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    file = request.files['profileImage']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        # Check file size
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0, 0)  # Reset file pointer
        
        if file_length > MAX_FILE_SIZE:
            return jsonify({'success': False, 'message': 'File too large. Max 5MB allowed.'})
        
        # Create upload directory if it doesn't exist
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        # Generate a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{session['user_id']}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save the file
        file.save(filepath)
        
        # Update user's profile image in database
        user = User.query.get(session['user_id'])
        if user:
            image_url = f'/{UPLOAD_FOLDER}/{unique_filename}'
            user.image_url = image_url
            session['user_image'] = image_url
            db.session.commit()
            
            return jsonify({'success': True, 'imageUrl': image_url})
    
    return jsonify({'success': False, 'message': 'Invalid file type'})

# ------------------------- Dashboard -----------------------------------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    dashboard_data = get_dashboard_data()
    
    return render_template('dashboard.html', **dashboard_data)

# ------------------------- Product Management ---------------------------------

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    existing_categories = get_existing_categories()
    
    if request.method == 'POST':
        try:
            name = request.form['name'].strip()
            category = request.form['category'].strip()
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            description = request.form.get('description', '').strip()
            
            # Validate inputs
            if not name:
                flash('Product name cannot be empty!', 'error')
                return render_template('add_product.html', existing_categories=existing_categories)
            
            if not category:
                flash('Category cannot be empty!', 'error')
                return render_template('add_product.html', existing_categories=existing_categories)
            
            if price < 0:
                flash('Price cannot be negative!', 'error')
                return render_template('add_product.html', existing_categories=existing_categories)
            
            if quantity < 0:
                flash('Quantity cannot be negative!', 'error')
                return render_template('add_product.html', existing_categories=existing_categories)
           
            # Capitalize first letter of category for consistency
            category = category[0].upper() + category[1:].lower() if category else category
           
            # Check if product with same name already exists (optional)
            existing_product = Product.query.filter_by(name=name).first()
            if existing_product:
                flash(f'Product "{name}" already exists! You can edit it from the inventory.', 'warning')
                return redirect(url_for('edit_product', product_id=existing_product.id))
           
            new_product = Product(
                name=name,
                category=category,
                price=price,
                quantity=quantity,
                description=description
            )
           
            db.session.add(new_product)
            db.session.commit()
            flash(f'Product "{name}" added to category "{category}" successfully!', 'success')
            return redirect(url_for('inventory'))
        except ValueError:
            db.session.rollback()
            flash('Invalid price or quantity format. Please enter valid numbers.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
   
    return render_template('add_product.html', existing_categories=existing_categories)

@app.route('/inventory')
def inventory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('inventory.html', products=products)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    product = Product.query.get_or_404(product_id)
    existing_categories = get_existing_categories()
   
    if request.method == 'POST':
        try:
            product.name = request.form['name']
            product.category = request.form['category']
            product.price = float(request.form['price'])
            product.quantity = int(request.form['quantity'])
            product.description = request.form.get('description', '')
           
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('inventory'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating product.', 'error')
   
    return render_template('edit_product.html', product=product, existing_categories=existing_categories)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
   
    try:
        product = Product.query.get_or_404(product_id)
        product_name = product.name
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Product "{product_name}" deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error deleting product'})

# ------------------------- Reports -------------------------------------------

# ... (keep all the imports and models the same)
@app.route('/report')
def report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    products = Product.query.all()
    total_count = len(products)
    total_value = sum(p.price * p.quantity for p in products)
   
    categories = {}
    for p in products:
        if p.category not in categories:
            categories[p.category] = {'count': 0, 'value': 0}
        categories[p.category]['count'] += 1
        categories[p.category]['value'] += p.price * p.quantity
   
    low_stock_items = Product.query.filter(Product.quantity < 10).all()
    
    # Convert Product objects to dictionaries for JSON serialization
    low_stock_items_dict = []
    for item in low_stock_items:
        low_stock_items_dict.append({
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'price': float(item.price),
            'quantity': item.quantity,
            'description': item.description
        })
    
    # Calculate highest value category for the report
    highest_value_category = ['', {'value': 0}]
    if categories:
        highest_value_category = max(categories.items(), key=lambda x: x[1]['value'])
    
    # Calculate category statistics
    category_stats = {
        'count': len(categories),
        'highest_value': highest_value_category,
        'total_value': total_value
    }
    
    # Calculate low stock statistics
    low_stock_stats = {
        'total': len(low_stock_items),
        'out_of_stock': len([p for p in low_stock_items if p.quantity == 0]),
        'low_stock': len([p for p in low_stock_items if p.quantity > 0 and p.quantity < 10])
    }

    return render_template(
        'report.html',
        total_count=total_count,
        total_value=total_value,
        categories=categories,
        low_stock_items=low_stock_items,  # Keep original for template display
        low_stock_items_dict=low_stock_items_dict,  # Use this for JSON serialization
        now=datetime.now(),
        category_stats=category_stats,
        low_stock_stats=low_stock_stats,
        highest_value_category=highest_value_category
    )
# ... (keep the rest of the routes the same)
# ------------------------- Database Reset ------------------------------------

@app.route('/reset-db')
def reset_db_route():
    """Reset the database to a clean state."""
    try:
        reset_database()
        init_db()  # Reinitialize with sample data
        flash('Database has been successfully reset.', 'success')
    except Exception as e:
        flash(f'Error resetting database: {e}', 'danger')
    return redirect(url_for('dashboard'))



# ------------------------------------------------------------------------------
# Run App
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    print("Starting Inventory Management System...")
    print("Database: inventory_new.db")
    print("Access the application at: http://localhost:5000")
    print("Demo credentials: demo@example.com / password123")
    app.run(debug=True)
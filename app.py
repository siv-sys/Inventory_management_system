from flask import Flask, request, jsonify, render_template
from models import Expense
from database import db, init_db
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Database configuration for cloud
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Create tables and sample data
with app.app_context():
    db.create_all()
    
    # Add sample data if no expenses exist
    if Expense.query.count() == 0:
        sample_expenses = [
            Expense(
                description='Weekly groceries at Walmart', 
                amount=125.75, 
                date=datetime.now().date() - timedelta(days=2),
                category='Food'
            ),
            Expense(
                description='Gas station fill-up', 
                amount=55.30, 
                date=datetime.now().date() - timedelta(days=1),
                category='Transport'
            ),
            Expense(
                description='Electricity bill payment', 
                amount=89.99, 
                date=datetime.now().date() - timedelta(days=5),
                category='Bills'
            ),
            Expense(
                description='Movie night with friends', 
                amount=42.50, 
                date=datetime.now().date() - timedelta(days=3),
                category='Entertainment'
            ),
            Expense(
                description='New running shoes', 
                amount=79.99, 
                date=datetime.now().date() - timedelta(days=7),
                category='Shopping'
            ),
            Expense(
                description='Coffee shop meetings', 
                amount=18.75, 
                date=datetime.now().date(),
                category='Food'
            ),
            Expense(
                description='Monthly bus pass', 
                amount=65.00, 
                date=datetime.now().date() - timedelta(days=10),
                category='Transport'
            ),
            Expense(
                description='Internet subscription', 
                amount=59.99, 
                date=datetime.now().date() - timedelta(days=8),
                category='Bills'
            )
        ]
        
        db.session.add_all(sample_expenses)
        db.session.commit()
        print("Sample data added successfully!")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# CRUD API Endpoints
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    try:
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        search = request.args.get('search')
        
        # Base query
        query = Expense.query
        
        # Apply filters
        if start_date and start_date != '':
            query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date and end_date != '':
            query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        if category and category != 'All' and category != '':
            query = query.filter(Expense.category == category)
        if search and search != '':
            query = query.filter(Expense.description.ilike(f'%{search}%'))
        
        expenses = query.order_by(Expense.date.desc()).all()
        return jsonify([expense.to_dict() for expense in expenses])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses', methods=['POST'])
def create_expense():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['description', 'amount', 'date', 'category']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be positive'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid amount format'}), 400
        
        # Create new expense
        expense = Expense(
            description=data['description'].strip(),
            amount=amount,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            category=data['category']
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return jsonify(expense.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['GET'])
def get_expense(expense_id):
    try:
        expense = Expense.query.get_or_404(expense_id)
        return jsonify(expense.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    try:
        expense = Expense.query.get_or_404(expense_id)
        data = request.get_json()
        
        if 'description' in data:
            expense.description = data['description'].strip()
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    return jsonify({'error': 'Amount must be positive'}), 400
                expense.amount = amount
            except ValueError:
                return jsonify({'error': 'Invalid amount format'}), 400
        if 'date' in data:
            expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'category' in data:
            expense.category = data['category']
        
        db.session.commit()
        
        return jsonify(expense.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    try:
        expense = Expense.query.get_or_404(expense_id)
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'message': 'Expense deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/stats', methods=['GET'])
def get_stats():
    try:
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        
        # Base query
        query = Expense.query
        
        # Apply filters
        if start_date:
            query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        if category and category != 'All':
            query = query.filter(Expense.category == category)
        
        # Calculate total
        total = db.session.query(db.func.sum(Expense.amount)).select_from(query.subquery()).scalar() or 0
        
        # Calculate category breakdown
        category_query = db.session.query(
            Expense.category, 
            db.func.sum(Expense.amount).label('total')
        )
        
        # Apply same filters to category query
        if start_date:
            category_query = category_query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            category_query = category_query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        if category and category != 'All':
            category_query = category_query.filter(Expense.category == category)
            
        category_totals = category_query.group_by(Expense.category).all()
        
        return jsonify({
            'total': round(total, 2),
            'count': query.count(),
            'by_category': {cat: round(total, 2) for cat, total in category_totals}
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/export', methods=['GET'])
def export_csv():
    try:
        expenses = get_expenses().get_json()
        csv_data = "Date,Description,Category,Amount\n"
        
        for expense in expenses:
            csv_data += f"{expense['date']},{expense['description']},{expense['category']},{expense['amount']}\n"
        
        return csv_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=expenses.csv'
        }
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = [
        'Food', 'Transport', 'Entertainment', 'Shopping', 
        'Bills', 'Healthcare', 'Education', 'Travel', 'Other'
    ]
    return jsonify(categories)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
from app import app, db, Expense
from datetime import datetime, timedelta

def add_sample_data():
    with app.app_context():
        # Clear existing data
        Expense.query.delete()
        
        # Add comprehensive sample expenses
        sample_expenses = [
            # Food expenses
            Expense(description='Weekly groceries at Walmart', amount=125.75, date=datetime.now().date() - timedelta(days=2), category='Food'),
            Expense(description='Lunch with colleagues', amount=25.75, date=datetime.now().date() - timedelta(days=1), category='Food'),
            Expense(description='Coffee shop meetings', amount=18.75, date=datetime.now().date(), category='Food'),
            Expense(description='Pizza delivery', amount=32.99, date=datetime.now().date() - timedelta(days=5), category='Food'),
            Expense(description='Restaurant dinner', amount=68.50, date=datetime.now().date() - timedelta(days=7), category='Food'),
            
            # Transport expenses
            Expense(description='Gas station fill-up', amount=55.30, date=datetime.now().date() - timedelta(days=1), category='Transport'),
            Expense(description='Monthly bus pass', amount=65.00, date=datetime.now().date() - timedelta(days=10), category='Transport'),
            Expense(description='Taxi ride', amount=28.50, date=datetime.now().date() - timedelta(days=4), category='Transport'),
            Expense(description='Car maintenance', amount=120.00, date=datetime.now().date() - timedelta(days=15), category='Transport'),
            
            # Bills
            Expense(description='Electricity bill', amount=89.99, date=datetime.now().date() - timedelta(days=5), category='Bills'),
            Expense(description='Internet subscription', amount=59.99, date=datetime.now().date() - timedelta(days=8), category='Bills'),
            Expense(description='Phone bill', amount=45.99, date=datetime.now().date() - timedelta(days=3), category='Bills'),
            Expense(description='Water bill', amount=35.50, date=datetime.now().date() - timedelta(days=12), category='Bills'),
            
            # Entertainment
            Expense(description='Movie tickets', amount=42.50, date=datetime.now().date() - timedelta(days=3), category='Entertainment'),
            Expense(description='Concert tickets', amount=120.00, date=datetime.now().date() - timedelta(days=15), category='Entertainment'),
            Expense(description='Netflix subscription', amount=15.99, date=datetime.now().date() - timedelta(days=20), category='Entertainment'),
            
            # Shopping
            Expense(description='New running shoes', amount=79.99, date=datetime.now().date() - timedelta(days=7), category='Shopping'),
            Expense(description='Office supplies', amount=45.30, date=datetime.now().date() - timedelta(days=12), category='Shopping'),
            Expense(description='Birthday gift', amount=35.00, date=datetime.now().date() - timedelta(days=6), category='Shopping'),
            
            # Other categories
            Expense(description='Dental checkup', amount=85.00, date=datetime.now().date() - timedelta(days=9), category='Healthcare'),
            Expense(description='Online course', amount=99.00, date=datetime.now().date() - timedelta(days=18), category='Education'),
            Expense(description='Weekend trip', amount=250.00, date=datetime.now().date() - timedelta(days=25), category='Travel'),
        ]
        
        db.session.add_all(sample_expenses)
        db.session.commit()
        print(f"Added {len(sample_expenses)} sample expenses successfully!")

if __name__ == '__main__':
    add_sample_data()
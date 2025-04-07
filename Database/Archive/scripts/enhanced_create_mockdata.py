import os
import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Initialize Faker
fake = Faker()

# Database setup
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "BankDB.db")
SCHEMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced_schema.sql")

# Create a connection to the database
def create_connection():
    """Create a connection to the SQLite database"""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    return conn

def execute_schema_script(conn):
    """Execute the schema script to create database tables"""
    with open(SCHEMA_FILE, 'r') as f:
        schema_script = f.read()
    conn.executescript(schema_script)
    conn.commit()

# Mock data generation functions
def create_customers(conn, n=500):
    """Generate mock customer data"""
    customers = []
    for _ in range(n):
        customer = (
            fake.first_name(),
            fake.last_name(),
            fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d'),
            fake.unique.phone_number().replace('-', '')[:15],
            fake.unique.email(),
            fake.address(),
            random.randint(300, 850),  # Credit score
            (datetime.now() - timedelta(days=random.randint(1, 3650))).strftime('%Y-%m-%d'),  # Customer since
            fake.date_time_this_decade().strftime('%Y-%m-%d %H:%M:%S')
        )
        customers.append(customer)
    
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO customers 
        (first_name, last_name, dob, phone_number, email, address, credit_score, customer_since, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', customers)
    conn.commit()
    print(f"Created {n} customers")

def create_users(conn, n=10):
    """Generate mock bank employee users"""
    roles = ['Admin', 'Teller', 'CustomerService']
    users = []
    
    for _ in range(n):
        user = (
            fake.unique.user_name(),
            fake.sha256(),  # Password hash
            random.choice(roles),
            fake.date_time_this_decade().strftime('%Y-%m-%d %H:%M:%S')
        )
        users.append(user)
    
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO users (username, password_hash, role, created_at) 
        VALUES (?, ?, ?, ?)
    ''', users)
    conn.commit()
    print(f"Created {n} users")

def create_transaction_categories(conn):
    """Create transaction categories"""
    categories = [
        ('Shopping', 'Purchases from retail stores'),
        ('Groceries', 'Purchases of food and household items'),
        ('Dining', 'Restaurant and eating out expenses'),
        ('Entertainment', 'Movies, games, and other recreational activities'),
        ('Utilities', 'Bills for electricity, water, gas, etc.'),
        ('Rent/Mortgage', 'Housing payments'),
        ('Transportation', 'Public transit, fuel, ride sharing'),
        ('Travel', 'Flights, hotels, vacation expenses'),
        ('Healthcare', 'Medical bills, pharmacy, insurance'),
        ('Education', 'Tuition, books, courses'),
        ('Subscriptions', 'Recurring digital services'),
        ('Investments', 'Stocks, bonds, crypto purchases'),
        ('Income', 'Salary, wages, freelance payments'),
        ('Transfer', 'Moving money between accounts'),
        ('Withdrawal', 'Taking money out of account'),
        ('Deposit', 'Adding money to account')
    ]
    
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO transaction_categories (category_name, description) 
        VALUES (?, ?)
    ''', categories)
    conn.commit()
    print(f"Created {len(categories)} transaction categories")

def create_merchants(conn, n=100):
    """Generate mock merchant data"""
    categories = ['Retail', 'Grocery', 'Restaurant', 'Utility', 'Entertainment', 'Travel', 
                 'Healthcare', 'Education', 'Technology', 'Services', 'Transportation']
    
    merchants = []
    for _ in range(n):
        merchant = (
            fake.company(),
            random.choice(categories),
            fake.address()
        )
        merchants.append(merchant)
    
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO merchants (merchant_name, category, location) 
        VALUES (?, ?, ?)
    ''', merchants)
    conn.commit()
    print(f"Created {n} merchants")

def create_benefits(conn):
    """Create card and account benefits"""
    benefits = [
        ('Cash Back', 'Earn cash back on purchases'),
        ('Travel Insurance', 'Coverage for trip cancellations and emergencies'),
        ('Extended Warranty', 'Additional warranty coverage on purchases'),
        ('Price Protection', 'Refund if price drops after purchase'),
        ('Concierge Service', 'Personal assistance service'),
        ('Airport Lounge Access', 'Free access to airport lounges'),
        ('No Foreign Transaction Fee', 'No fees on international purchases'),
        ('Rental Car Insurance', 'Coverage for rental car damages'),
        ('Reward Points', 'Earn points for each purchase'),
        ('Purchase Protection', 'Coverage for theft or damage'),
        ('Roadside Assistance', 'Emergency road service'),
        ('Zero Liability', 'No responsibility for fraudulent charges'),
        ('Fraud Alerts', 'Get notified of suspicious activity'),
        ('Free Credit Score', 'Access to your credit score'),
        ('Overdraft Protection', 'Protection from overdraft fees')
    ]
    
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO benefits (benefit_name, description) 
        VALUES (?, ?)
    ''', benefits)
    conn.commit()
    print(f"Created {len(benefits)} benefits")

def create_accounts(conn, n=1000):
    """Generate mock account data"""
    account_types = ['Savings', 'Checking', 'Loan', 'Credit Card']
    currencies = ['USD', 'EUR', 'GBP', 'INR', 'CAD', 'AUD']
    
    # Get all customer IDs
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id FROM customers")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    accounts = []
    for _ in range(n):
        account_type = random.choice(account_types)
        
        # Set appropriate fields based on account type
        interest_rate = None
        credit_limit = None
        due_date = None
        
        if account_type == 'Savings':
            interest_rate = round(random.uniform(0.5, 3.5), 2)
        elif account_type == 'Loan':
            interest_rate = round(random.uniform(4.0, 12.0), 2)
            due_date = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')
        elif account_type == 'Credit Card':
            interest_rate = round(random.uniform(15.0, 24.0), 2)
            credit_limit = round(random.uniform(1000, 30000), 2)
            due_date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
        
        currency = random.choice(currencies)
        open_date = fake.date_time_between(start_date='-5y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
        
        account = (
            random.choice(customer_ids),
            account_type,
            fake.unique.bban(),
            round(random.uniform(0, 50000), 2),
            currency,
            random.choices(['Active', 'Inactive', 'Closed', 'Frozen'], weights=[0.85, 0.05, 0.05, 0.05])[0],
            interest_rate,
            credit_limit,
            due_date,
            open_date
        )
        accounts.append(account)
    
    cursor.executemany('''
        INSERT INTO accounts (
            customer_id, account_type, account_number, balance, currency, status, 
            interest_rate, credit_limit, due_date, opened_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', accounts)
    conn.commit()
    print(f"Created {n} accounts")

def create_account_benefits(conn):
    """Assign benefits to accounts"""
    cursor = conn.cursor()
    
    # Get account IDs
    cursor.execute("SELECT account_id FROM accounts WHERE account_type IN ('Savings', 'Credit Card') AND status = 'Active'")
    account_ids = [row[0] for row in cursor.fetchall()]
    
    # Get benefit IDs
    cursor.execute("SELECT benefit_id FROM benefits")
    benefit_ids = [row[0] for row in cursor.fetchall()]
    
    # Assign benefits to about 50% of eligible accounts
    account_benefits = []
    for account_id in random.sample(account_ids, len(account_ids) // 2):
        # Each account gets 1-4 benefits
        assigned_benefits = random.sample(benefit_ids, random.randint(1, min(4, len(benefit_ids))))
        
        for benefit_id in assigned_benefits:
            activation_date = fake.date_time_between(start_date='-2y', end_date='now').strftime('%Y-%m-%d')
            expiry_date = (datetime.now() + timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d')
            
            account_benefits.append((
                account_id,
                benefit_id,
                activation_date,
                expiry_date,
                random.choices(['Active', 'Inactive', 'Expired'], weights=[0.9, 0.05, 0.05])[0]
            ))
    
    cursor.executemany('''
        INSERT INTO account_benefits (account_id, benefit_id, activation_date, expiry_date, status) 
        VALUES (?, ?, ?, ?, ?)
    ''', account_benefits)
    conn.commit()
    print(f"Created {len(account_benefits)} account benefits")

def create_credit_cards(conn, n=500):
    """Generate mock credit card data"""
    card_types = ['Visa', 'MasterCard', 'Amex', 'Discover']
    
    # Get account IDs of credit card accounts
    cursor = conn.cursor()
    cursor.execute("SELECT account_id FROM accounts WHERE account_type = 'Credit Card'")
    credit_card_account_ids = [row[0] for row in cursor.fetchall()]
    
    if not credit_card_account_ids:
        print("No credit card accounts found")
        return
    
    credit_cards = []
    for _ in range(min(n, len(credit_card_account_ids))):
        account_id = random.choice(credit_card_account_ids)
        card_type = random.choice(card_types)
        
        # Generate appropriate card number based on type
        if card_type == 'Visa':
            card_number = '4' + ''.join([str(random.randint(0, 9)) for _ in range(15)])
        elif card_type == 'MasterCard':
            card_number = '5' + ''.join([str(random.randint(0, 9)) for _ in range(15)])
        elif card_type == 'Amex':
            card_number = '3' + ''.join([str(random.randint(0, 9)) for _ in range(14)])
        else:  # Discover
            card_number = '6' + ''.join([str(random.randint(0, 9)) for _ in range(15)])
        
        issued_date = fake.date_time_between(start_date='-5y', end_date='-1d').strftime('%Y-%m-%d')
        expiry_date = (datetime.strptime(issued_date, '%Y-%m-%d') + timedelta(days=1095)).strftime('%Y-%m-%d')
        
        credit_card = (
            account_id,
            card_number,
            card_type,
            expiry_date,
            str(random.randint(100, 999)) if card_type != 'Amex' else str(random.randint(1000, 9999)),
            random.choices(['Active', 'Blocked', 'Expired'], weights=[0.9, 0.05, 0.05])[0],
            issued_date,
            round(random.uniform(1000, 10000), 2)  # Monthly limit
        )
        credit_cards.append(credit_card)
    
    cursor.executemany('''
        INSERT INTO credit_cards (
            account_id, card_number, card_type, expiry_date, cvv, card_status, issued_date, monthly_limit
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', credit_cards)
    conn.commit()
    print(f"Created {len(credit_cards)} credit cards")

def create_card_benefits(conn):
    """Assign benefits to credit cards"""
    cursor = conn.cursor()
    
    # Get card IDs of active cards
    cursor.execute("SELECT card_id FROM credit_cards WHERE card_status = 'Active'")
    card_ids = [row[0] for row in cursor.fetchall()]
    
    # Get benefit IDs
    cursor.execute("SELECT benefit_id FROM benefits")
    benefit_ids = [row[0] for row in cursor.fetchall()]
    
    # Assign benefits to cards
    card_benefits = []
    for card_id in card_ids:
        # Each card gets 1-5 benefits
        assigned_benefits = random.sample(benefit_ids, random.randint(1, min(5, len(benefit_ids))))
        
        for benefit_id in assigned_benefits:
            activation_date = fake.date_time_between(start_date='-2y', end_date='now').strftime('%Y-%m-%d')
            expiry_date = (datetime.now() + timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d')
            
            card_benefits.append((
                card_id,
                benefit_id,
                activation_date,
                expiry_date,
                random.choices(['Active', 'Inactive', 'Expired'], weights=[0.9, 0.05, 0.05])[0]
            ))
    
    cursor.executemany('''
        INSERT INTO card_benefits (card_id, benefit_id, activation_date, expiry_date, status) 
        VALUES (?, ?, ?, ?, ?)
    ''', card_benefits)
    conn.commit()
    print(f"Created {len(card_benefits)} card benefits")

def create_transactions(conn, n=10000):
    """Generate realistic transaction data"""
    transaction_types = ['Deposit', 'Withdrawal', 'Transfer', 'Payment']
    currencies = ['USD', 'EUR', 'GBP', 'INR', 'CAD', 'AUD']
    statuses = ['Pending', 'Completed', 'Failed', 'Reversed']
    
    cursor = conn.cursor()
    
    # Get all account IDs with their balances and currencies
    cursor.execute("SELECT account_id, balance, currency FROM accounts WHERE status = 'Active'")
    accounts_data = cursor.fetchall()
    if not accounts_data:
        print("No active accounts found")
        return
    
    # Create a dictionary for easy access
    accounts = {account[0]: {'balance': account[1], 'currency': account[2]} for account in accounts_data}
    account_ids = list(accounts.keys())
    
    # Get merchant IDs
    cursor.execute("SELECT merchant_id FROM merchants")
    merchant_ids = [row[0] for row in cursor.fetchall()]
    
    # Get category IDs
    cursor.execute("SELECT category_id, category_name FROM transaction_categories")
    categories = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Generate transactions with time ordering
    transactions = []
    account_transaction_dates = {account_id: datetime.now() - timedelta(days=365) for account_id in account_ids}
    
    for _ in range(n):
        account_id = random.choice(account_ids)
        transaction_type = random.choice(transaction_types)
        
        # Set appropriate fields based on transaction type
        merchant_id = None
        category_id = None
        receiver_account_id = None
        
        # Calculate amount based on transaction type and account balance
        if transaction_type == 'Deposit':
            amount = round(random.uniform(10, 5000), 2)
            category_id = categories.get('Deposit')
        elif transaction_type == 'Withdrawal':
            # Ensure withdrawal is less than balance
            max_withdrawal = min(accounts[account_id]['balance'], 2000)
            if max_withdrawal <= 0:
                continue  # Skip if account balance is 0
            amount = round(random.uniform(10, max_withdrawal), 2)
            category_id = categories.get('Withdrawal')
        elif transaction_type == 'Transfer':
            # Ensure transfer is less than balance
            max_transfer = min(accounts[account_id]['balance'], 3000)
            if max_transfer <= 0:
                continue  # Skip if account balance is 0
            amount = round(random.uniform(10, max_transfer), 2)
            # Select a random receiver account
            potential_receivers = [acc_id for acc_id in account_ids if acc_id != account_id]
            if potential_receivers:
                receiver_account_id = random.choice(potential_receivers)
            category_id = categories.get('Transfer')
        else:  # Payment
            # Ensure payment is less than balance
            max_payment = min(accounts[account_id]['balance'], 1000)
            if max_payment <= 0:
                continue  # Skip if account balance is 0
            amount = round(random.uniform(10, max_payment), 2)
            merchant_id = random.choice(merchant_ids)
            
            # Select an appropriate category based on the payment
            payment_categories = [cat for cat in categories.keys() if cat not in ['Deposit', 'Withdrawal', 'Transfer', 'Income']]
            if payment_categories:
                category_name = random.choice(payment_categories)
                category_id = categories.get(category_name)
        
        # Generate transaction date (ensures chronological order for each account)
        last_date = account_transaction_dates[account_id]
        days_increment = random.randint(0, 7)  # 0-7 days since last transaction
        hours_increment = random.randint(0, 23) if days_increment == 0 else 0
        minutes_increment = random.randint(1, 59) if days_increment == 0 and hours_increment == 0 else 0
        
        transaction_date = last_date + timedelta(
            days=days_increment, 
            hours=hours_increment, 
            minutes=minutes_increment
        )
        
        # Don't allow future dates
        if transaction_date > datetime.now():
            transaction_date = datetime.now()
        
        # Update the last transaction date for this account
        account_transaction_dates[account_id] = transaction_date
        
        # Generate a description
        if transaction_type == 'Deposit':
            description = random.choice([
                "Salary deposit", "Cash deposit", "Check deposit", 
                "Interest credit", "Refund", "Incoming wire transfer"
            ])
        elif transaction_type == 'Withdrawal':
            description = random.choice([
                "ATM withdrawal", "Cash withdrawal", "Fund transfer out",
                "Bill payment", "Investment purchase"
            ])
        elif transaction_type == 'Transfer':
            description = f"Transfer to account ending in {random.randint(1000, 9999)}"
        else:  # Payment
            if merchant_id:
                cursor.execute("SELECT merchant_name FROM merchants WHERE merchant_id = ?", (merchant_id,))
                merchant_name = cursor.fetchone()[0]
                description = f"Payment to {merchant_name}"
            else:
                description = "Payment"
        
        status = random.choices(statuses, weights=[0.05, 0.9, 0.03, 0.02])[0]
        currency = accounts[account_id]['currency']
        
        transaction = (
            account_id,
            transaction_type,
            amount,
            currency,
            transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
            status,
            description,
            merchant_id,
            category_id,
            receiver_account_id
        )
        transactions.append(transaction)
        
        # Update account balances for completed transactions
        if status == 'Completed':
            if transaction_type in ['Withdrawal', 'Transfer', 'Payment']:
                accounts[account_id]['balance'] -= amount
            elif transaction_type == 'Deposit':
                accounts[account_id]['balance'] += amount
    
    # Insert transactions
    cursor.executemany('''
        INSERT INTO transactions (
            account_id, transaction_type, amount, currency, transaction_date, status, description,
            merchant_id, category_id, receiver_account_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', transactions)
    
    # Update account balances
    for account_id, data in accounts.items():
        cursor.execute("UPDATE accounts SET balance = ? WHERE account_id = ?", (data['balance'], account_id))
    
    conn.commit()
    print(f"Created {len(transactions)} transactions")

def create_transaction_tags(conn):
    """Generate tags for transactions for better AI analysis"""
    cursor = conn.cursor()
    
    # Get transactions with categories
    cursor.execute("""
        SELECT t.transaction_id, tc.category_name
        FROM transactions t
        JOIN transaction_categories tc ON t.category_id = tc.category_id
        WHERE t.status = 'Completed'
    """)
    transaction_categories = cursor.fetchall()
    
    # Define possible tags per category
    category_tags = {
        'Shopping': ['online', 'retail', 'clothing', 'electronics', 'furniture', 'luxury'],
        'Groceries': ['supermarket', 'organic', 'bulk', 'discount', 'weekly'],
        'Dining': ['restaurant', 'fast-food', 'cafe', 'delivery', 'lunch', 'dinner'],
        'Entertainment': ['movies', 'streaming', 'concert', 'games', 'sports', 'subscription'],
        'Utilities': ['electricity', 'water', 'gas', 'internet', 'phone', 'monthly'],
        'Rent/Mortgage': ['housing', 'apartment', 'home', 'monthly'],
        'Transportation': ['fuel', 'public-transit', 'ride-share', 'taxi', 'car', 'travel'],
        'Travel': ['flight', 'hotel', 'vacation', 'booking', 'international', 'domestic'],
        'Healthcare': ['medical', 'pharmacy', 'insurance', 'dental', 'therapy', 'routine'],
        'Education': ['tuition', 'books', 'courses', 'school', 'university', 'online-learning'],
        'Subscriptions': ['streaming', 'software', 'news', 'monthly', 'annual'],
        'Investments': ['stocks', 'bonds', 'crypto', 'retirement', 'savings'],
        'Income': ['salary', 'bonus', 'freelance', 'interest', 'dividend'],
        'Transfer': ['internal', 'external', 'recurring', 'one-time'],
        'Withdrawal': ['atm', 'in-person', 'emergency', 'planned'],
        'Deposit': ['check', 'cash', 'electronic', 'recurring', 'one-time']
    }
    
    # Tags indicating spending patterns for any category
    general_tags = ['recurring', 'one-time', 'essential', 'discretionary', 'emergency', 'planned']
    
    transaction_tags = []
    
    for transaction_id, category_name in transaction_categories:
        # Get category-specific tags
        specific_tags = category_tags.get(category_name, [])
        
        # Choose 1-3 tags
        num_tags = random.randint(1, 3)
        
        # 70% chance to include at least one category-specific tag if available
        if specific_tags and random.random() < 0.7:
            chosen_tags = random.sample(specific_tags, min(num_tags, len(specific_tags)))
            # If we need more tags, add from general tags
            if len(chosen_tags) < num_tags:
                additional_tags = random.sample(general_tags, num_tags - len(chosen_tags))
                chosen_tags.extend(additional_tags)
        else:
            # Otherwise just choose from general tags
            chosen_tags = random.sample(general_tags, min(num_tags, len(general_tags)))
        
        # Add tags to the transaction
        for tag in chosen_tags:
            transaction_tags.append((transaction_id, tag))
    
    cursor.executemany('''
        INSERT INTO transaction_tags (transaction_id, tag) 
        VALUES (?, ?)
    ''', transaction_tags)
    conn.commit()
    print(f"Created {len(transaction_tags)} transaction tags")

def create_bills(conn, n=300):
    """Generate recurring bills for customers"""
    cursor = conn.cursor()
    
    # Get account IDs for checking accounts
    cursor.execute("SELECT account_id FROM accounts WHERE account_type = 'Checking' AND status = 'Active'")
    checking_accounts = [row[0] for row in cursor.fetchall()]
    
    if not checking_accounts:
        print("No checking accounts found")
        return
    
    # Get merchant IDs
    cursor.execute("SELECT merchant_id, merchant_name, category FROM merchants")
    merchants_data = cursor.fetchall()
    
    # Group merchants by category
    merchants_by_category = {}
    for merchant_id, name, category in merchants_data:
        if category not in merchants_by_category:
            merchants_by_category[category] = []
        merchants_by_category[category].append((merchant_id, name))
    
    # Define bill types with typical amounts and categories
    bill_types = {
        'Utility': {
            'names': ['Electricity Bill', 'Water Bill', 'Gas Bill', 'Internet Bill', 'Phone Bill'],
            'amount_range': (50, 300)
        },
        'Services': {
            'names': ['Insurance Payment', 'Subscription Service', 'Gym Membership'],
            'amount_range': (20, 200)
        },
        'Rent/Mortgage': {
            'names': ['Rent Payment', 'Mortgage Payment', 'Property Tax'],
            'amount_range': (500, 3000)
        },
        'Entertainment': {
            'names': ['Netflix Subscription', 'Spotify Premium', 'HBO Max', 'Disney+', 'Amazon Prime'],
            'amount_range': (5, 30)
        },
        'Transportation': {
            'names': ['Car Payment', 'Car Insurance', 'Public Transit Pass'],
            'amount_range': (60, 800)
        }
    }
    
    bills = []
    for _ in range(n):
        # Select a random account
        account_id = random.choice(checking_accounts)
        
        # Get account's currency
        cursor.execute("SELECT currency FROM accounts WHERE account_id = ?", (account_id,))
        currency = cursor.fetchone()[0]
        
        # Select a bill category and type
        bill_category = random.choice(list(bill_types.keys()))
        
        # Find merchants in this category
        if bill_category in merchants_by_category and merchants_by_category[bill_category]:
            merchant_id, merchant_name = random.choice(merchants_by_category[bill_category])
        else:
            # Use any merchant if no category match
            merchant_id, merchant_name = random.choice(random.choice(list(merchants_by_category.values())))
        
        # Generate bill details
        bill_name = random.choice(bill_types[bill_category]['names'])
        min_amount, max_amount = bill_types[bill_category]['amount_range']
        amount = round(random.uniform(min_amount, max_amount), 2)
        
        # Bill dates
        bill_date = fake.date_time_between(start_date='-60d', end_date='-30d').strftime('%Y-%m-%d')
        due_date = (datetime.strptime(bill_date, '%Y-%m-%d') + timedelta(days=random.randint(14, 30))).strftime('%Y-%m-%d')
        
        # Bill status
        if datetime.strptime(due_date, '%Y-%m-%d') < datetime.now():
            status = random.choices(['Paid', 'Overdue'], weights=[0.9, 0.1])[0]
        else:
            status = random.choices(['Pending', 'Paid'], weights=[0.7, 0.3])[0]
        
        # Recurring or one-time
        recurring = random.choices([0, 1], weights=[0.3, 0.7])[0]
        recurrence_period = None
        if recurring:
            recurrence_period = random.choice(['Monthly', 'Quarterly', 'Annually'])
        
        bill = (
            account_id,
            merchant_id,
            bill_name,
            amount,
            currency,
            bill_date,
            due_date,
            status,
            recurring,
            recurrence_period
        )
        bills.append(bill)
    
    cursor.executemany('''
        INSERT INTO bills (
            account_id, merchant_id, bill_name, amount, currency, bill_date, due_date,
            status, recurring, recurrence_period
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', bills)
    conn.commit()
    print(f"Created {len(bills)} bills")

# Main function to create all data
def create_mock_data():
    """Main function to generate all mock data"""
    conn = create_connection()
    
    try:
        # Create tables from schema
        execute_schema_script(conn)
        
        # Generate data in proper order (respecting foreign key constraints)
        create_customers(conn, 500)
        create_users(conn, 10)
        create_transaction_categories(conn)
        create_merchants(conn, 100)
        create_benefits(conn)
        create_accounts(conn, 1000)
        create_account_benefits(conn)
        create_credit_cards(conn, 500)
        create_card_benefits(conn)
        create_transactions(conn, 10000)
        create_transaction_tags(conn)
        create_bills(conn, 300)
        
        print("Mock data creation complete!")
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_mock_data() 
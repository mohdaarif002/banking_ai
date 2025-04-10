import mysql.connector
from faker import Faker
import random
from datetime import datetime, timedelta
import json
import os

from dotenv import load_dotenv
load_dotenv()

# Initialize Faker
fake = Faker()

import mysql.connector
# Database connection
def get_db_connection():
    try:
        print("Connecting to database...")
        conn = mysql.connector.connect(
            host="localhost",
            user=os.getenv('DB_USER'), 
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv("DB_NAME"),
            use_pure=True
        )
        print("Successfully connected to database")
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        print(f"Please check:")
        print("1. MySQL server is running")
        print("2. Database 'BankDB2' exists")
        print("3. Username and password are correct") 
        print("4. Host is accessible")
        print(f"Full error: {err}")
        raise
    except Exception as e:
        print(f"Unexpected error connecting to database: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error args: {e.args}")
        raise

def create_mock_customers(conn, num_customers=100):
    try:
        cursor = conn.cursor()
        for i in range(1, num_customers + 1):
            first_name = fake.first_name()
            last_name = fake.last_name()
            dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
            phone = f"+91-{fake.msisdn()[:10]}"  # Format: +91 followed by 10 digits
            email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
            address = fake.address()
            credit_score = random.randint(300, 850)
            credit_score_updated_at = fake.date_time_between(start_date='-1y', end_date='now')
            customer_since = fake.date_between(start_date='-5y', end_date='today')
            
            cursor.execute("""
                INSERT INTO Customers 
                (first_name, last_name, dob, phone_number, email, address, credit_score, 
                 credit_score_updated_at, customer_since)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (first_name, last_name, dob, phone, email, address, credit_score, 
                  credit_score_updated_at, customer_since))
        
        conn.commit()
        print(f"Created {num_customers} customers")
    except mysql.connector.Error as err:
        print(f"Error creating customers: {err}")
        conn.rollback()
        raise

def create_mock_accounts(conn, num_accounts_per_customer=2):
    try:
        cursor = conn.cursor()
        
        # Get all customer IDs
        cursor.execute("SELECT customer_id FROM Customers")
        customer_ids = [row[0] for row in cursor.fetchall()]
        
        account_types = ['Savings',
                         'Current',
                         'Loan',
                         'Credit Card']
        currencies = ['INR']
        
        # Define weights for number of accounts (1-10)
        # Higher weights for fewer accounts, decreasing as number increases
        account_weights = {
            1: 0.35,  # 35% chance of having 1 account
            2: 0.25,  # 25% chance of having 2 accounts
            3: 0.15,  # 15% chance of having 3 accounts
            4: 0.10,  # 10% chance of having 4 accounts
            5: 0.05,  # 5% chance of having 5 accounts
            6: 0.04,  # 4% chance of having 6 accounts
            7: 0.03,  # 3% chance of having 7 accounts
            8: 0.02,  # 2% chance of having 8 accounts
            9: 0.01,  # 1% chance of having 9 accounts
            10: 0.00  # 0% chance of having 10 accounts (rounded up from 0.005)
        }
        
        for customer_id in customer_ids:
            # Select number of accounts based on weighted distribution
            num_accounts = random.choices(
                list(account_weights.keys()),
                weights=list(account_weights.values()),
                k=1
            )[0]
            
            # Track which account types have been created for this customer
            created_account_types = set()
            
            for _ in range(num_accounts):
                # Ensure each customer has at least one savings account
                if not created_account_types and 'Savings' not in created_account_types:
                    account_type = 'Savings'
                else:
                    # For subsequent accounts, choose from remaining types
                    available_types = [t for t in account_types if t not in created_account_types]
                    if not available_types:
                        available_types = account_types  # If all types used, allow duplicates
                    account_type = random.choice(available_types)
                
                created_account_types.add(account_type)
                
                account_number = fake.bban()
                balance = round(random.uniform(100, 100000), 2)
                currency = random.choice(currencies)
                status = random.choice(['Active', 'Inactive', 'Closed', 'Frozen'])
                
                # Credit-related fields
                credit_limit = round(random.uniform(1000, 50000), 2) if account_type == 'Credit Card' else None
                due_date = fake.date_between(start_date='today', end_date='+30d') if account_type in ['Credit Card', 'Loan'] else None
                interest_rate = round(random.uniform(0.5, 15.0), 2) if account_type in ['Loan', 'Credit Card'] else None
                
                # Handle outstanding balance based on account type
                if account_type in ['Loan', 'Credit Card']:
                    # For loans and credit cards, outstanding balance should be >= balance
                    # Include additional fees, interest, or penalties
                    outstanding_balance = round(balance + random.uniform(0, 10000), 2)
                else:
                    # For savings and current accounts, outstanding balance must be 0
                    outstanding_balance = 0.00
                
                cursor.execute("""
                    INSERT INTO Accounts 
                    (customer_id, account_type, account_number, balance, outstanding_balance, currency, status, 
                     interest_rate, credit_limit, due_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (customer_id, account_type, account_number, balance, outstanding_balance, currency, status, 
                      interest_rate, credit_limit, due_date))
        
        conn.commit()
        print("Created accounts for all customers with realistic distribution")
    except mysql.connector.Error as err:
        print(f"Error creating accounts: {err}")
        conn.rollback()
        raise

def create_mock_payees(conn, num_payees_per_customer=5):
    try:
        cursor = conn.cursor()
        
        # Get all customer IDs
        cursor.execute("SELECT customer_id FROM Customers")
        customer_ids = [row[0] for row in cursor.fetchall()]
        
        payee_types = ['Merchant', 'Individual', 'Business', 'Bill', 'International']
        
        for customer_id in customer_ids:
            for _ in range(random.randint(1, num_payees_per_customer)):
                payee_name = fake.company() if random.random() > 0.5 else fake.name()
                payee_type = random.choice(payee_types)
                account_number = fake.bban() if random.random() > 0.3 else None
                bank_name = fake.company() if account_number else None
                email = fake.email() if random.random() > 0.3 else None
                phone = phone = f"+91-{fake.msisdn()[:10]}"  # Format: +91 followed by 10 digits if random.random() > 0.3 else None
                address = fake.address() if random.random() > 0.3 else None
                is_favorite = random.choice([True, False])
                
                cursor.execute("""
                    INSERT INTO Payees 
                    (customer_id, payee_name, payee_type, account_number, bank_name, 
                     email, phone, address, is_favorite)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (customer_id, payee_name, payee_type, account_number, bank_name, 
                      email, phone, address, is_favorite))
        
        conn.commit()
        print("Created payees for all customers")
    except mysql.connector.Error as err:
        print(f"Error creating payees: {err}")
        conn.rollback()
        raise

def create_mock_transactions(conn, num_transactions_per_account=20):
    try:
        cursor = conn.cursor()
        
        # Get all account IDs
        cursor.execute("SELECT account_id, account_type FROM Accounts")
        accounts = cursor.fetchall()
        
        transaction_types = ['Deposit', 'Withdrawal', 'Transfer', 'Payment']
        statuses = ['Pending', 'Completed', 'Failed', 'Reversed']
        
        for account_id, account_type in accounts:
            # Get payees for this account's customer
            cursor.execute("""
                SELECT p.payee_id 
                FROM Payees p
                JOIN Accounts a ON p.customer_id = a.customer_id
                WHERE a.account_id = %s
            """, (account_id,))
            payee_ids = [row[0] for row in cursor.fetchall()]
            
            for _ in range(random.randint(5, num_transactions_per_account)):
                transaction_type = random.choice(transaction_types)
                amount = round(random.uniform(10, 5000), 2)
                currency = 'USD'  # Simplified for mock data
                status = random.choice(statuses)
                description = fake.sentence()
                payee_id = random.choice(payee_ids) if payee_ids and transaction_type in ['Transfer', 'Payment'] else None
                
                # Generate transaction date within last 6 months
                transaction_date = fake.date_time_between(start_date='-6m', end_date='now')
                
                cursor.execute("""
                    INSERT INTO Transactions 
                    (account_id, transaction_type, amount, currency, transaction_date, 
                     status, description, payee_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (account_id, transaction_type, amount, currency, transaction_date, 
                      status, description, payee_id))
        
        conn.commit()
        print("Created transactions for all accounts")
    except mysql.connector.Error as err:
        print(f"Error creating transactions: {err}")
        conn.rollback()
        raise

def create_mock_credit_cards(conn):
    try:
        cursor = conn.cursor()
        
        # Get credit card accounts
        cursor.execute("""
            SELECT account_id 
            FROM Accounts 
            WHERE account_type = 'Credit Card'
        """)
        credit_card_accounts = cursor.fetchall()
        
        card_types = ['Visa', 'MasterCard', 'Amex', 'Discover']
        
        for account_id, in credit_card_accounts:
            card_number = fake.credit_card_number(card_type=None)[:16]  # Limit to 16 characters
            card_type = random.choice(card_types)
            expiry_date = fake.date_between(start_date='today', end_date='+5y')
            cvv = fake.credit_card_security_code()
            card_status = random.choice(['Active', 'Blocked', 'Expired'])
            issued_date = fake.date_between(start_date='-2y', end_date='today')
            monthly_limit = round(random.uniform(1000, 50000), 2)
            
            cursor.execute("""
                INSERT INTO Credit_Cards 
                (account_id, card_number, card_type, expiry_date, cvv, 
                 card_status, issued_date, monthly_limit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (account_id, card_number, card_type, expiry_date, cvv, 
                  card_status, issued_date, monthly_limit))
        
        conn.commit()
        print("Created credit cards for credit card accounts")
    except mysql.connector.Error as err:
        print(f"Error creating credit cards: {err}")
        conn.rollback()
        raise

def create_mock_bills(conn):
    try:
        cursor = conn.cursor()
        
        # Get all accounts
        cursor.execute("SELECT account_id FROM Accounts")
        accounts = cursor.fetchall()
        
        bill_names = ['Electricity', 'Water', 'Internet', 'Phone', 'Rent', 'Insurance']
        statuses = ['Pending', 'Paid', 'Overdue', 'Cancelled']
        recurrence_periods = ['Weekly', 'Monthly', 'Quarterly', 'Annually']
        
        for account_id, in accounts:
            # Create 1-3 bills per account
            for _ in range(random.randint(1, 3)):
                bill_name = random.choice(bill_names)
                amount = round(random.uniform(50, 1000), 2)
                currency = 'USD'  # Simplified for mock data
                bill_date = fake.date_between(start_date='-1m', end_date='today')
                due_date = fake.date_between(start_date='today', end_date='+30d')
                status = random.choice(statuses)
                recurring = random.choice([True, False])
                recurrence_period = random.choice(recurrence_periods) if recurring else None
                merchant_id = random.randint(1, 100)  # Generate a random merchant_id
                
                cursor.execute("""
                    INSERT INTO Bills 
                    (account_id, merchant_id, bill_name, amount, currency, bill_date, 
                     due_date, status, recurring, recurrence_period)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (account_id, merchant_id, bill_name, amount, currency, bill_date, 
                      due_date, status, recurring, recurrence_period))
        
        conn.commit()
        print("Created bills for all accounts")
    except mysql.connector.Error as err:
        print(f"Error creating bills: {err}")
        conn.rollback()
        raise

def create_mock_customer_summaries(conn):
    try:
        cursor = conn.cursor()
        
        # Get all customer IDs
        cursor.execute("SELECT customer_id FROM Customers")
        customer_ids = [row[0] for row in cursor.fetchall()]
        
        for customer_id in customer_ids:
            # 1. Get account summary data
            cursor.execute("""
                SELECT 
                    SUM(balance) as total_balance,
                    COUNT(*) as total_accounts,
                    COUNT(CASE WHEN Accounts.status = 'Active' THEN 1 END) as active_accounts,
                    COUNT(CASE WHEN Accounts.status = 'Inactive' THEN 1 END) as inactive_accounts,
                    COUNT(CASE WHEN Accounts.status = 'Closed' THEN 1 END) as closed_accounts,
                    COUNT(CASE WHEN Accounts.status = 'Frozen' THEN 1 END) as frozen_accounts,
                    GROUP_CONCAT(DISTINCT account_type) as account_types
                FROM Accounts
                WHERE customer_id = %s
            """, (customer_id,))
            account_data = cursor.fetchone()
            
            # Get balance breakdown by account type
            cursor.execute("""
                SELECT 
                    account_type,
                    SUM(balance) as type_balance,
                    COUNT(*) as type_count
                FROM Accounts
                WHERE customer_id = %s
                GROUP BY account_type
            """, (customer_id,))
            account_type_breakdown = {}
            for account_type, type_balance, type_count in cursor.fetchall():
                account_type_breakdown[account_type] = {
                    "balance": float(type_balance or 0),
                    "count": int(type_count or 0)
                }
            
            # Get individual account details
            cursor.execute("""
                SELECT 
                    account_id,
                    account_type,
                    account_number,
                    balance,
                    Accounts.currency,
                    status,
                    interest_rate,
                    credit_limit,
                    due_date
                FROM Accounts
                WHERE customer_id = %s
            """, (customer_id,))
            
            individual_accounts = []
            for (acc_id, acc_type, acc_number, balance, currency, 
                 status, interest_rate, credit_limit, due_date) in cursor.fetchall():
                individual_accounts.append({
                    "account_id": acc_id,
                    "account_type": acc_type,
                    "account_number": acc_number,
                    "last_4_digits": acc_number[-4:] if acc_number else None,
                    "balance": float(balance or 0),
                    "currency": currency,
                    "status": status,
                    "interest_rate": float(interest_rate or 0) if interest_rate else None,
                    "credit_limit": float(credit_limit or 0) if credit_limit else None,
                    "due_date": due_date.strftime("%Y-%m-%d") if due_date else None
                })
            
            # Build the enhanced account summary
            account_summary = {
                "total_balance": float(account_data[0] or 0),
                "total_accounts": int(account_data[1] or 0),
                "status_breakdown": {
                    "active": int(account_data[2] or 0),
                    "inactive": int(account_data[3] or 0),
                    "closed": int(account_data[4] or 0),
                    "frozen": int(account_data[5] or 0)
                },
                "account_types": account_data[6].split(',') if account_data[6] else [],
                "type_breakdown": account_type_breakdown,
                "accounts": individual_accounts
            }
            
            # 2. Get transaction summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_transactions,
                    SUM(amount) as total_amount
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
            """, (customer_id,))
            total_tx_data = cursor.fetchone()
            
            # Last month transactions
            cursor.execute("""
                SELECT 
                    COUNT(*) as monthly_transactions,
                    AVG(amount) as avg_transaction
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
                AND t.transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)
            """, (customer_id,))
            monthly_tx_data = cursor.fetchone()
            
            # Transaction breakdown by type
            cursor.execute("""
                SELECT 
                    transaction_type,
                    COUNT(*) as count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
                GROUP BY transaction_type
            """, (customer_id,))
            
            transaction_types = {}
            for tx_type, count, total, avg in cursor.fetchall():
                transaction_types[tx_type] = {
                    "count": int(count or 0),
                    "total_amount": float(total or 0),
                    "average_amount": float(avg or 0)
                }
            
            # Most frequent payees
            cursor.execute("""
                SELECT 
                    p.payee_name,
                    COUNT(*) as transaction_count,
                    SUM(t.amount) as total_amount
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                JOIN Payees p ON t.payee_id = p.payee_id
                WHERE a.customer_id = %s
                GROUP BY p.payee_id
                ORDER BY transaction_count DESC
                LIMIT 5
            """, (customer_id,))
            
            frequent_payees = []
            for payee_name, tx_count, total_amount in cursor.fetchall():
                frequent_payees.append({
                    "payee_name": payee_name,
                    "transaction_count": int(tx_count or 0),
                    "total_amount": float(total_amount or 0)
                })
            
            # Largest transactions
            cursor.execute("""
                SELECT 
                    t.amount,
                    t.transaction_type,
                    t.transaction_date,
                    t.description,
                    p.payee_name
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                LEFT JOIN Payees p ON t.payee_id = p.payee_id
                WHERE a.customer_id = %s
                AND t.transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 3 MONTH)
                ORDER BY t.amount DESC
                LIMIT 3
            """, (customer_id,))
            
            largest_transactions = []
            for amount, tx_type, tx_date, description, payee in cursor.fetchall():
                largest_transactions.append({
                    "amount": float(amount or 0),
                    "type": tx_type,
                    "date": tx_date.strftime("%Y-%m-%d %H:%M:%S") if tx_date else None,
                    "description": description,
                    "payee": payee
                })
            
            # Monthly transaction history
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(transaction_date, '%Y-%m') as month,
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_amount
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
                AND t.transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH)
                GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
                ORDER BY month DESC
            """, (customer_id,))
            
            monthly_history = {}
            for month, count, total in cursor.fetchall():
                monthly_history[month] = {
                    "transaction_count": int(count or 0),
                    "total_amount": float(total or 0)
                }
            
            # Pending transactions
            cursor.execute("""
                SELECT COUNT(*), SUM(amount)
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s AND t.status = 'Pending'
            """, (customer_id,))
            pending_data = cursor.fetchone()
            
            transaction_summary = {
                "total_transactions": int(total_tx_data[0] or 0),
                "last_month_transactions": int(monthly_tx_data[0] or 0),
                "average_transaction": float(monthly_tx_data[1] or 0),
                "transaction_types": transaction_types,
                "frequent_payees": frequent_payees,
                "largest_transactions": {
                    "time_period": "Last 3 months",
                    "transactions": largest_transactions
                },
                "monthly_history": monthly_history,
                "pending_transactions": {
                    "count": int(pending_data[0] or 0),
                    "total_amount": float(pending_data[1] or 0) if pending_data[1] else 0
                }
            }
            
            # 3. Spending patterns (using enhanced categorization)
            cursor.execute("""
                SELECT 
                    description, 
                    SUM(amount) as total_spent,
                    COUNT(*) as transaction_count
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
                AND t.transaction_type IN ('Withdrawal', 'Payment')
                AND t.transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 3 MONTH)
                GROUP BY description
                ORDER BY total_spent DESC
                LIMIT 20
            """, (customer_id,))
            spending_items = cursor.fetchall()
            
            # Calculate monthly average spending
            cursor.execute("""
                SELECT AVG(monthly_total) as monthly_avg
                FROM (
                    SELECT 
                        DATE_FORMAT(transaction_date, '%Y-%m') as month,
                        SUM(amount) as monthly_total
                    FROM Transactions t
                    JOIN Accounts a ON t.account_id = a.account_id
                    WHERE a.customer_id = %s
                    AND t.transaction_type IN ('Withdrawal', 'Payment')
                    AND t.transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH)
                    GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
                ) as monthly_spending
            """, (customer_id,))
            monthly_avg_data = cursor.fetchone()
            
            # Monthly spending breakdown
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(transaction_date, '%Y-%m') as month,
                    SUM(amount) as total_spent
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
                AND t.transaction_type IN ('Withdrawal', 'Payment')
                AND t.transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH)
                GROUP BY month
                ORDER BY month DESC
            """, (customer_id,))
            
            monthly_spending = {}
            for month, total in cursor.fetchall():
                monthly_spending[month] = float(total or 0)
            
            # Extract categories and calculate amounts
            category_spending = {}
            top_categories = []
            
            for item in spending_items:
                description = item[0].lower() if item[0] else ""
                amount = float(item[1] or 0)
                count = int(item[2] or 0)
                
                # Simple keyword-based categorization
                category = None
                if any(food_term in description for food_term in ['restaurant', 'cafe', 'food', 'grocery']):
                    category = 'Food'
                elif any(shop_term in description for shop_term in ['shop', 'store', 'mall', 'market']):
                    category = 'Shopping'
                elif any(bill_term in description for bill_term in ['bill', 'utility', 'electric', 'water', 'gas']):
                    category = 'Bills'
                elif any(ent_term in description for ent_term in ['movie', 'theatre', 'concert', 'game']):
                    category = 'Entertainment'
                elif any(trans_term in description for trans_term in ['uber', 'lyft', 'taxi', 'transport', 'bus', 'train']):
                    category = 'Transport'
                else:
                    category = 'Other'
                
                if category in category_spending:
                    category_spending[category]["amount"] += amount
                    category_spending[category]["transaction_count"] += count
                else:
                    category_spending[category] = {
                        "amount": amount,
                        "transaction_count": count
                    }
                
                if category not in top_categories:
                    top_categories.append(category)
                    if len(top_categories) >= 3:
                        break
            
            # Calculate spending trend (compare last month to previous month)
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(transaction_date, '%Y-%m') as month,
                    SUM(amount) as monthly_total
                FROM Transactions t
                JOIN Accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
                AND t.transaction_type IN ('Withdrawal', 'Payment')
                AND t.transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 2 MONTH)
                GROUP BY month
                ORDER BY month DESC
                LIMIT 2
            """, (customer_id,))
            
            trend_data = cursor.fetchall()
            spending_trend = None
            
            if len(trend_data) == 2:
                current_month = float(trend_data[0][1] or 0)
                previous_month = float(trend_data[1][1] or 0)
                if previous_month > 0:
                    percent_change = ((current_month - previous_month) / previous_month) * 100
                    spending_trend = {
                        "current_month": current_month,
                        "previous_month": previous_month,
                        "percent_change": percent_change,
                        "is_increasing": percent_change > 0
                    }
            
            spending_patterns = {
                "top_categories": top_categories,
                "monthly_average": float(monthly_avg_data[0] or 0),
                "category_breakdown": category_spending,
                "monthly_spending": monthly_spending,
                "spending_trend": spending_trend
            }
            
            # 4. Credit summary with detailed breakdown
            cursor.execute("""
                SELECT 
                    c.credit_score,
                    SUM(a.balance) as total_outstanding,
                    SUM(a.credit_limit) as total_credit_limit
                FROM Accounts a
                JOIN Customers c ON a.customer_id = c.customer_id
                WHERE a.customer_id = %s
                AND a.account_type IN ('Credit Card', 'Loan')
                AND a.credit_limit IS NOT NULL
            """, (customer_id,))
            credit_data = cursor.fetchone()
            
            # Get individual credit accounts
            cursor.execute("""
                SELECT 
                    a.account_id,
                    a.account_number,
                    a.account_type,
                    a.balance,
                    a.credit_limit,
                    a.due_date,
                    a.interest_rate
                FROM Accounts a
                WHERE a.customer_id = %s
                AND a.account_type IN ('Credit Card', 'Loan')
                AND a.credit_limit IS NOT NULL
            """, (customer_id,))
            
            credit_accounts = []
            for (acc_id, acc_number, acc_type, balance, limit, due_date, interest_rate) in cursor.fetchall():
                # Try to get credit card details if this is a credit card account
                card_details = None
                if acc_type == 'Credit Card':
                    cursor.execute("""
                        SELECT card_type, card_number, expiry_date, monthly_limit, card_status
                        FROM Credit_Cards
                        WHERE account_id = %s
                    """, (acc_id,))
                    card_result = cursor.fetchone()
                    if card_result:
                        card_details = {
                            "card_type": card_result[0],
                            "card_number_last4": card_result[1][-4:] if card_result[1] else None,
                            "expiry_date": card_result[2].strftime("%Y-%m-%d") if card_result[2] else None,
                            "monthly_limit": float(card_result[3] or 0) if card_result[3] else None,
                            "status": card_result[4]
                        }
                
                # Calculate utilization for this account
                utilization = None
                if limit and limit > 0:
                    utilization = (float(balance or 0) / float(limit)) * 100
                
                credit_accounts.append({
                    "account_id": acc_id,
                    "account_number": acc_number,
                    "account_type": acc_type,
                    "balance": float(balance or 0),
                    "credit_limit": float(limit or 0),
                    "available_credit": float(limit or 0) - float(balance or 0),
                    "utilization_percentage": utilization,
                    "due_date": due_date.strftime("%Y-%m-%d") if due_date else None,
                    "interest_rate": float(interest_rate or 0) if interest_rate else None,
                    "card_details": card_details
                })
            
            # Calculate overall utilization
            overall_utilization = None
            if credit_data[2] and credit_data[2] > 0:
                overall_utilization = (float(credit_data[1] or 0) / float(credit_data[2] or 0)) * 100
            
            credit_summary = {
                "credit_score": int(credit_data[0] or 0),
                "total_outstanding": float(credit_data[1] or 0),
                "total_credit_limit": float(credit_data[2] or 0),
                "available_credit": float(credit_data[2] or 0) - float(credit_data[1] or 0),
                "credit_utilization_percentage": overall_utilization,
                "credit_accounts": credit_accounts
            }
            
            # 5. Bills summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_bills,
                    COUNT(CASE WHEN b.status = 'Pending' THEN 1 END) as pending_bills,
                    COUNT(CASE WHEN b.status = 'Overdue' THEN 1 END) as overdue_bills,
                    SUM(CASE WHEN b.status = 'Pending' THEN amount ELSE 0 END) as pending_amount,
                    SUM(CASE WHEN b.status = 'Overdue' THEN amount ELSE 0 END) as overdue_amount
                FROM Bills b
                JOIN Accounts a ON b.account_id = a.account_id
                WHERE a.customer_id = %s
            """, (customer_id,))
            bills_summary_data = cursor.fetchone()
            
            # Get upcoming bills
            cursor.execute("""
                SELECT 
                    bill_id,
                    bill_name,
                    amount,
                    b.currency,
                    b.bill_date,
                    b.due_date,
                    b.status,
                    recurring,
                    recurrence_period
                FROM Bills b
                JOIN Accounts a ON b.account_id = a.account_id
                WHERE a.customer_id = %s
                AND b.status = 'Pending'
                ORDER BY b.due_date ASC
                LIMIT 5
            """, (customer_id,))
            
            upcoming_bills = []
            for (bill_id, name, amount, currency, bill_date, due_date, 
                 status, recurring, recurrence_period) in cursor.fetchall():
                upcoming_bills.append({
                    "bill_id": bill_id,
                    "name": name,
                    "amount": float(amount or 0),
                    "currency": currency,
                    "bill_date": bill_date.strftime("%Y-%m-%d") if bill_date else None,
                    "due_date": due_date.strftime("%Y-%m-%d") if due_date else None,
                    "status": status,
                    "recurring": bool(recurring),
                    "recurrence_period": recurrence_period
                })
            
            # Get overdue bills
            cursor.execute("""
                SELECT 
                    bill_id,
                    bill_name,
                    amount,
                    b.currency,
                    b.bill_date,
                    b.due_date,
                    recurring
                FROM Bills b
                JOIN Accounts a ON b.account_id = a.account_id
                WHERE a.customer_id = %s
                AND b.status = 'Overdue'
                ORDER BY b.due_date ASC
            """, (customer_id,))
            
            overdue_bills = []
            for (bill_id, name, amount, currency, bill_date, due_date, recurring) in cursor.fetchall():
                overdue_bills.append({
                    "bill_id": bill_id,
                    "name": name,
                    "amount": float(amount or 0),
                    "currency": currency,
                    "bill_date": bill_date.strftime("%Y-%m-%d") if bill_date else None,
                    "due_date": due_date.strftime("%Y-%m-%d") if due_date else None,
                    "recurring": bool(recurring)
                })
            
            # Get recurring bills
            cursor.execute("""
                SELECT 
                    COUNT(*) as recurring_count,
                    SUM(amount) as recurring_total
                FROM Bills b
                JOIN Accounts a ON b.account_id = a.account_id
                WHERE a.customer_id = %s
                AND recurring = 1
            """, (customer_id,))
            recurring_data = cursor.fetchone()
            
            bills_summary = {
                "total_bills": int(bills_summary_data[0] or 0),
                "pending_bills": {
                    "count": int(bills_summary_data[1] or 0),
                    "total_amount": float(bills_summary_data[3] or 0)
                },
                "overdue_bills": {
                    "count": int(bills_summary_data[2] or 0),
                    "total_amount": float(bills_summary_data[4] or 0)
                },
                "recurring_bills": {
                    "count": int(recurring_data[0] or 0),
                    "total_amount": float(recurring_data[1] or 0) if recurring_data[1] else 0
                },
                "upcoming_bills": upcoming_bills,
                "overdue_bills_details": overdue_bills
            }
            
            # Insert the compiled summary
            cursor.execute("""
                INSERT INTO Customer_Summary 
                (customer_id, account_summary, transaction_summary, 
                 spending_patterns, credit_summary, bills_summary)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                account_summary = VALUES(account_summary),
                transaction_summary = VALUES(transaction_summary),
                spending_patterns = VALUES(spending_patterns),
                credit_summary = VALUES(credit_summary),
                bills_summary = VALUES(bills_summary),
                last_updated = CURRENT_TIMESTAMP
            """, (customer_id, json.dumps(account_summary), json.dumps(transaction_summary),
                  json.dumps(spending_patterns), json.dumps(credit_summary), json.dumps(bills_summary)))
        
        conn.commit()
        print("Created comprehensive customer summaries using actual database data")
    except mysql.connector.Error as err:
        print(f"Error creating customer summaries: {err}")
        conn.rollback()
        raise

def main():
    conn = None
    try:
        print("Starting mock data generation...")
        conn = get_db_connection()
        print("Connected to the database")
        # Create mock data in order of dependencies
        print("Generating customers with unique 6-digit MPINs...")
        create_mock_customers(conn)
        print("Generating accounts...")
        create_mock_accounts(conn)
        print("Generating payees...")
        create_mock_payees(conn)
        print("Generating transactions...")
        create_mock_transactions(conn)
        print("Generating credit cards...")
        create_mock_credit_cards(conn)
        print("Generating bills...")
        create_mock_bills(conn)
        print("Generating customer summaries...")
        create_mock_customer_summaries(conn)
        
        print("Mock data generation completed successfully!")
        
    except Exception as e:
        print(f"Error generating mock data: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    main()
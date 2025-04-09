import mysql.connector
from faker import Faker
import random
from datetime import datetime, timedelta
import json
import os

# Initialize Faker
fake = Faker()

import mysql.connector
# Database connection
def get_db_connection():
    try:
        print("Connecting to database...")
        conn = mysql.connector.connect(
            host="localhost",
            user="root", 
            password="Mazhar321",
            database="BankDB",
            use_pure=True
        )
        print("Successfully connected to database")
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        print(f"Please check:")
        print("1. MySQL server is running")
        print("2. Database 'BankDB' exists")
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
            customer_since = fake.date_between(start_date='-5y', end_date='today')
            # Generate 6-digit mpin by padding customer index with leading zeros
            mpin = str(i).zfill(6)
            
            cursor.execute("""
                INSERT INTO Customers 
                (first_name, last_name, dob, phone_number, email, address, credit_score, customer_since, mpin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (first_name, last_name, dob, phone, email, address, credit_score, customer_since, mpin))
        
        conn.commit()
        print(f"Created {num_customers} customers with unique 6-digit MPINs")
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
        
        for customer_id in customer_ids:
            for _ in range(random.randint(1, num_accounts_per_customer)):
                account_type = random.choice(account_types)
                account_number = fake.bban()
                balance = round(random.uniform(100, 100000), 2)
                currency = random.choice(currencies)
                status = random.choice(['Active', 'Inactive', 'Closed', 'Frozen'])
                
                # Credit-related fields
                credit_limit = round(random.uniform(1000, 50000), 2) if account_type == 'Credit Card' else None
                due_date = fake.date_between(start_date='today', end_date='+30d') if account_type in ['Credit Card', 'Loan'] else None
                interest_rate = round(random.uniform(0.5, 15.0), 2) if account_type in ['Loan', 'Credit Card'] else None
                
                cursor.execute("""
                    INSERT INTO Accounts 
                    (customer_id, account_type, account_number, balance, currency, status, 
                     interest_rate, credit_limit, due_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (customer_id, account_type, account_number, balance, currency, status, 
                      interest_rate, credit_limit, due_date))
        
        conn.commit()
        print("Created accounts for all customers")
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
            # Generate mock JSON summaries
            account_summary = {
                "total_balance": round(random.uniform(1000, 100000), 2),
                "active_accounts": random.randint(1, 4),
                "account_types": random.sample(['Savings', 'Checking', 'Loan', 'Credit Card'], random.randint(1, 4))
            }
            
            transaction_summary = {
                "total_transactions": random.randint(10, 100),
                "last_month_transactions": random.randint(1, 20),
                "average_transaction": round(random.uniform(50, 500), 2)
            }
            
            spending_patterns = {
                "top_categories": random.sample(['Food', 'Shopping', 'Bills', 'Entertainment', 'Transport'], 3),
                "monthly_average": round(random.uniform(500, 5000), 2)
            }
            
            credit_summary = {
                "credit_score": random.randint(300, 850),
                "credit_utilization": round(random.uniform(0, 0.8), 2),
                "total_credit_limit": round(random.uniform(1000, 50000), 2)
            }
            
            cursor.execute("""
                INSERT INTO Customer_Summary 
                (customer_id, account_summary, transaction_summary, 
                 spending_patterns, credit_summary)
                VALUES (%s, %s, %s, %s, %s)
            """, (customer_id, json.dumps(account_summary), json.dumps(transaction_summary),
                  json.dumps(spending_patterns), json.dumps(credit_summary)))
        
        conn.commit()
        print("Created customer summaries")
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
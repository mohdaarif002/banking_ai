from db_utils import MySQLDatabase

def example_fetch_one():
    """Example of fetching a single row"""
    db = MySQLDatabase()
    
    # Query to get a single customer by ID
    query = "SELECT * FROM Customers WHERE customer_id = %s"
    result = db.fetch_one(query, (1,))
    
    if result:
        print(f"Customer found: {result}")
    else:
        print("Customer not found")
    
    db.disconnect()

def example_fetch_all():
    """Example of fetching multiple rows"""
    db = MySQLDatabase()
    
    # Query to get all accounts for a customer
    query = "SELECT * FROM Accounts WHERE customer_id = %s"
    results = db.fetch_all(query, (1,))
    
    if results:
        print(f"Found {len(results)} accounts:")
        for account in results:
            print(account)
    else:
        print("No accounts found")
    
    db.disconnect()

def example_fetch_dict():
    """Example of fetching a single row as dictionary"""
    db = MySQLDatabase()
    
    # Query to get transaction details
    query = "SELECT * FROM Transactions WHERE transaction_id = %s"
    result = db.fetch_dict(query, (101,))
    
    if result:
        # Now we can access fields by name
        print(f"Transaction amount: {result['amount']}")
        print(f"Transaction date: {result['transaction_date']}")
    else:
        print("Transaction not found")
    
    db.disconnect()

def example_fetch_all_dict():
    """Example of fetching multiple rows as dictionaries"""
    db = MySQLDatabase()
    
    # Query to get recent transactions for an account
    query = """
    SELECT * FROM Transactions 
    WHERE account_id = %s 
    ORDER BY transaction_date DESC 
    LIMIT 5
    """
    results = db.fetch_all_dict(query, (1001,))
    
    if results:
        print(f"Found {len(results)} recent transactions:")
        for transaction in results:
            print(f"Date: {transaction['transaction_date']}, "
                  f"Type: {transaction['transaction_type']}, "
                  f"Amount: {transaction['amount']}")
    else:
        print("No transactions found")
    
    db.disconnect()

def example_execute_query():
    """Example of executing an insert/update query"""
    db = MySQLDatabase()
    
    # Update a customer's phone number
    query = """
    UPDATE Customers 
    SET phone_number = %s 
    WHERE customer_id = %s
    """
    success = db.execute_query(query, ("555-123-4567", 1))
    
    if success:
        print("Customer phone number updated successfully")
    else:
        print("Failed to update customer phone number")
    
    db.disconnect()

def example_with_context_manager():
    """Example using the context manager (with statement)"""
    # Database connection is automatically opened and closed
    with MySQLDatabase() as db:
        query = "SELECT COUNT(*) FROM Customers"
        result = db.fetch_one(query)
        if result:
            print(f"Total customers: {result[0]}")

def main():
    print("=== Database Abstraction Examples ===")
    
    print("\n1. Fetch One Row Example:")
    example_fetch_one()
    
    print("\n2. Fetch All Rows Example:")
    example_fetch_all()
    
    print("\n3. Fetch Dictionary Example:")
    example_fetch_dict()
    
    print("\n4. Fetch All Dictionaries Example:")
    example_fetch_all_dict()
    
    print("\n5. Execute Query Example:")
    example_execute_query()
    
    print("\n6. With Context Manager Example:")
    example_with_context_manager()

if __name__ == "__main__":
    main() 
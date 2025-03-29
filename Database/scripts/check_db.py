import os
import sqlite3
import pandas as pd

# Connect to the database
DB_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "BankDB.db"
)
conn = sqlite3.connect(DB_FILE)

# Check table names
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in the database:")
for table in tables:
    print(f"- {table[0]}")
print("\n" + "-"*50 + "\n")

# Sample data from each table
for table in tables:
    table_name = table[0]
    print(f"Sample data from {table_name}:")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
    columns = [desc[0] for desc in cursor.description]
    print(f"Columns: {', '.join(columns)}")
    
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    print("\n" + "-"*50 + "\n")

# Example query: Find total transaction amount by category
print("Transaction amounts by category:")
query = """
SELECT tc.category_name, COUNT(t.transaction_id) as count, 
       SUM(t.amount) as total_amount
FROM transactions t
JOIN transaction_categories tc ON t.category_id = tc.category_id
WHERE t.status = 'Completed'
GROUP BY tc.category_name
ORDER BY total_amount DESC;
"""
cursor.execute(query)
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} transactions, total: ${row[2]:.2f}")

# Example query: Credit cards with benefits
print("\n" + "-"*50 + "\n")
print("Credit cards with benefits:")
query = """
SELECT cc.card_id, cc.card_type, b.benefit_name
FROM credit_cards cc
JOIN card_benefits cb ON cc.card_id = cb.card_id
JOIN benefits b ON cb.benefit_id = b.benefit_id
WHERE cb.status = 'Active'
LIMIT 10;
"""
cursor.execute(query)
for row in cursor.fetchall():
    print(f"Card ID {row[0]} ({row[1]}): {row[2]}")

# Close the connection
conn.close() 
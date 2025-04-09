import mysql.connector
import pandas as pd
from tabulate import tabulate
from datetime import datetime
import os

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mazhar321",
        database="BankDB",
        use_pure=True
    )

def get_all_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    conn.close()
    return tables

def get_top_rows(table_name, limit=10):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        rows = []
    conn.close()
    return rows

def main():
    # Create output directory if it doesn't exist
    output_dir = "database_reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_filename = f"{output_dir}/database_report_{timestamp}.md"
    
    print("Connecting to MySQL database...")
    tables = get_all_tables()
    print(f"Found {len(tables)} tables")
    
    # Open markdown file for writing
    with open(md_filename, 'w') as md_file:
        # Write header
        md_file.write(f"# Database Report - BankDB\n\n")
        md_file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        md_file.write(f"Total tables: {len(tables)}\n\n")
        
        # Write table of contents
        md_file.write("## Table of Contents\n\n")
        for i, table in enumerate(tables, 1):
            md_file.write(f"{i}. [{table}](#{table.lower()})\n")
        md_file.write("\n---\n\n")
        
        # Process each table
        for i, table in enumerate(tables, 1):
            print(f"\nProcessing {i}/{len(tables)}: Table {table}")
            
            # Write table header to markdown
            md_file.write(f"## {i}. {table} {{{table.lower()}}}\n\n")
            
            rows = get_top_rows(table)
            if rows:
                # Convert to DataFrame
                df = pd.DataFrame(rows)
                
                # Display in console
                console_output = tabulate(df, headers=df.columns, tablefmt="psql")
                print(console_output)
                
                # Write to markdown file with github-flavored markdown table format
                md_table = tabulate(df, headers=df.columns, tablefmt="github")
                md_file.write(md_table)
                md_file.write(f"\n\n*Showing top 10 rows from {table}*\n\n")
            else:
                msg = "No data in this table"
                print(msg)
                md_file.write(f"*{msg}*\n\n")
            
            md_file.write("---\n\n")
            print("-" * 80)
    
    print(f"\nMarkdown report saved to: {md_filename}")

if __name__ == "__main__":
    main() 
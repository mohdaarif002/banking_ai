import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple, Union
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MySQLDatabase:
    """
    A class to handle MySQL database connections and operations
    """
    
    def __init__(self, 
                 host: str = os.getenv("DB_HOST", "localhost"),
                 user: str = os.getenv("DB_USER", "root"),
                 password: str = os.getenv("DB_PASSWORD", ""), 
                 database: str = os.getenv("DB_NAME", "BankDB")):
        """
        Initialize database connection parameters
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None
    
    def connect(self) -> bool:
        """
        Establish connection to the MySQL database
        Returns True if successful, False otherwise
        """
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                use_pure=True
            )
            self.cursor = self.conn.cursor()
            return True
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            return False
    
    def disconnect(self) -> None:
        """
        Close the database connection
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query: str, params: Tuple = ()) -> bool:
        """
        Execute a query without returning results (INSERT, UPDATE, DELETE)
        Returns True if successful, False otherwise
        """
        success = False
        try:
            if not self.conn or not self.conn.is_connected():
                self.connect()
                
            self.cursor.execute(query, params)
            self.conn.commit()
            success = True
        except Error as e:
            print(f"Error executing query: {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            return success
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Tuple]:
        """
        Execute a query and fetch one result
        Returns a single row or None if no results or error
        """
        try:
            if not self.conn or not self.conn.is_connected():
                self.connect()
                
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
    
    def fetch_all(self, query: str, params: Tuple = ()) -> Optional[List[Tuple]]:
        """
        Execute a query and fetch all results
        Returns list of rows or None if no results or error
        """
        try:
            if not self.conn or not self.conn.is_connected():
                self.connect()
                
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
    
    def fetch_dict(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """
        Execute a query and fetch one result as dictionary
        Returns a single row as dict or None if no results or error
        """
        try:
            if not self.conn or not self.conn.is_connected():
                self.connect()
                
            # Use dictionary cursor
            dict_cursor = self.conn.cursor(dictionary=True)
            dict_cursor.execute(query, params)
            result = dict_cursor.fetchone()
            dict_cursor.close()
            return result
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
    
    def fetch_all_dict(self, query: str, params: Tuple = ()) -> Optional[List[Dict]]:
        """
        Execute a query and fetch all results as dictionaries
        Returns list of dictionaries or None if no results or error
        """
        try:
            if not self.conn or not self.conn.is_connected():
                self.connect()
                
            # Use dictionary cursor
            dict_cursor = self.conn.cursor(dictionary=True)
            dict_cursor.execute(query, params)
            result = dict_cursor.fetchall()
            dict_cursor.close()
            return result
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
            
    def __enter__(self):
        """
        Support for with statement - connects to database
        """
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Support for with statement - disconnects from database
        """
        self.disconnect() 
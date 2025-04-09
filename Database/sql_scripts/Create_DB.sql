-- Create and select the database
CREATE DATABASE IF NOT EXISTS BankDB;
USE BankDB;

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS Customer_Summary;
DROP TABLE IF EXISTS Card_Benefits;
DROP TABLE IF EXISTS Bills;
DROP TABLE IF EXISTS Credit_Cards;
DROP TABLE IF EXISTS Transaction_Tags;
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Account_Benefits;
DROP TABLE IF EXISTS Accounts;
DROP TABLE IF EXISTS Benefits;
DROP TABLE IF EXISTS Merchants;
DROP TABLE IF EXISTS Transaction_Categories;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Payees;
DROP TABLE IF EXISTS Customers;

-- 1. Customers Table
CREATE TABLE Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    phone_number VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    address TEXT NOT NULL,
    credit_score INT,
    customer_since DATE NOT NULL,
    mpin VARCHAR(6) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -- 2. Users Table (Bank Employees)
-- CREATE TABLE Users (
--     user_id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(50) NOT NULL UNIQUE,
--     password_hash VARCHAR(255) NOT NULL,
--     role ENUM('Admin', 'Teller', 'CustomerService') NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- -- 3. Transaction Categories
-- CREATE TABLE Transaction_Categories (
--     category_id INT AUTO_INCREMENT PRIMARY KEY,
--     category_name VARCHAR(50) NOT NULL UNIQUE,
--     description TEXT
-- );

-- -- 4. Merchants Table
-- CREATE TABLE Merchants (
--     merchant_id INT AUTO_INCREMENT PRIMARY KEY,
--     merchant_name VARCHAR(100) NOT NULL,
--     category VARCHAR(50) NOT NULL,
--     location VARCHAR(200)
-- );

-- -- 5. Benefits Table
-- CREATE TABLE Benefits (
--     benefit_id INT AUTO_INCREMENT PRIMARY KEY,
--     benefit_name VARCHAR(100) NOT NULL,
--     description TEXT NOT NULL
-- );

-- 6. Accounts Table
CREATE TABLE Accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    account_type ENUM('Savings', 'Current', 'Loan', 'Credit Card') NOT NULL,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    balance DECIMAL(15, 2) DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL,
    status ENUM('Active', 'Inactive', 'Closed', 'Frozen') DEFAULT 'Active',
    interest_rate DECIMAL(5, 2),
    -- Credit-related fields (applicable to Credit Card and Loan accounts)
    credit_limit DECIMAL(15, 2),
    due_date DATE, -- Payment due date (applicable to Credit Card and Loan accounts)
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers (customer_id) ON DELETE CASCADE
);

-- -- 7. Account Benefits Table (Many-to-Many Relationship)
-- CREATE TABLE Account_Benefits (
--     account_id INT NOT NULL,
--     benefit_id INT NOT NULL,
--     activation_date DATE NOT NULL,
--     expiry_date DATE,
--     status ENUM('Active', 'Inactive', 'Expired') DEFAULT 'Active',
--     PRIMARY KEY (account_id, benefit_id),
--     FOREIGN KEY (account_id) REFERENCES Accounts (account_id) ON DELETE CASCADE,
--     FOREIGN KEY (benefit_id) REFERENCES Benefits (benefit_id) ON DELETE CASCADE
-- );

-- 8. Payees Table
CREATE TABLE Payees (
    payee_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    payee_name VARCHAR(100) NOT NULL,
    payee_type ENUM('Merchant', 'Individual', 'Business', 'Bill', 'International') NOT NULL,
    -- For bank transfers
    account_number VARCHAR(20),
    -- routing_number VARCHAR(20), --  Bank routing number (Applicable for US)
    bank_name VARCHAR(100),
    -- For merchants
    merchant_id INT,
    -- Contact information
    email VARCHAR(100),
    phone VARCHAR(15),
    address TEXT,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers (customer_id) ON DELETE CASCADE
    -- FOREIGN KEY (merchant_id) REFERENCES Merchants (merchant_id) ON DELETE SET NULL
);

-- 9. Transactions Table
CREATE TABLE Transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    transaction_type ENUM('Deposit', 'Withdrawal', 'Transfer', 'Payment') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pending', 'Completed', 'Failed', 'Reversed') DEFAULT 'Completed',
    description TEXT,
    payee_id INT,
    category_id INT,
    FOREIGN KEY (account_id) REFERENCES Accounts (account_id) ON DELETE CASCADE,
    FOREIGN KEY (payee_id) REFERENCES Payees (payee_id) ON DELETE SET NULL
    -- FOREIGN KEY (category_id) REFERENCES Transaction_Categories (category_id) ON DELETE SET NULL
);

-- -- 10. Transaction Tags (for machine learning and customer analysis)
-- CREATE TABLE Transaction_Tags (
--     transaction_id INT NOT NULL,
--     tag VARCHAR(50) NOT NULL,
--     PRIMARY KEY (transaction_id, tag),
--     FOREIGN KEY (transaction_id) REFERENCES Transactions (transaction_id) ON DELETE CASCADE
-- );

-- 11. Credit Cards Table
CREATE TABLE Credit_Cards (
    card_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    card_number VARCHAR(16) NOT NULL UNIQUE,
    card_type ENUM('Visa', 'MasterCard', 'Amex', 'Discover') NOT NULL,
    expiry_date DATE NOT NULL,
    cvv VARCHAR(4) NOT NULL,
    card_status ENUM('Active', 'Blocked', 'Expired') DEFAULT 'Active',
    issued_date DATE NOT NULL,
    monthly_limit DECIMAL(15, 5),
    FOREIGN KEY (account_id) REFERENCES Accounts (account_id) ON DELETE CASCADE
);

-- -- 12. Card Benefits Junction Table (Many-to-Many)
-- CREATE TABLE Card_Benefits (
--     card_id INT NOT NULL,
--     benefit_id INT NOT NULL,
--     activation_date DATE NOT NULL,
--     expiry_date DATE,
--     status ENUM('Active', 'Inactive', 'Expired') DEFAULT 'Active',
--     PRIMARY KEY (card_id, benefit_id),
--     FOREIGN KEY (card_id) REFERENCES Credit_Cards (card_id) ON DELETE CASCADE,
--     FOREIGN KEY (benefit_id) REFERENCES Benefits (benefit_id) ON DELETE CASCADE
-- );

-- 13. Bills Table
CREATE TABLE Bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    merchant_id INT NOT NULL,
    bill_name VARCHAR(100) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    bill_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('Pending', 'Paid', 'Overdue', 'Cancelled') DEFAULT 'Pending',
    recurring BOOLEAN DEFAULT FALSE,
    recurrence_period ENUM('Weekly', 'Monthly', 'Quarterly', 'Annually'),
    FOREIGN KEY (account_id) REFERENCES Accounts (account_id) ON DELETE CASCADE
    -- FOREIGN KEY (merchant_id) REFERENCES Merchants (merchant_id) ON DELETE CASCADE
);

-- 14. Customer Summary Table (for AI quick responses)
CREATE TABLE Customer_Summary (
    customer_id INT PRIMARY KEY,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    account_summary JSON,
    transaction_summary JSON,
    benefits_summary JSON,
    bills_summary JSON,
    spending_patterns JSON,
    credit_summary JSON,
    FOREIGN KEY (customer_id) REFERENCES Customers (customer_id) ON DELETE CASCADE
);

-- Create Indices for better performance
CREATE INDEX idx_customers_email ON Customers(email);
CREATE INDEX idx_accounts_customer ON Accounts(customer_id);
CREATE INDEX idx_transactions_account ON Transactions(account_id);
-- CREATE INDEX idx_transactions_merchant ON Transactions(merchant_id);
-- CREATE INDEX idx_transactions_category ON Transactions(category_id);
CREATE INDEX idx_transactions_date ON Transactions(transaction_date);
CREATE INDEX idx_cards_account ON Credit_Cards(account_id);
CREATE INDEX idx_bills_account ON Bills(account_id);
CREATE INDEX idx_bills_due_date ON Bills(due_date); 
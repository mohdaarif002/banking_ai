-- Drop tables if they exist (in reverse order of dependencies)
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
DROP TABLE IF EXISTS Customers;

-- 1. Customers Table
CREATE TABLE Customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    phone_number VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    address TEXT NOT NULL,
    credit_score INTEGER,
    customer_since DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users Table (Bank Employees)
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR NOT NULL UNIQUE,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL CHECK (role IN ('Admin', 'Teller', 'CustomerService')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Transaction Categories
CREATE TABLE Transaction_Categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- 4. Merchants Table
CREATE TABLE Merchants (
    merchant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    location VARCHAR(200)
);

-- 5. Benefits Table
CREATE TABLE Benefits (
    benefit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    benefit_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL
);

-- 6. Accounts Table
CREATE TABLE Accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    account_type VARCHAR NOT NULL CHECK (account_type IN ('Savings', 'Checking', 'Loan', 'Credit Card')),
    account_number VARCHAR NOT NULL UNIQUE,
    balance NUMERIC(15, 2) DEFAULT 0.00,
    currency VARCHAR NOT NULL,
    status VARCHAR CHECK (status IN ('Active', 'Inactive', 'Closed', 'Frozen')) DEFAULT 'Active',
    interest_rate NUMERIC(5, 2),
    credit_limit NUMERIC(15, 2),
    due_date DATE,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers (customer_id) ON DELETE CASCADE
);

-- 7. Account Benefits Table (Many-to-Many Relationship)
CREATE TABLE Account_Benefits (
    account_id INTEGER NOT NULL,
    benefit_id INTEGER NOT NULL,
    activation_date DATE NOT NULL,
    expiry_date DATE,
    status VARCHAR CHECK (status IN ('Active', 'Inactive', 'Expired')) DEFAULT 'Active',
    PRIMARY KEY (account_id, benefit_id),
    FOREIGN KEY (account_id) REFERENCES Accounts (account_id) ON DELETE CASCADE,
    FOREIGN KEY (benefit_id) REFERENCES Benefits (benefit_id) ON DELETE CASCADE
);

-- 8. Transactions Table
CREATE TABLE Transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    transaction_type VARCHAR NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Payment')),
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR CHECK (status IN ('Pending', 'Completed', 'Failed', 'Reversed')) DEFAULT 'Completed',
    description TEXT,
    merchant_id INTEGER,
    category_id INTEGER,
    receiver_account_id INTEGER,
    FOREIGN KEY (account_id) REFERENCES Accounts (account_id) ON DELETE CASCADE,
    FOREIGN KEY (merchant_id) REFERENCES Merchants (merchant_id) ON DELETE SET NULL,
    FOREIGN KEY (category_id) REFERENCES Transaction_Categories (category_id) ON DELETE SET NULL,
    FOREIGN KEY (receiver_account_id) REFERENCES Accounts (account_id) ON DELETE SET NULL
);

-- 9. Transaction Tags (for machine learning and customer analysis)
CREATE TABLE Transaction_Tags (
    transaction_id INTEGER NOT NULL,
    tag VARCHAR(50) NOT NULL,
    PRIMARY KEY (transaction_id, tag),
    FOREIGN KEY (transaction_id) REFERENCES Transactions (transaction_id) ON DELETE CASCADE
);

-- 10. Credit Cards Table
CREATE TABLE Credit_Cards (
    card_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    card_number VARCHAR(16) NOT NULL UNIQUE,
    card_type VARCHAR NOT NULL CHECK (card_type IN ('Visa', 'MasterCard', 'Amex', 'Discover')),
    expiry_date DATE NOT NULL,
    cvv VARCHAR(4) NOT NULL,
    card_status VARCHAR CHECK (card_status IN ('Active', 'Blocked', 'Expired')) DEFAULT 'Active',
    issued_date DATE NOT NULL,
    monthly_limit NUMERIC(15, 2),
    FOREIGN KEY (account_id) REFERENCES Accounts (account_id) ON DELETE CASCADE
);

-- 11. Card Benefits Junction Table (Many-to-Many)
CREATE TABLE Card_Benefits (
    card_id INTEGER NOT NULL,
    benefit_id INTEGER NOT NULL,
    activation_date DATE NOT NULL,
    expiry_date DATE,
    status VARCHAR CHECK (status IN ('Active', 'Inactive', 'Expired')) DEFAULT 'Active',
    PRIMARY KEY (card_id, benefit_id),
    FOREIGN KEY (card_id) REFERENCES Credit_Cards (card_id) ON DELETE CASCADE,
    FOREIGN KEY (benefit_id) REFERENCES Benefits (benefit_id) ON DELETE CASCADE
);

-- 12. Bills Table
CREATE TABLE Bills (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    merchant_id INTEGER NOT NULL,
    bill_name VARCHAR(100) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR NOT NULL,
    bill_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR CHECK (status IN ('Pending', 'Paid', 'Overdue', 'Cancelled')) DEFAULT 'Pending',
    recurring BOOLEAN DEFAULT 0,
    recurrence_period VARCHAR CHECK (recurrence_period IN ('Weekly', 'Monthly', 'Quarterly', 'Annually')),
    FOREIGN KEY (account_id) REFERENCES Accounts (account_id) ON DELETE CASCADE,
    FOREIGN KEY (merchant_id) REFERENCES Merchants (merchant_id) ON DELETE CASCADE
);

-- Create Indices for better performance
CREATE INDEX idx_customers_email ON Customers(email);
CREATE INDEX idx_accounts_customer ON Accounts(customer_id);
CREATE INDEX idx_transactions_account ON Transactions(account_id);
CREATE INDEX idx_transactions_merchant ON Transactions(merchant_id);
CREATE INDEX idx_transactions_category ON Transactions(category_id);
CREATE INDEX idx_transactions_date ON Transactions(transaction_date);
CREATE INDEX idx_cards_account ON Credit_Cards(account_id);
CREATE INDEX idx_bills_account ON Bills(account_id);
CREATE INDEX idx_bills_due_date ON Bills(due_date); 
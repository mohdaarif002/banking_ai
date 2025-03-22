-- Drop tables if they exist
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS Accounts;
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Transfers;
DROP TABLE IF EXISTS Loans;
DROP TABLE IF EXISTS Cards;
DROP TABLE IF EXISTS Branches;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS TransactionLogs;
DROP TABLE IF EXISTS LoginAttempts;
DROP TABLE IF EXISTS SupportQueries;

-- 1. Customers Table
CREATE TABLE Customers (
    customer_id      INT AUTO_INCREMENT PRIMARY KEY,
    first_name       VARCHAR(100) NOT NULL,
    last_name        VARCHAR(100) NOT NULL,
    dob             DATE NOT NULL,
    phone_number     VARCHAR(15) UNIQUE NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    address         TEXT NOT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Accounts Table
CREATE TABLE Accounts (
    account_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id      INTEGER NOT NULL,
    account_type     TEXT CHECK(account_type IN ('Savings', 'Checking', 'Loan', 'Credit Card')) NOT NULL,
    account_number   TEXT UNIQUE NOT NULL,
    balance          DECIMAL(15,2) DEFAULT 0.00 CHECK (balance >= 0),
    currency         TEXT NOT NULL,
    status          TEXT CHECK(status IN ('Active', 'Inactive', 'Closed', 'Frozen')) DEFAULT 'Active',
    opened_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);

-- 3. Transactions Table
CREATE TABLE Transactions (
    transaction_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id       INTEGER NOT NULL,
    transaction_type TEXT CHECK(transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Payment')) NOT NULL,
    amount          DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    currency        TEXT NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status          TEXT CHECK(status IN ('Pending', 'Completed', 'Failed', 'Reversed')) DEFAULT 'Completed',
    description     TEXT,
    FOREIGN KEY (account_id) REFERENCES Accounts(account_id) ON DELETE CASCADE
);

-- 4. Transfers Table
CREATE TABLE Transfers (
    transfer_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    from_account_id  INTEGER NOT NULL,
    to_account_id    INTEGER NOT NULL,
    amount           DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    currency         TEXT NOT NULL,
    initiated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at     TIMESTAMP NULL,
    status          TEXT CHECK(status IN ('Pending', 'Completed', 'Failed')) DEFAULT 'Pending',
    FOREIGN KEY (from_account_id) REFERENCES Accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (to_account_id) REFERENCES Accounts(account_id) ON DELETE CASCADE
);

-- 5. Loans Table
CREATE TABLE Loans (
    loan_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,
    loan_type      TEXT CHECK(loan_type IN ('Personal', 'Home', 'Auto', 'Business')) NOT NULL,
    principal_amount DECIMAL(15,2) NOT NULL CHECK (principal_amount > 0),
    interest_rate   DECIMAL(5,2) NOT NULL CHECK (interest_rate >= 0),
    loan_term_months INTEGER NOT NULL CHECK (loan_term_months > 0),
    outstanding_balance DECIMAL(15,2) DEFAULT 0.00 CHECK (outstanding_balance >= 0),
    due_date        DATE NOT NULL,
    status         TEXT CHECK(status IN ('Active', 'Closed', 'Defaulted')) DEFAULT 'Active',
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);

-- 6. Cards Table (Combining Credit & Debit)
CREATE TABLE Cards (
    card_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,
    account_id      INTEGER NULL,
    card_number     TEXT UNIQUE NOT NULL,
    card_type      TEXT CHECK(card_type IN ('Debit', 'Credit')) NOT NULL,
    expiration_date DATE NOT NULL,
    cvv            TEXT NOT NULL,
    credit_limit    DECIMAL(15,2) NULL CHECK (credit_limit >= 0),
    outstanding_balance DECIMAL(15,2) NULL CHECK (outstanding_balance >= 0),
    status         TEXT CHECK(status IN ('Active', 'Blocked', 'Expired')) DEFAULT 'Active',
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);

-- 7. Bank Branches Table
CREATE TABLE Branches (
    branch_id       INT AUTO_INCREMENT PRIMARY KEY,
    branch_name     VARCHAR(100) NOT NULL,
    branch_address  TEXT NOT NULL,
    phone_number    VARCHAR(15) UNIQUE NOT NULL
);

-- 8. Users Table (For Bank Employees)
CREATE TABLE Users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT UNIQUE NOT NULL,
    password_hash  TEXT NOT NULL,
    role          TEXT CHECK(role IN ('Admin', 'Teller', 'CustomerService')) NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Transaction Logs Table (For Auditing)
CREATE TABLE TransactionLogs (
    log_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL,
    event_type    TEXT CHECK(event_type IN ('Debit', 'Credit', 'Chargeback')) NOT NULL,
    old_balance    DECIMAL(15,2) NOT NULL,
    new_balance    DECIMAL(15,2) NOT NULL,
    event_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id) ON DELETE CASCADE
);

-- 10. Login Attempts Table (For Security)
CREATE TABLE LoginAttempts (
    attempt_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    ip_address    VARCHAR(45) NOT NULL,
    success       BOOLEAN NOT NULL,
    attempt_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 11. Support Queries Table (For AI Assistant)
CREATE TABLE SupportQueries (
    query_id       INT AUTO_INCREMENT PRIMARY KEY,
    customer_id    INT NOT NULL,
    query_text    TEXT NOT NULL,
    bot_response  TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE ON UPDATE CASCADE
);
-- More table creation queries go here...

-- Create Indexes
CREATE INDEX idx_customers_email ON Customers(email);
CREATE INDEX idx_accounts_number ON Accounts(account_number);
CREATE INDEX idx_transactions_account ON Transactions(account_id);
CREATE INDEX idx_cards_number ON Cards(card_number);

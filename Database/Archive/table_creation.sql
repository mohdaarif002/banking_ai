
CREATE TABLE customers (
	customer_id INTEGER NOT NULL, 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100) NOT NULL, 
	dob DATE NOT NULL, 
	phone_number VARCHAR(15) NOT NULL, 
	email VARCHAR(100) NOT NULL, 
	address TEXT NOT NULL, 
	created_at TIMESTAMP, 
	PRIMARY KEY (customer_id), 
	UNIQUE (phone_number), 
	UNIQUE (email)
)



CREATE TABLE accounts (
	account_id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	account_type VARCHAR NOT NULL CHECK (account_type IN ('Savings', 'Checking', 'Loan', 'Credit Card')), 
	account_number VARCHAR NOT NULL, 
	balance NUMERIC(15, 2), 
	currency VARCHAR NOT NULL, 
	status VARCHAR CHECK (status IN ('Active', 'Inactive', 'Closed', 'Frozen')), 
	opened_at TIMESTAMP, 
	PRIMARY KEY (account_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (customer_id), 
	UNIQUE (account_number)
)



CREATE TABLE transactions (
	transaction_id INTEGER NOT NULL, 
	account_id INTEGER NOT NULL, 
	transaction_type VARCHAR NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Payment')), 
	amount NUMERIC(15, 2) NOT NULL, 
	currency VARCHAR NOT NULL, 
	transaction_date TIMESTAMP, 
	status VARCHAR CHECK (status IN ('Pending', 'Completed', 'Failed', 'Reversed')), 
	description TEXT, 
	PRIMARY KEY (transaction_id), 
	FOREIGN KEY(account_id) REFERENCES accounts (account_id)
)



CREATE TABLE users (
	user_id INTEGER NOT NULL, 
	username VARCHAR NOT NULL, 
	password_hash VARCHAR NOT NULL, 
	role VARCHAR NOT NULL CHECK (role IN ('Admin', 'Teller', 'CustomerService')), 
	created_at TIMESTAMP, 
	PRIMARY KEY (user_id), 
	UNIQUE (username)
)


import streamlit as st
import numpy as np
import os
import time
from datetime import datetime
from Database.db_utils import MySQLDatabase
from agent_utils.sql_agent import setup_generic_sql_agent, format_conversation_history, format_agent_output

from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

def authenticate_user():
    st.title("🏦 Welcome to CA-Bank")
    with st.form("auth_form"):
        customer_id = st.text_input("Enter Customer ID")
        mpin = st.text_input("Enter 6-digit MPIN", type="password", max_chars=6)
        submit = st.form_submit_button("Login")

        if submit:
            if len(mpin) == 6 and mpin.isdigit():
                # Use the database utility class
                with st.spinner("Connecting to database..."):
                    time.sleep(0.5)
                db = MySQLDatabase()
                # st.info("Connected to Database")
                query = "SELECT customer_id, first_name FROM Customers WHERE customer_id = %s"
                result = db.fetch_one(query, (customer_id,))
                print(result)
                # st.chat_message(result)
                if result:
                    customer_id, first_name = result
                    st.success(f"Welcome {first_name}!")
                    # Store user info in session state
                    st.session_state.user_info = {
                        "customer_id": customer_id,
                        "first_name": first_name
                    }
                    return True
                else:
                    st.error("Invalid Credentials")
                    return False
            else:
                st.error("Please enter a valid CustomerID or 6-digit MPIN")
                return False
    return False

def show_ai_bankbot():
    """Display the AI BankBot chat interface"""
    st.header("AI-BankBot")
    st.write("Ask me anything about your bank account")
    
    # Initialize chat history in session state if it doesn't exist
    # This checks if a "messages" list exists in Streamlit's session state
    # If it doesn't exist, creates an empty list to store chat history
    # Session state persists across reruns of the Streamlit app
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
        
    # Display chat messages
    # Iterates through all messages stored in the session state
    # Each message is a dict with "role" (user/assistant) and "content" (the message text)
    # st.chat_message creates a chat bubble UI component with the appropriate styling
    # st.markdown renders the message content with markdown formatting
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    prompt = st.chat_input("Ask me anything about your bank account")
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Display assistant response
        with st.chat_message("assistant"):
            response = f"Echo: {prompt}"  # Replace this with your actual AI response
            st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    

def show_account_summary():
    """Display the account summary tab"""
    st.header("Account Summary")
    st.write("Your account details will appear here")
    
    # Example account info
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Balance", "$2,540.00", "+$250.00")
        with col2:
            st.metric("Savings Goal", "75%", "+5%")

def show_transactions():
    """Display the transactions tab"""
    st.header("Recent Transactions")
    st.write("Your transaction history will appear here")
    
    # Example transactions
    transactions = [
        {"date": "2023-05-15", "description": "Grocery Store", "amount": "-$42.50"},
        {"date": "2023-05-14", "description": "Salary Deposit", "amount": "+$1,200.00"},
        {"date": "2023-05-10", "description": "Electric Bill", "amount": "-$85.20"}
    ]
    
    for t in transactions:
        with st.container():
            cols = st.columns([2, 4, 2])
            cols[0].write(t["date"])
            cols[1].write(t["description"])
            cols[2].write(t["amount"])
            st.divider()

def show_services():
    """Display the services tab"""
    st.header("Banking Services")
    st.write("Access our banking services")
    
    service_options = ["Transfer Money", "Pay Bills", "Apply for Loan", "Contact Support"]
    selected_service = st.selectbox("Select a service", service_options)
    
    if selected_service:
        st.write(f"You selected: {selected_service}")
        st.write("This feature will be implemented soon.")

def show_sql_agent():
    """Display the SQL Query interface"""
    st.header("DB SQL Query Interface")
    st.write("Ask any question about the database and get SQL insights")
    
    # Initialize chat history in session state if it doesn't exist
    if "sql_messages" not in st.session_state:
        st.session_state.sql_messages = []
    
    # Create a container for the chat messages
    chat_container = st.container()
    
    # Create a container for the input at the bottom
    input_container = st.container()
    
    # Display chat messages in the chat container
    with chat_container:
        for message in st.session_state.sql_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Add spacing to push the input to the bottom
    st.write("")  # Add empty space
    st.write("")  # Add more empty space
    
    # Place the input at the bottom
    with input_container:
        prompt = st.chat_input("Ask any question about the database...")
        if prompt:
            # Add user message to chat history
            st.session_state.sql_messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            try:
                # Initialize the SQL agent if not already in session state
                if "sql_agent" not in st.session_state:
                    st.session_state.sql_agent = setup_generic_sql_agent()
                
                # Format the conversation history
                conversation_history = format_conversation_history(st.session_state.sql_messages[:-1])
                
                # Create the prompt with conversation history
                full_prompt = f"""Previous conversation:
{conversation_history}

Current question: {prompt}"""
                
                # Get response from the SQL agent
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = st.session_state.sql_agent.invoke(full_prompt)
                        formatted_response = format_agent_output(response)
                        
                        # Display thought process in an expander
                        with st.expander("View Thought Process"):
                            if formatted_response['thought_process']:
                                st.markdown(formatted_response['thought_process'])
                            else:
                                st.info("No thought process available for this response.")
                        
                        # Display final answer
                        st.markdown(formatted_response['final_answer'])
                
                # Add assistant response to chat history
                st.session_state.sql_messages.append({
                    "role": "assistant", 
                    "content": formatted_response['final_answer']
                })
            
            except Exception as e:
                error_message = f"Error: {str(e)}"
                st.error(error_message)
                st.session_state.sql_messages.append({"role": "assistant", "content": error_message})
            
            # Rerun to update the display
            st.rerun()

def show_main_interface():
    """Display the main banking interface"""
    # Access user information
    user_info = st.session_state.user_info
    
    # Display header with user name
    st.title(f"Hello, {user_info['first_name']}! 👋")
    st.subheader("Welcome to MyBank Dashboard")
    
    # Add tabs for different banking functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["AI-BankBot",
                                      "Account Summary",
                                      "Transactions",
                                      "Services",
                                      "AI-DB-BankBot"])
    
    # Display content for each tab
    with tab1:
        show_ai_bankbot()
    
    with tab2:
        show_account_summary()
    
    with tab3:
        show_transactions()
    
    with tab4:
        show_services()
    
    with tab5:
        show_sql_agent()
    # Add logout button
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.rerun()

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# Main app flow - show either login form or main interface
if not st.session_state.authenticated:
    st.session_state.authenticated = authenticate_user()
else:
    show_main_interface()




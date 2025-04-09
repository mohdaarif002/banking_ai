import streamlit as st
import time
from datetime import datetime
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
from dotenv import load_dotenv
from utils import *

# Load environment variables
load_dotenv()

# For production, use environment variable
groq_api_key = os.getenv("GROQ_API_KEY")

# Simpler user credentials
user_credentials = {
    "user1": "password1",
    "user2": "password2",
    "root": "root",
}


def main():
    # Set page configuration
    st.set_page_config(
        page_title="CA Financial Agent",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Apply WhatsApp-style CSS
    apply_whatsapp_style()
    
    # Initialize session states
    initialize_session_states()
    
    # Check if we need to process a pending message after MPIN verification
    process_pending_messages()
    
    # Authentication flow
    if not st.session_state.authenticated:
        show_authentication_screen()
        return
    
    # Header with user info
    display_header()
    
    # Display chat messages in WhatsApp style
    display_chat_messages()
    
    # Create WhatsApp-style input area with fixed position at bottom
    display_input_area()

def apply_whatsapp_style():
    """Apply WhatsApp styling with CSS"""
    st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #efeae2;
        background-image: url("https://web.whatsapp.com/img/bg-chat-tile-dark_a4be512e7195b6b733d9110b408f075d.png");
        background-repeat: repeat;
    }
    
    /* Fixed header */
    .header-container {
        position: fixed;
        top: 0;
        z-index: 100;
        background-color: #128C7E;
        width: 100%;
        max-width: 100vw;
        margin: 0 auto;
        border-radius: 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 20px;
        color: white;
    }
    
    /* User profile in header */
    .user-profile {
        display: flex;
        align-items: center;
    }
    
    .user-avatar {
        width: 40px;
        height: 40px;
        background-color: #075E54;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
        margin-right: 10px;
    }
    
    /* Container for the entire chat */
    .chat-container {
        max-width: 900px;
        margin: 60px auto 70px;
        padding: 20px;
        height: calc(100vh - 130px);
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }
    
    /* User message bubble (on right) */
    .user-message-container {
        display: flex;
        justify-content: flex-end;
        margin: 8px 0;
        align-items: flex-start;
    }
    
    .user-message {
        background-color: #d9fdd3;
        padding: 8px 12px;
        border-radius: 7px;
        max-width: 65%;
        word-wrap: break-word;
        box-shadow: 0 1px 0.5px rgba(0, 0, 0, 0.13);
        position: relative;
        margin-left: 8px;
    }
    
    .user-icon {
        width: 25px;
        height: 25px;
        background-color: #128C7E;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 14px;
        font-weight: bold;
    }
    
    /* System message bubble (on left) */
    .system-message-container {
        display: flex;
        justify-content: flex-start;
        margin: 8px 0;
        align-items: flex-start;
    }
    
    .system-response {
        background-color: #ffffff;
        padding: 8px 12px;
        border-radius: 7px;
        max-width: 65%;
        word-wrap: break-word;
        box-shadow: 0 1px 0.5px rgba(0, 0, 0, 0.13);
        margin-left: 8px;
    }
    
    .bot-icon {
        width: 25px;
        height: 25px;
        background-color: #128C7E;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 14px;
    }
    
    /* Input area styling - FIXED AT BOTTOM */
    .input-area-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 99;
        padding: 10px;
        background-color: #f0f2f5;
        box-shadow: 0 -1px 5px rgba(0,0,0,0.1);
    }
    
    .input-area {
        max-width: 900px;
        margin: 0 auto;
        display: flex;
        align-items: center;
    }
    
    /* Make input field look more like WhatsApp */
    .stTextInput > div > div > input {
        border-radius: 18px !important;
        padding: 10px 15px !important;
        border: none !important;
        background-color: white !important;
    }
    
    /* Send button styling */
    .stButton > button {
        border-radius: 50% !important;
        background-color: #128C7E !important;
        color: white !important;
        width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        margin-left: 10px !important;
        border: none !important;
    }
    
    /* Loading indicator */
    .loading-dots {
        display: flex;
        justify-content: center;
    }
    
    .loading-dot {
        width: 8px;
        height: 8px;
        background-color: #667781;
        border-radius: 50%;
        margin: 0 2px;
    }
    
    /* Hide header elements */
    header {
        display: none !important;
    }
    
    /* Login form styling - CENTERED */
    .login-container {
        max-width: 400px;
        margin: 20vh auto;
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
        position: relative;
        top: 50%;
        transform: translateY(-50%);
    }
    
    .login-logo {
        width: 80px;
        height: 80px;
        background-color: #128C7E;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 40px;
        margin: 0 auto 20px;
    }
    
    .login-title {
        color: #128C7E;
        margin-bottom: 20px;
    }
    
    .login-error {
        color: red;
        font-size: 14px;
        margin-top: 10px;
    }
    
    /* Timestamp styling */
    .timestamp {
        font-size: 11px;
        color: #667781;
        text-align: right;
        margin-top: 3px;
    }
    
    /* MPIN verification modal - CENTERED */
    .mpin-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0,0,0,0.5);
        z-index: 1000;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .mpin-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        max-width: 300px;
        width: 100%;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        position: fixed;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
    }
                
    /* Loading indicator */
    .loading-dots {
        display: flex;
        justify-content: center;
    }
    
    .loading-dot {
        width: 8px;
        height: 8px;
        background-color: #667781;
        border-radius: 50%;
        margin: 0 2px;
    }
    
    /* Fix Streamlit form elements */
    div.stForm > div[data-testid="stFormSubmitButton"] {
        text-align: center;
    }
    
    /* Make equal padding in header */
    .header-container {
        padding-left: 20px;
        padding-right: 20px;
    }
    
    /* Fix form alignment */
    .centered-form {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_states():
    """Initialize all session state variables"""
    # Authentication states
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "login_error" not in st.session_state:
        st.session_state.login_error = ""
    
    # Chat states
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "processing_query" not in st.session_state:
        st.session_state.processing_query = False
    if "show_mpin" not in st.session_state:
        st.session_state.show_mpin = False
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None
    # Track MPIN verification for the session
    if "mpin_verified" not in st.session_state:
        st.session_state.mpin_verified = False
    # For form submission handling
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    if "mpin_verification_result" not in st.session_state:
        st.session_state.mpin_verification_result = None

def process_pending_messages():
    """Process any pending messages after MPIN verification"""
    # Process pending message if MPIN was verified
    if st.session_state.mpin_verification_result == "success":
        st.session_state.mpin_verification_result = None
        if st.session_state.pending_query:
            send_message(st.session_state.pending_query)
            st.session_state.pending_query = None
            st.session_state.show_mpin = False
            st.session_state.user_input = ""
    
    # Handle login form submission
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False
        # No need to rerun here, as we're already at the beginning of the script execution

def show_authentication_screen():
    """Display the login form"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <div class="login-logo">🏦</div>
            <h2 class="login-title">CA Banking Assistant</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username in user_credentials and user_credentials[username] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.login_error = ""
                    st.session_state.form_submitted = True
                else:
                    st.session_state.login_error = "Invalid username or password"
        
        if st.session_state.login_error:
            st.markdown(f"""
            <div class="login-error">{st.session_state.login_error}</div>
            """, unsafe_allow_html=True)

def display_header():
    """Display the header with user information"""
    first_initial = st.session_state.username[0].upper() if st.session_state.username else "G"
    
    st.markdown(f"""
    <div class="header-container">
        <div class="user-profile">
            <div class="user-avatar">{first_initial}</div>
            <div>
                <div style="font-weight: bold;">CA Banking Assistant</div>
                <div style="font-size: 12px;">Active now</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_chat_messages():
    """Display chat messages in WhatsApp style"""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        user_msg = message["user_message"]
        result = message["result"]
        timestamp = message.get("timestamp", datetime.now().strftime("%H:%M"))
        
        # User message with icon (right-aligned)
        st.markdown(f"""
        <div class="user-message-container">
            <div class="user-message">
                {user_msg}
                <div class="timestamp">{timestamp}</div>
            </div>
            <div class="user-icon">{st.session_state.username[0].upper() if st.session_state.username else "U"}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # System response with bank icon (left-aligned)
        if result and result.strip():
            st.markdown(f"""
            <div class="system-message-container">
                <div class="bot-icon">🏦</div>
                <div class="system-response">
                    {result}
                    <div class="timestamp">{timestamp}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Show typing indicator when processing
    if st.session_state.processing_query:
        st.markdown("""
        <div class="system-message-container">
            <div class="bot-icon">🏦</div>
            <div class="system-response" style="padding: 15px 12px;">
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_input_area():
    """Display the input area for queries"""
    st.markdown('<div class="input-area-container">', unsafe_allow_html=True)
    
    # Input area
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    cols = st.columns([14, 1])
    
    # User input handler
    def handle_input():
        if st.session_state.user_input:
            query = st.session_state.user_input
            st.session_state.user_input = ""  # Clear the input
            
            # Check if MPIN verification is needed
            if needs_mpin_verification(query) and not st.session_state.mpin_verified:
                st.session_state.show_mpin = True
                st.session_state.pending_query = query
            else:
                send_message(query)
    
    with cols[0]:
        st.text_input(
            "Type your query", 
            key="user_input",
            label_visibility="collapsed",
            on_change=handle_input,
            placeholder="Type your query",
            disabled=st.session_state.processing_query or st.session_state.show_mpin
        )
    
    # Send button
    with cols[1]:
        send_button = st.button("➤", key="send_button", 
                 disabled=st.session_state.processing_query or st.session_state.show_mpin)
        if send_button and st.session_state.user_input:
            handle_input()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display MPIN modal if needed
    if st.session_state.show_mpin:
        display_mpin_modal()

def needs_mpin_verification(query):
    """Check if the query requires MPIN verification"""
    # Keywords that might indicate a sensitive operation requiring verification
    sensitive_keywords = ["transfer", "payment", "send money", "pay", "withdraw", 
                         "transaction", "purchase", "buy", "authorize"]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in sensitive_keywords)

def handle_mpin_submit(verify):
    """Handle MPIN form submission"""
    if verify:
        mpin = st.session_state.mpin_input
        # In a real app, you would verify the MPIN securely
        if mpin == "123456":  # Sample MPIN
            # Set verification result to be processed in the next run
            st.session_state.mpin_verification_result = "success"
            st.session_state.mpin_verified = True
        else:
            st.session_state.mpin_verification_result = "error"
    else:
        # Cancel was clicked
        st.session_state.show_mpin = False
        st.session_state.pending_query = None

def display_mpin_modal():
    """Display MPIN verification modal"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        with st.form("mpin_form", clear_on_submit=False):
            st.markdown("<h3 style='text-align: center; color: #128C7E;'>Enter MPIN</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 14px; color: #667781;'>This transaction requires verification</p>", unsafe_allow_html=True)
            
            mpin = st.text_input("Enter your 6-digit MPIN", type="password", max_chars=6, key="mpin_input")
            
            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("Cancel")
            with col2:
                verify = st.form_submit_button("Verify")
            
            if verify or cancel:
                handle_mpin_submit(verify)
        
        # Show error message if verification failed
        if st.session_state.mpin_verification_result == "error":
            st.error("Invalid MPIN. Please try again.")
            # Reset the result so the error doesn't persist
            st.session_state.mpin_verification_result = None

def send_message(user_input, mpin=None):
    """Process user input and add to chat"""
    if not user_input:
        return
    
    # Set processing state to show loading indicator
    st.session_state.processing_query = True
    
    # Simulate API call with delay
    time.sleep(1)
    
    try:
        # Try to evaluate as a mathematical expression
        try:
            result = str(eval(user_input))
            # result = process_user_input(user_input)
        except:
            # Not a calculation, simulate API response
            # result = simulate_banking_response(user_input, mpin)
            try:
                result = str(groq_api_call(user_text=user_input, user_mpin="123456", groq_api_key=groq_api_key))
                llm_response = clean_sql_block(result)
                result = fetch_data_from_db(llm_response)
                if "Invalid" in result:
                    result = simulate_banking_response(user_input, mpin)
                    
            except:
                result
        
        # Add to chat history with timestamp
        st.session_state.messages.append({
            "user_message": user_input,
            "result": str(result),
            "timestamp": datetime.now().strftime("%H:%M")
        })
    except Exception as e:
        # Add error message to chat
        st.session_state.messages.append({
            "user_message": user_input,
            "result": f"I'm sorry, I encountered an error processing your query: {str(e)}",
            "timestamp": datetime.now().strftime("%H:%M")
        })
    finally:
        # Reset processing state
        st.session_state.processing_query = False

def simulate_banking_response(query, mpin=None):
    """Simulate banking chatbot responses"""
    query_lower = query.lower()
    
    # Balance inquiry
    if "balance" in query_lower:
        return "Your current account balance is $5,432.10"
    
    # Account info
    elif "account" in query_lower and "info" in query_lower:
        return "Account Number: XXXX-XXXX-1234\nAccount Type: Savings\nAccount Status: Active"
    
    # Transfer (requires MPIN)
    elif "transfer" in query_lower:
        if st.session_state.mpin_verified:
            return "Transfer processed successfully. Confirmation #TRF29384756"
        else:
            return "This transaction requires verification with your MPIN."
    
    # Recent transactions
    elif "transaction" in query_lower or "recent" in query_lower:
        return """Recent transactions:
- Amazon - $45.67 (Yesterday)
- Grocery Store - $32.50 (04/07/2025)
- Monthly Subscription - $9.99 (04/05/2025)
- Salary Deposit - +$3,500.00 (04/01/2025)"""
    
    # Loan information
    elif "loan" in query_lower:
        return "Your current loan balance is $15,678.90. Next payment of $450.00 is due on 04/15/2025."
    
    # Credit card
    elif "credit card" in query_lower:
        return "Your credit card ending in 5678 has a balance of $1,234.56. Available credit: $3,765.44"
    
    # Help/FAQ
    elif "help" in query_lower or "faq" in query_lower:
        return """How can I help you today?
- Check account balance
- View recent transactions
- Transfer funds
- Check loan status
- Credit card information
- Update personal details"""
    
    # Default response
    else:
        return "I'm your CA Banking Assistant. How may I help you with your banking needs today?"

if __name__ == "__main__":
    main()
import streamlit as st
import mysql.connector
import os
import sounddevice as sd
import numpy as np
import wave
from datetime import datetime
import openai
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Add OpenAI API key for Whisper

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Set up directories
SAVE_DIR = "recordings"
os.makedirs(SAVE_DIR, exist_ok=True)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mazhar321",
        database="BankDB",
        use_pure=True
    )

# # Audio recording function
# def record_audio(duration=5, sample_rate=44100):
#     st.write(f"Get ready... Recording will start in 1 second!")
#     sd.sleep(1000)  # 1-second buffer to ensure mic activation
#     st.write(f"🔴 Speak now for {duration} seconds...")

#     audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype=np.int16)
#     sd.wait()  # Wait for recording to finish
#     return audio_data, sample_rate

def record_audio(duration=5, sample_rate=44100):
    st.write(f"Preparing microphone...")
    
    # Generate and play a short silence/noise burst to activate the mic
    warmup_noise = np.zeros(int(1 * sample_rate), dtype=np.int16)  # 1 sec of silence
    sd.play(warmup_noise, samplerate=sample_rate)
    sd.wait()

    st.write(f"🔴 Speak now for {duration} seconds...")
    
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype=np.int16)
    sd.wait()  # Wait for recording to finish
    return audio_data, sample_rate

# Function to save WAV file in a given directory
def save_wav(filename, data, sample_rate, SAVE_DIR):
    filepath = os.path.join(SAVE_DIR, filename)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(2)  # Stereo
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(sample_rate)
        wf.writeframes(data.tobytes())
    return filepath  # Return the file path


# Transcribe audio using Whisper API
def transcribe_audio(audio_path):
    try:
        with open(audio_path, "rb") as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            print(f"Transcription response: {response}")
            return response["text"]
        
        # # Check if response has the expected format
        # if isinstance(response, dict) and "text" in response:
        #     transcribed_text = response["text"].strip()
        #     if transcribed_text:
        #         return transcribed_text
        #     else:
        #         st.warning("Empty transcription received. Please try speaking louder or recording again.")
        #         return ""
        # else:
        #     st.warning(f"Unexpected response format: {type(response)}")
        #     return ""
            
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        print(f"Transcription exception: {str(e)}")
        return ""

# Authentication function
def authenticate_user(mpin_input):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id, first_name FROM Customers WHERE customer_id = %s", (mpin_input,))
    result = cursor.fetchone()
    conn.close()
    return result  # Returns (customer_id, first_name) if found

# Get customer accounts
def get_customer_accounts(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT account_id, account_type, account_number, balance, currency FROM Accounts WHERE customer_id = %s", 
        (customer_id,)
    )
    accounts = cursor.fetchall()
    conn.close()
    return accounts

# Get account transactions
def get_transactions(account_id, limit=5):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT transaction_id, transaction_type, amount, currency, 
               transaction_date, status, description 
        FROM Transactions 
        WHERE account_id = %s 
        ORDER BY transaction_date DESC 
        LIMIT %s
        """, 
        (account_id, limit)
    )
    transactions = cursor.fetchall()
    conn.close()
    return transactions

# Get credit card details
def get_credit_cards(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT cc.card_id, cc.card_type, cc.card_number, cc.expiry_date, 
               cc.card_status, a.balance, a.credit_limit
        FROM Credit_Cards cc
        JOIN Accounts a ON cc.account_id = a.account_id
        WHERE a.customer_id = %s
        """,
        (customer_id,)
    )
    cards = cursor.fetchall()
    conn.close()
    return cards

# Get pending bills
def get_bills(customer_id, status="Pending"):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT b.bill_id, b.bill_name, b.amount, b.currency, 
               b.bill_date, b.due_date, b.status
        FROM Bills b
        JOIN Accounts a ON b.account_id = a.account_id
        WHERE a.customer_id = %s AND b.status = %s
        ORDER BY b.due_date
        """,
        (customer_id, status)
    )
    bills = cursor.fetchall()
    conn.close()
    return bills

# Define conversation flows
CONVERSATION_FLOWS = {
    "balance_inquiry": {
        "initial_message": "Which account balance would you like to check?",
        "slots": ["account_type"],
        "choices": {
            "account_type": ["Savings", "Checking", "Credit Card", "All accounts"]
        },
        "handler": "handle_balance_inquiry"
    },
    "transaction_history": {
        "initial_message": "For which account would you like to see transactions?",
        "slots": ["account_id", "time_period"],
        "choices": {
            "time_period": ["Last 5 transactions", "Last month", "Last 3 months"]
        },
        "handler": "handle_transaction_history"
    },
    "credit_card_info": {
        "initial_message": "What credit card information would you like to know?",
        "slots": ["card_id", "info_type"],
        "choices": {
            "info_type": ["Current balance", "Available credit", "Due date", "Payment details"]
        },
        "handler": "handle_credit_card_info"
    },
    "bills_payment": {
        "initial_message": "Would you like to view or pay bills?",
        "slots": ["action", "bill_id"],
        "choices": {
            "action": ["View pending bills", "Pay a bill"]
        },
        "handler": "handle_bills_payment"
    }
}

# Handler functions for each conversation flow
def handle_balance_inquiry(customer_id, slots):
    account_type = slots.get("account_type")
    accounts = get_customer_accounts(customer_id)
    
    if account_type == "All accounts":
        return {
            "response_type": "account_list",
            "data": accounts,
            "message": "Here are all your accounts:"
        }
    else:
        filtered_accounts = [a for a in accounts if a["account_type"] == account_type]
        if filtered_accounts:
            return {
                "response_type": "account_list", 
                "data": filtered_accounts,
                "message": f"Here are your {account_type} accounts:"
            }
        else:
            return {
                "response_type": "message",
                "message": f"You don't have any {account_type} accounts."
            }

def handle_transaction_history(customer_id, slots):
    account_id = slots.get("account_id")
    time_period = slots.get("time_period", "Last 5 transactions")
    
    # Default to 5 transactions
    limit = 5
    if time_period == "Last month":
        limit = 30
    elif time_period == "Last 3 months":
        limit = 90
    
    transactions = get_transactions(account_id, limit)
    
    if transactions:
        return {
            "response_type": "transaction_list",
            "data": transactions,
            "message": f"Here are your {time_period}:"
        }
    else:
        return {
            "response_type": "message",
            "message": "No transactions found for this period."
        }

def handle_credit_card_info(customer_id, slots):
    card_id = slots.get("card_id")
    info_type = slots.get("info_type")
    
    cards = get_credit_cards(customer_id)
    selected_card = next((c for c in cards if c["card_id"] == int(card_id)), None)
    
    if not selected_card:
        return {
            "response_type": "message",
            "message": "Credit card not found."
        }
    
    if info_type == "Current balance":
        return {
            "response_type": "message",
            "message": f"Your current balance is {selected_card['balance']} {selected_card.get('currency', 'USD')}"
        }
    elif info_type == "Available credit":
        available = selected_card['credit_limit'] - selected_card['balance']
        return {
            "response_type": "message",
            "message": f"Your available credit is {available} {selected_card.get('currency', 'USD')}"
        }
    elif info_type == "Due date":
        # This would require additional database query for actual implementation
        return {
            "response_type": "message",
            "message": "Your payment due date is on the 15th of next month."
        }
    else:
        return {
            "response_type": "card_details",
            "data": selected_card,
            "message": "Here are your card details:"
        }

def handle_bills_payment(customer_id, slots):
    action = slots.get("action")
    
    if action == "View pending bills":
        bills = get_bills(customer_id, "Pending")
        if bills:
            return {
                "response_type": "bill_list",
                "data": bills,
                "message": "Here are your pending bills:"
            }
        else:
            return {
                "response_type": "message",
                "message": "You don't have any pending bills."
            }
    elif action == "Pay a bill":
        bill_id = slots.get("bill_id")
        if bill_id:
            # In a real implementation, this would process the payment
            return {
                "response_type": "message",
                "message": f"Bill payment for bill #{bill_id} has been scheduled."
            }
        else:
            bills = get_bills(customer_id, "Pending")
            return {
                "response_type": "bill_selection",
                "data": bills,
                "message": "Which bill would you like to pay?"
            }

# Main app initialization
def initialize_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.customer_id = None
        st.session_state.customer_name = ""
    
    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = {
            "current_flow": None,
            "flow_step": 0,
            "slots": {}
        }
    
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

# Function to render different response types
def render_response(response):
    if response["response_type"] == "message":
        st.info(response["message"])
    
    elif response["response_type"] == "account_list":
        st.info(response["message"])
        for account in response["data"]:
            st.write(f"**{account['account_type']}** (#{account['account_number']}): {account['balance']} {account['currency']}")
    
    elif response["response_type"] == "transaction_list":
        st.info(response["message"])
        for txn in response["data"]:
            st.write(f"**{txn['transaction_type']}** - {txn['amount']} {txn['currency']} on {txn['transaction_date']}")
            st.write(f"Status: {txn['status']} | {txn['description']}")
            st.write("---")
    
    elif response["response_type"] == "bill_list":
        st.info(response["message"])
        for bill in response["data"]:
            st.write(f"**{bill['bill_name']}**: {bill['amount']} {bill['currency']}")
            st.write(f"Due date: {bill['due_date']} | Status: {bill['status']}")
            st.write("---")
    
    elif response["response_type"] == "bill_selection":
        st.info(response["message"])
        for bill in response["data"]:
            if st.button(f"Pay {bill['bill_name']} - {bill['amount']} {bill['currency']}"):
                st.session_state.conversation_state["slots"]["bill_id"] = bill['bill_id']
                process_flow_step()
    
    elif response["response_type"] == "card_details":
        st.info(response["message"])
        card = response["data"]
        st.write(f"**Card Type**: {card['card_type']}")
        st.write(f"**Card Number**: ****{card['card_number'][-4:]}")
        st.write(f"**Expiry Date**: {card['expiry_date']}")
        st.write(f"**Status**: {card['card_status']}")
        st.write(f"**Current Balance**: {card['balance']}")
        st.write(f"**Credit Limit**: {card['credit_limit']}")

# Process conversation flow
def process_flow_step():
    state = st.session_state.conversation_state
    current_flow = state["current_flow"]
    flow_step = state["flow_step"]
    
    # If no active flow, do nothing
    if not current_flow:
        return
    
    flow_config = CONVERSATION_FLOWS[current_flow]
    
    # If all slots are filled, process the request
    required_slots = flow_config["slots"]
    if all(slot in state["slots"] for slot in required_slots):
        # Call the appropriate handler
        handler_name = flow_config["handler"]
        response = globals()[handler_name](st.session_state.customer_id, state["slots"])
        
        # Add to conversation history
        st.session_state.conversation_history.append({
            "type": "response",
            "response_type": response["response_type"],
            "message": response["message"],
            "data": response.get("data", None)
        })
        
        # Reset conversation state
        st.session_state.conversation_state = {
            "current_flow": None,
            "flow_step": 0,
            "slots": {}
        }
    else:
        # Get the next slot to fill
        next_slot = required_slots[flow_step]
        
        # If this slot has predefined choices, show them
        if next_slot in flow_config.get("choices", {}):
            choices = flow_config["choices"][next_slot]
            st.info(flow_config["initial_message"])
            
            # For account selection or card selection, fetch from DB
            if next_slot == "account_id":
                accounts = get_customer_accounts(st.session_state.customer_id)
                for account in accounts:
                    if st.button(f"{account['account_type']} (#{account['account_number']})"):
                        state["slots"][next_slot] = account['account_id']
                        state["flow_step"] += 1
                        process_flow_step()
            
            elif next_slot == "card_id":
                cards = get_credit_cards(st.session_state.customer_id)
                for card in cards:
                    if st.button(f"{card['card_type']} (****{card['card_number'][-4:]})"):
                        state["slots"][next_slot] = card['card_id']
                        state["flow_step"] += 1
                        process_flow_step()
            
            else:
                # Generic choices
                for choice in choices:
                    if st.button(choice):
                        state["slots"][next_slot] = choice
                        state["flow_step"] += 1
                        process_flow_step()
        else:
            # For slots without predefined choices, use text input
            st.text_input(f"Please enter {next_slot}:", 
                          key=f"input_{next_slot}",
                          on_change=lambda: state["slots"].update({
                              next_slot: st.session_state[f"input_{next_slot}"]
                          }))
            
            if next_slot in state["slots"]:
                state["flow_step"] += 1
                process_flow_step()

# Intent detection (simplified - in a real system would use NLP/NLU)
def detect_intent(text):
    text = text.lower()
    
    # Simple keyword matching for intent detection
    if any(keyword in text for keyword in ["balance", "how much", "money", "account"]):
        return "balance_inquiry"
    
    elif any(keyword in text for keyword in ["transaction", "history", "recent", "spent"]):
        return "transaction_history"
    
    elif any(keyword in text for keyword in ["credit card", "card", "credit"]):
        return "credit_card_info"
    
    elif any(keyword in text for keyword in ["bill", "payment", "pay", "due"]):
        return "bills_payment"
    
    return None

# Streamlit app UI components
def login_form():
    with st.form("login_form"):
        st.markdown('<div class="centered-image">', unsafe_allow_html=True)
        st.image("logo.png", width=120)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>MyBank Assistant</h2>", unsafe_allow_html=True)

        mpin = st.text_input("Enter your Customer ID to log in:", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user = authenticate_user(mpin)
            if user:
                st.session_state.logged_in = True
                st.session_state.customer_id = user[0]
                st.session_state.customer_name = user[1]
                st.rerun()
            else:
                st.error("Invalid Customer ID. Please try again.")

def main_interface():
    st.markdown(f"### 👋 Welcome back, **{st.session_state.customer_name}**")
    
    # Show conversation history
    with st.container():
        for item in st.session_state.conversation_history:
            if item["type"] == "user":
                st.markdown(f"**You**: {item['content']}")
            elif item["type"] == "response":
                # Check if content is nested or direct
                if "content" in item and isinstance(item["content"], dict):
                    render_response(item["content"])
                else:
                    # Handle the case where response properties are at the top level
                    render_response(item)
    
    # Process current conversation state if active
    if st.session_state.conversation_state["current_flow"]:
        process_flow_step()
    
    # Show main options if no active conversation
    if not st.session_state.conversation_state["current_flow"]:
        st.markdown("### What would you like to do today?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Check Account Balance"):
                st.session_state.conversation_state = {
                    "current_flow": "balance_inquiry",
                    "flow_step": 0,
                    "slots": {}
                }
                st.rerun()
                
            if st.button("Credit Card Information"):
                st.session_state.conversation_state = {
                    "current_flow": "credit_card_info",
                    "flow_step": 0,
                    "slots": {}
                }
                st.rerun()
                
        with col2:
            if st.button("Transaction History"):
                st.session_state.conversation_state = {
                    "current_flow": "transaction_history",
                    "flow_step": 0,
                    "slots": {}
                }
                st.rerun()
                
            if st.button("Bills & Payments"):
                st.session_state.conversation_state = {
                    "current_flow": "bills_payment",
                    "flow_step": 0,
                    "slots": {}
                }
                st.rerun()
    
    # Voice input
    st.markdown("---")
    st.markdown("### 🎤 Speak to your banking assistant")
    
    # Initialize session state for transcription editing if not exists
    if "audio_recorded" not in st.session_state:
        st.session_state.audio_recorded = False
        st.session_state.transcription = ""
        st.session_state.audio_filepath = ""
    
    # Only show the recording controls if not currently editing a transcription
    if not st.session_state.audio_recorded:
        duration = st.slider("Recording Duration (seconds)", min_value=1, max_value=10, value=5)
        
        if st.button("Start Recording"):
            audio_data, sample_rate = record_audio(duration)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rec_audio_{timestamp}.wav"
            filepath = save_wav(filename, audio_data, sample_rate, SAVE_DIR)
            print(f"Audio saved to: {filepath}")
            
            # Transcribe audio
            user_text = transcribe_audio(filepath)
            print(f"You said: {user_text}")
            
            # Store in session state for editing
            st.session_state.audio_recorded = True
            st.session_state.transcription = user_text
            st.session_state.audio_filepath = filepath
            st.rerun()
    else:
        # Show the editable transcription
        st.audio(st.session_state.audio_filepath)
        st.info("Please review and edit the transcription if needed:")
        
        # Editable text area for transcription
        edited_transcription = st.text_area(
            "Transcription", 
            value=st.session_state.transcription,
            height=100,
            key="edited_transcription"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Transcription"):
                # Process the edited transcription
                user_text = edited_transcription
                st.success(f"Processing: {user_text}")
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "type": "user",
                    "content": user_text
                })
                
                # Detect intent and set flow
                intent = detect_intent(user_text)
                if intent:
                    st.session_state.conversation_state = {
                        "current_flow": intent,
                        "flow_step": 0,
                        "slots": {}
                    }
                else:
                    st.session_state.conversation_history.append({
                        "type": "response",
                        "response_type": "message",
                        "message": "I'm sorry, I couldn't understand what you need. Please try again or use the buttons above."
                    })
                
                # Reset the audio recording state
                st.session_state.audio_recorded = False
                st.session_state.transcription = ""
                st.session_state.audio_filepath = ""
                st.rerun()
        
        with col2:
            if st.button("Cancel"):
                # Reset without processing
                st.session_state.audio_recorded = False
                st.session_state.transcription = ""
                st.session_state.audio_filepath = ""
                st.rerun()

# Main app
def main():
    st.set_page_config(page_title="CA Bank Assistant", page_icon="💰")
    
    # Initialize session state
    initialize_session_state()
    
    # Custom CSS
    st.markdown("""
    <style>
    .centered-image {
        display: flex;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Show login form or main interface
    if not st.session_state.logged_in:
        login_form()
    else:
        main_interface()
    
    # Logout option
    if st.session_state.logged_in:
        if st.sidebar.button("Logout"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main() 
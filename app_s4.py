import streamlit as st
import sounddevice as sd
import numpy as np
import wave
import os
import time
from datetime import datetime
import whisper
from utils import *

from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")



def main():
    # Set page configuration
    st.set_page_config(
        page_title="Banking_app",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS for WhatsApp Web style
    st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #efeae2;
        background-image: url("https://web.whatsapp.com/img/bg-chat-tile-dark_a4be512e7195b6b733d9110b408f075d.png");
        background-repeat: repeat;
    }
    
    /* Container for the entire chat */
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        height: 75vh;
        overflow-y: auto;
    }
    
    /* User message bubble (on right) */
    .user-message {
        background-color: #d9fdd3;
        padding: 10px 12px;
        border-radius: 7px;
        margin: 5px 0;
        max-width: 65%;
        margin-left: auto;
        word-wrap: break-word;
        box-shadow: 0 1px 0.5px rgba(0, 0, 0, 0.13);
        position: relative;
    }
    
    /* System message bubble (on left) */
    .system-response {
        background-color: #ffffff;
        padding: 10px 12px;
        border-radius: 7px;
        margin: 5px 0;
        max-width: 65%;
        word-wrap: break-word;
        box-shadow: 0 1px 0.5px rgba(0, 0, 0, 0.13);
    }
    
    /* Input area styling */
    .input-area {
        background-color: #f0f2f5;
        padding: 10px;
        border-radius: 8px;
        margin-top: 20px;
        display: flex;
    }
    
    /* Header bar */
    .header-bar {
        background-color: #128C7E;
        color: white;
        padding: 10px 20px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px 8px 0 0;
        margin-bottom: 5px;
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
    
    /* Hide header elements */
    header {
        display: none !important;
    }
    
    /* Result text styling */
    .result-text {
        color: #65676b;
        font-size: 0.85em;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # WhatsApp header
    st.markdown('<div class="header-bar">CA Banking Agent</div>', unsafe_allow_html=True)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Define processing function (calculator example)
    def process_user_input(user_input):
        try:
            # Try to evaluate as a mathematical expression
            result = eval(user_input)
            return result
        except:
            # If not a calculation, return empty string
            # user_text = transcribe_audio(filepath)
            # print('user_text: ',user_input)

            llm_response = groq_api_call(user_text=user_input, user_mpin="123456", groq_api_key= groq_api_key)
            # llm_response = clean_sql_block(llm_response)
            # st.success("Transcription Complete!")
            # st.text_area("LLM Response: ", llm_response)

            return llm_response

    # Function to process input and add to chat
    def send_message():
        if st.session_state.user_input:
            user_message = st.session_state.user_input
            
            # Process the message
            result = process_user_input(user_message)
            
            # Add to chat history
            st.session_state.messages.append({
                "user_message": user_message,
                "result": result
            })
            
            # Clear the input
            st.session_state.user_input = ""

    # Display chat messages in WhatsApp style
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        user_msg = message["user_message"]
        result = message["result"]
        
        # User message in green bubble (right-aligned)
        st.markdown(f'<div class="user-message">{user_msg}</div>', unsafe_allow_html=True)
        
        # System response in white bubble (left-aligned) - Only show if there's a result
        if result != "":
            system_text = f'Result: {result}'
            st.markdown(f'<div class="system-response">{system_text}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Create WhatsApp-style input area
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    cols = st.columns([15, 1])
    
    with cols[0]:
        st.text_input(
            "", 
            key="user_input",
            label_visibility="collapsed",
            on_change=send_message,
            placeholder="Type a message"
        )
    
    with cols[1]:
        st.button("➤", on_click=send_message)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
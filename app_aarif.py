import streamlit as st
import sounddevice as sd
import numpy as np
import wave
import os
import time
from datetime import datetime
import whisper
from utils import *

# from dotenv import load_dotenv
# load_dotenv()

# groq_api_key = os.getenv("GROQ_API_KEY")


SAVE_DIR = "./recordings"
os.makedirs(SAVE_DIR, exist_ok=True)



def clean_sql_block(sql_code):
    # Remove triple backticks and 'sql' if present
    lines = sql_code.strip().splitlines()
    print(sql_code.strip().splitlines())
    cleaned_lines = [line for line in lines if not line.strip().startswith("```")]
    return "\n".join(cleaned_lines)

def check_mpin(mpin_input):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",
        database="BankDB"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id, first_name FROM Customers WHERE mpin = %s", (mpin_input,))
    result = cursor.fetchone()
    conn.close()
    return result  # Returns (customer_id, first_name) if found

# Initialize session state on first run
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.customer_id = None
    st.session_state.customer_name = ""

# Show login form only if not logged in
if not st.session_state.logged_in:
    with st.form("login_form"):
        # st.title("🔐 Welcome to AxisBank, Please provide your 6 digit MPIN ?")
        # st.markdown(
        #             """
        #             <div style="text-align: center;">
        #                 <img src="./logo.png" width="120"/>
        #                 <h2 style="margin-top: 0;">MyBank Assistant</h2>
        #             </div>
        #             """,
        #             unsafe_allow_html=True
        #         )
        

        st.markdown('<div class="centered-image">', unsafe_allow_html=True)
        st.image("logo.png", width=120)
        st.markdown("</div>", unsafe_allow_html=True)

        # st.image("logo.png", width=120)
        st.markdown("<h2 style='text-align: center;'>MyBank Assistant</h2>", unsafe_allow_html=True)

        mpin = st.text_input("Enter your 6-digit MPIN to log in:", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user = check_mpin(mpin)  # Replace with your auth logic
            if user:
                st.session_state.logged_in = True
                st.session_state.customer_id = user[0]
                st.session_state.customer_name = user[1]
                st.experimental_rerun()  # 🔁 Force re-run to clear login form
                # st.success(f"Welcome, {user[1]}! 🔓")
            else:
                st.error("Invalid MPIN. Please try again.")



if st.session_state.logged_in:
    # st.title("🔓 Welcome {st.session_state.customer_name} to AxisBank, Voice Assistanct")
    st.markdown(f"### 👋 Welcome back, **{st.session_state.customer_name}**")
    # st.success(f"Welcome, {st.session_state.customer_name}!")
  
    # Input for recording duration
    duration = st.slider("Select Recording Duration (seconds)", min_value=1, max_value=10, value=5)

# Initialize session state for storing recordings
    if "list_of_dic" not in st.session_state:
        st.session_state.list_of_dic = []

    # Button to start recording
    if st.button("Start Recording"):
        audio_data, sample_rate = record_audio(duration)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"rec_audio_{timestamp}.wav"
        filepath = save_wav(filename, audio_data, sample_rate,SAVE_DIR)

        # Till now recording is saved and we have a path to it 


        # st.success(f"Recording saved at: {filepath}")
        # Allow playback
        # st.audio(filepath, format="audio/wav")


        user_text = transcribe_audio(filepath)
        print('user_text: ',user_text)

        chain_response = groq_api_call(user_text=user_text, user_mpin="123456")
        # llm_response = clean_sql_block(llm_response)
        
        st.text_area("Chain Response: ", chain_response)


        if chain_response == "Access Denied: Invalid MPIN.":
            print(chain_response)
        else:
            response_2 = groq_api_call_2(user_text,chain_response)
           

        st.text_area("Human Readable Response:", response_2)



        # Append new recording to session state
        dic_of_rec = {
            'filepath': filepath,
            'text': user_text
        }
        st.session_state.list_of_dic.append(dic_of_rec)

        # Display stored recordings
        for dic in st.session_state.list_of_dic:
            st.audio(dic['filepath'], format="audio/wav")  # Play audio
            st.text_area("Transcription", dic['text'])  # Show transcription
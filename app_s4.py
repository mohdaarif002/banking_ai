import streamlit as st
import sounddevice as sd
import numpy as np
import wave
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
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
        page_title="CA Financial Agent",
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
    
    /* Fixed header */
    .header-container {
        position: fixed;
        top: 0;
        z-index: 100;
        background-color: #128C7E;
        width: 100% ;
        max-width: auto;
        margin: 0 auto;
        border-radius: 8px 8px 0 0;
    }
    
    
    /* Header bar */
    .header-bar {
        color: white;
        padding: 10px 20px;
        font-size: 18px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    
    /* About button in header */
    .about-button {
        background-color: transparent;
        color: white;
        border: none;
        font-size: 16px;
        cursor: pointer;
        padding: 5px 10px;
        border-radius: 5px;
    }
    
    .about-button:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    /* Container for the entire chat */
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        height: 70vh;
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
    
    /* Input area styling */
    .input-area-container {
        position: fixed;
        bottom: 0;
        z-index: 99;
        max-width: 900px;
        margin: 0 auto;
    }
    
    .input-area {
        background-color: #f0f2f5;
        padding: 10px;
        border-radius: 8px;
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
    
    /* Audio button styling */
    .audio-button button {
        border-radius: 50% !important;
        background-color: #128C7E !important;
        color: white !important;
        width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        margin-left: 10px !important;
        border: none !important;
    }
    
    /* Audio recording indicator */
    .recording-indicator {
        color: red;
        font-size: 12px;
        margin-top: 5px;
        text-align: center;
    }
    
    /* Hide header elements */
    header {
        display: none !important;
    }
    
    /* Audio message styling */
    .audio-message {
        background-color: #d9fdd3;
        padding: 5px 10px;
        border-radius: 8px;
        margin-top: 5px;
        display: flex;
        align-items: center;
    }
    
    /* Transcription styling */
    .transcription {
        font-style: italic;
        color: #667781;
        font-size: 0.9em;
        margin-top: 5px;
    }
    
    /* About dialog */
    .about-dialog {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        max-width: 500px;
        margin: 0 auto;
    }
    
    .dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize recording state
    if "recording" not in st.session_state:
        st.session_state.recording = False
    
    # Initialize transcribing state
    if "transcribing" not in st.session_state:
        st.session_state.transcribing = False
    
    # Initialize about dialog state
    if "show_about" not in st.session_state:
        st.session_state.show_about = False
    
    # Initialize edit transcription state
    if "edit_transcription" not in st.session_state:
        st.session_state.edit_transcription = None

    # About button callback
    def toggle_about():
        st.session_state.show_about = not st.session_state.show_about

    # Header with fixed position
    st.markdown("""
    <div class="header-container">
        <div class="header-bar">
            <span>CA Banking Agent</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # # About button in standard Streamlit
    # if st.button("About", key="about_button"):
    #     toggle_about()

    # # Show about dialog if state is True
    # if st.session_state.show_about:
    #     st.markdown("""
    #     <div class="about-dialog">
    #         <div class="dialog-header">
    #             <h3>About CA Banking Agent</h3>
    #         </div>
    #         <p>This is a WhatsApp-style chat interface for CA Banking Agent. You can interact using text or voice messages.</p>
    #         <p>Features:</p>
    #         <ul>
    #             <li>Voice input with real-time transcription</li>
    #             <li>Edit transcriptions if needed</li>
    #             <li>AI-powered responses to banking queries</li>
    #         </ul>
    #         <p>Version 1.0</p>
    #     </div>
    #     """, unsafe_allow_html=True)
        
    #     if st.button("Close", key="close_about_button"):
    #         st.session_state.show_about = False
    #         st.rerun()

    # Function to load whisper model for transcription
    @st.cache_resource
    def load_whisper_model():
        model = whisper.load_model("base")
        return model

    # Load the whisper model
    whisper_model = load_whisper_model()

    # Function to record audio
    def record_audio(duration=5, sample_rate=16000):
        st.write("Recording...")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()
        st.write("Recording finished!")
        return audio_data, sample_rate

    # Function to save audio to file
    def save_audio(audio_data, sample_rate, file_path="temp_audio.wav"):
        with wave.open(file_path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        return file_path

    # Function to transcribe audio using whisper
    def transcribe_audio(filepath):
        try:
            result = whisper_model.transcribe(filepath)
            return result["text"]
        except Exception as e:
            st.error(f"Transcription error: {e}")
            return "Transcription failed. Please try again."

    # Process user input
    def process_user_input(user_input):
        try:
            # Try to evaluate as a mathematical expression
            result = eval(user_input)
            return str(result)
        except:
            # Not a calculation, send to LLM
            try:
                llm_response = groq_api_call(user_text=user_input, user_mpin="123456", groq_api_key=groq_api_key)
                return llm_response
            except Exception as e:
                return f"I'm having trouble processing your request. Error: {str(e)}"

    # Function to process input and add to chat
    def send_message():
        if st.session_state.user_input:
            user_message = st.session_state.user_input
            
            # Process the message
            result = process_user_input(user_message)
            
            # Add to chat history
            st.session_state.messages.append({
                "user_message": user_message,
                "result": result,
                "type": "text"
            })
            
            # Clear the input and edit state
            st.session_state.user_input = ""
            st.session_state.edit_transcription = None

    # Function to toggle recording state
    def toggle_recording():
        if not st.session_state.recording:
            # Start recording
            st.session_state.recording = True
            st.session_state.transcribing = False
        else:
            # Stop recording and start transcribing
            st.session_state.recording = False
            st.session_state.transcribing = True
            
            # In a real implementation without actual recording function
            # we'll simulate recording and transcription for demo purposes
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_path = f"audio_{timestamp}.wav"
            
            # Simulate a delay for recording
            time.sleep(1)
            
            # Here we would actually record and transcribe
            # For demo, we'll simulate with sample messages
            transcribed_text = simulate_transcription()
            
            # Set the transcribed text for editing if needed
            st.session_state.edit_transcription = transcribed_text
            
            # Reset transcribing state
            st.session_state.transcribing = False

    # Function to simulate audio transcription
    def simulate_transcription():
        sample_transcriptions = [
            "What's my current account balance?",
            "I need to transfer $500 to John's account.",
            "When is my next loan payment due?",
            "Can you help me understand the recent transaction from Amazon?",
            "How do I apply for a new credit card?"
        ]
        import random
        return random.choice(sample_transcriptions)

    # Function to edit transcription
    def use_transcription():
        if st.session_state.edit_transcription:
            st.session_state.user_input = st.session_state.edit_transcription
            st.session_state.edit_transcription = None

    # Display chat messages in WhatsApp style
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        user_msg = message["user_message"]
        result = message["result"]
        msg_type = message.get("type", "text")
        
        # User message with icon (right-aligned)
        st.markdown(f"""
        <div class="user-message-container">
            <div class="user-message">{user_msg}</div>
            <div class="user-icon">You</div>
        </div>
        """, unsafe_allow_html=True)
        
        if msg_type == "audio":
            # Show audio player and transcription
            st.markdown(f"""
            <div class="user-message-container">
                <div class="audio-message">
                    <span>🔊</span>&nbsp;&nbsp;<span>0:05</span>
                </div>
                <div class="user-icon">U</div>
            </div>
            """, unsafe_allow_html=True)
        
        # System response with boat icon (left-aligned)
        if result and result.strip():
            st.markdown(f"""
            <div class="system-message-container">
                <div class="bot-icon">🚢</div>
                <div class="system-response">{result}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Create WhatsApp-style input area with fixed position at bottom
    st.markdown('<div class="input-area-container">', unsafe_allow_html=True)
    
    # Show transcription editing area if needed
    if st.session_state.edit_transcription:
        st.markdown(f"""
        <div style="background-color: #f0f2f5; padding: 10px; border-radius: 8px 8px 0 0; margin-bottom: 2px;">
            <div class="transcription">
                <strong>Transcription:</strong> {st.session_state.edit_transcription}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Use this transcription", key="use_transcription_button"):
            use_transcription()
    
    # Input area
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    cols = st.columns([14, .5, .5])
    
    with cols[0]:
        st.text_input(
            "", 
            key="user_input",
            label_visibility="collapsed",
            on_change=send_message,
            placeholder="Type your query",
            disabled=st.session_state.recording or st.session_state.transcribing
        )
    
    # Audio button
    with cols[1]:
        if st.session_state.transcribing:
            audio_icon = "⏳"
        elif st.session_state.recording:
            audio_icon = "⏹️"
        else:
            audio_icon = "🎤"
        
        audio_button = st.button(audio_icon, key="audio_button", on_click=toggle_recording)
        
        if st.session_state.recording:
            st.markdown('<div class="recording-indicator">Recording...</div>', unsafe_allow_html=True)
        elif st.session_state.transcribing:
            st.markdown('<div class="recording-indicator">Transcribing...</div>', unsafe_allow_html=True)
    
    # Send button
    with cols[2]:
        st.button("➤", key="send_button", on_click=send_message, disabled=st.session_state.recording or st.session_state.transcribing)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
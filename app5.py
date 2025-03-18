import streamlit as st
import sounddevice as sd
import numpy as np
import wave
import os
import time
from datetime import datetime
import whisper


# Load Whisper model (choose from: "tiny", "base", "small", "medium", "large")
model = whisper.load_model("base")

# Create a directory for recordings if it doesn't exist
SAVE_DIR = "recordings"
os.makedirs(SAVE_DIR, exist_ok=True)

# Function to record audio
# def record_audio(duration=5, sample_rate=44100):
#     st.write(f"Speak now for {duration} seconds...")
#     audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype=np.int16)
#     sd.wait()  # Wait for recording to finish
#     return audio_data, sample_rate


# def record_audio(duration=5, sample_rate=44100):
#     st.write(f"Get ready... Recording will start in 1 second!")
#     sd.sleep(2000)  # 1-second buffer to ensure mic activation
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
def save_wav(filename, data, sample_rate):
    filepath = os.path.join(SAVE_DIR, filename)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(2)  # Stereo
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(sample_rate)
        wf.writeframes(data.tobytes())
    return filepath  # Return the file path

# Function to transcribe audio
def transcribe_audio(filepath):
    result = model.transcribe(filepath)
    return result["text"]


# Streamlit UI
st.title("Real-Time Voice Recorder")

# Input for recording duration
duration = st.slider("Select Recording Duration (seconds)", min_value=1, max_value=10, value=5)

# list_of_dic =[]

# Initialize session state for storing recordings
if "list_of_dic" not in st.session_state:
    st.session_state.list_of_dic = []

# Button to start recording
if st.button("Start Recording"):
    audio_data, sample_rate = record_audio(duration)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"rec_audio_{timestamp}.wav"
    filepath = save_wav(filename, audio_data, sample_rate)

    # Till now recording is saved and we have a path to it 


    # st.success(f"Recording saved at: {filepath}")
    # Allow playback
    # st.audio(filepath, format="audio/wav")


    text = transcribe_audio(filepath)
    # st.success("Transcription Complete!")
    # st.text_area("Transcribed Text:", text)


    # dic_of_rec = {
    #     'filepath': filepath,
    #     'text': text
    # }
    # list_of_dic.append(dic_of_rec)

    # # Display stored recordings
    # for dic in list_of_dic:
    #     print(dic)
    #     st.audio(dic['filepath'], format="audio/wav")  # Play audio
    #     st.text_area("Transcription", dic['text'])  # Show transcription


    

    # Append new recording to session state
    dic_of_rec = {
        'filepath': filepath,
        'text': text
    }
    st.session_state.list_of_dic.append(dic_of_rec)

    # Display stored recordings
    for dic in st.session_state.list_of_dic:
        st.audio(dic['filepath'], format="audio/wav")  # Play audio
        st.text_area("Transcription", dic['text'])  # Show transcription




    

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
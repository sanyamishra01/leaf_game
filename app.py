import sounddevice as sd
import numpy as np
import streamlit as st

# Parameters for live audio capture
RATE = 44100  # Sampling rate in Hz
CHUNK = 1024  # Number of audio frames per buffer

# Streamlit App Title
st.title("Live Audio Analyzer")
st.write("Humming into the microphone will process audio data in real-time!")

# Function to process audio data in real-time
def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")  # Report any errors in the stream
    # Process audio data here
    audio_data = indata[:, 0]  # Use the first channel of audio input
    normalized_data = np.linalg.norm(audio_data)  # Normalize the data
    # Example: Print normalized data to console
    print(f"Normalized Data: {normalized_data:.3f}")

# Start the audio stream and process in real-time using Streamlit button
if st.button("Start Listening"):
    try:
        st.write("Listening... Press Stop to end the session.")
        with sd.InputStream(callback=audio_callback, channels=1, samplerate=RATE, blocksize=CHUNK):
            sd.sleep(10000)  # Keep the stream open for 10 seconds
    except Exception as e:
        st.error(f"An error occurred: {e}")

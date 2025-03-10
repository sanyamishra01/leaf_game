import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.signal import stft
import sounddevice as sd
import queue


print(sd.query_devices())  # List all available devices for debugging
sd.default.device = (1, 1)  # Use appropriate device IDs for input and output

devices = sd.query_devices()
default_input = sd.default.device[0] if sd.default.device else None
if default_input is None:
    st.error("No audio input device detected! Please check your microphone.")


# Parameters for live audio capture
CHUNK = 2048
RATE = 44100  # Sampling rate in Hz
HUMMING_LOW_FREQ = 20000  # Frequency range for humming (low)
HUMMING_HIGH_FREQ = 30000  # Frequency range for humming (high)

# Queue to store audio data
audio_queue = queue.Queue()

# Function to map the airway patency score to a color
def get_color(score):
    if 0 <= score <= 0.3:
        return 'red'
    elif 0.3 < score <= 0.6:
        return 'green'
    else:
        return 'blue'

# Function to calculate the airway patency score using STFT
def calculate_patency_score(audio_data):
    f, t, Zxx = stft(audio_data, fs=RATE, window='hamming', nperseg=CHUNK,
                     noverlap=CHUNK // 2, nfft=2 * CHUNK, boundary='zeros', padded=True)
    freq_indices = np.where((f >= HUMMING_LOW_FREQ) & (f <= HUMMING_HIGH_FREQ))[0]
    filtered_Zxx = np.abs(Zxx[freq_indices, :])
    if filtered_Zxx.size == 0:
        return 0
    stft_intensity = 20 * np.log10(np.abs(filtered_Zxx) + 1e-6)
    avg_intensity = np.mean(stft_intensity)
    score = min(max(avg_intensity / 100, 0), 1)
    return score

# Callback function to capture audio in real-time
def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")
    audio_queue.put(indata[:, 0])  # Add audio data to the queue

# Streamlit app layout
st.title("Live Airway Patency Score")
st.write("Humming into the microphone changes the leaf color based on your airway patency score.")

# Live visualization with Streamlit
if st.button("Start Listening"):
    st.write("Listening... Please hum!")

    # Setting up the Matplotlib figure
    fig, ax = plt.subplots()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    leaf = patches.Ellipse((5, 5), 8, 10, fc='green', ec='black')
    ax.add_patch(leaf)
    placeholder = st.empty()
    placeholder.pyplot(fig)

    # Stream audio and update visualization
    try:
        with sd.InputStream(callback=audio_callback, channels=1, samplerate=RATE, blocksize=CHUNK):
            for _ in range(200):  # Run the loop for ~20 seconds (adjust as needed)
                if not audio_queue.empty():
                    audio_data = audio_queue.get()
                    score = calculate_patency_score(audio_data)
                    leaf.set_facecolor(get_color(score))
                    ax.set_title(f'Patency Score: {score:.2f}', fontsize=14)
                    placeholder.pyplot(fig)  # Update the figure in Streamlit
    except Exception as e:
        st.error(f"An error occurred: {e}")

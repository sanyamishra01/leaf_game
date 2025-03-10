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





# Parameters
CHUNK = 2048
RATE = 44100
HUMMING_LOW_FREQ = 100
HUMMING_HIGH_FREQ = 300

# Queue for audio data
audio_queue = queue.Queue()

# Function to map AP score to colors (Light Green to Dark Green)
def get_color(score):
    if score < 0.3:
        return '#b8e994'  # Light Green
    elif 0.3 <= score <= 0.6:
        return '#55efc4'  # Normal Green
    else:
        return '#00b894'  # Dark Green

# Function to calculate airway patency score using STFT
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

# Function to calculate health stock dynamically
def calculate_health_stock(ap_ranges, amount_invested=100):
    weighted_sum = (ap_ranges['>0.6'] * 4 + ap_ranges['0.5–0.6'] * 3 +
                    ap_ranges['0.3–0.4'] * 2 + ap_ranges['<0.2'] * 1)
    total_counts = sum(ap_ranges.values())
    if total_counts == 0:
        return 0
    weighted_average = weighted_sum / total_counts
    return amount_invested * weighted_average

# Callback function for real-time audio capture
def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")
    audio_queue.put(indata[:, 0])  # Add audio data to the queue

# Streamlit app layout
st.title("Live Airway Patency Visualizer and Health Stock Analytics")
st.write("Humming changes the leaf color and calculates your health stock dynamically.")

# Initialize player analytics and health stock
ap_ranges = {'<0.2': 0, '0.3–0.4': 0, '0.5–0.6': 0, '>0.6': 0}
amount_invested = 100  # Set a default investment amount

# Start button
if st.button("Start Listening"):
    st.write("Listening... Please hum!")

    # Matplotlib figure setup
    fig, ax = plt.subplots()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    leaf = patches.Ellipse((5, 5), 8, 10, fc='green', ec='black')
    ax.add_patch(leaf)
    placeholder = st.empty()  # Placeholder for live plot

    # Dashboard placeholders
    analytics_placeholder = st.empty()
    rankings_placeholder = st.empty()

    # Simulate live data processing
    try:
        with sd.InputStream(callback=audio_callback, channels=1, samplerate=RATE, blocksize=CHUNK):
            for _ in range(200):  # Adjust the loop for ~20 seconds
                if not audio_queue.empty():
                    audio_data = audio_queue.get()
                    score = calculate_patency_score(audio_data)

                    # Update color based on score
                    leaf.set_facecolor(get_color(score))
                    ax.set_title(f'Patency Score: {score:.2f}', fontsize=14)
                    placeholder.pyplot(fig)

                    # Update analytics
                    if score < 0.2:
                        ap_ranges['<0.2'] += 1
                    elif 0.3 <= score <= 0.4:
                        ap_ranges['0.3–0.4'] += 1
                    elif 0.5 <= score <= 0.6:
                        ap_ranges['0.5–0.6'] += 1
                    elif score > 0.6:
                        ap_ranges['>0.6'] += 1

                    # Calculate health stock
                    health_stock = calculate_health_stock(ap_ranges, amount_invested)

                    # Update analytics and rankings
                    analytics_placeholder.write(f"""
                    **Live Analytics**
                    - AP < 0.2: {ap_ranges['<0.2']}
                    - AP 0.3–0.4: {ap_ranges['0.3–0.4']}
                    - AP 0.5–0.6: {ap_ranges['0.5–0.6']}
                    - AP > 0.6: {ap_ranges['>0.6']}
                    - **Health Stock**: {health_stock:.2f}
                    """)

                    # Dummy rankings for demonstration
                    rankings_placeholder.write(f"""
                    **Player Rankings**
                    1. Player A: 1200 Health Stock
                    2. Player B: 1100 Health Stock
                    3. You: {health_stock:.2f} Health Stock
                    """)
    except Exception as e:
        st.error(f"An error occurred: {e}")

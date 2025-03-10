# import streamlit as st
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib.patches as patches
# from scipy.signal import stft
# import sounddevice as sd
# import queue

# # Parameters
# CHUNK = 2048
# RATE = 44100
# HUMMING_LOW_FREQ = 100
# HUMMING_HIGH_FREQ = 300

# audio_queue = queue.Queue()

# def get_color(score):
#     if score < 0.3:
#         return '#b8e994'  # Light Green
#     elif 0.3 <= score <= 0.6:
#         return '#55efc4'  # Normal Green
#     else:
#         return '#00b894'  # Dark Green

# def calculate_patency_score(audio_data):
#     f, t, Zxx = stft(audio_data, fs=RATE, window='hamming', nperseg=CHUNK,
#                      noverlap=CHUNK // 2, nfft=2 * CHUNK, boundary='zeros', padded=True)
#     freq_indices = np.where((f >= HUMMING_LOW_FREQ) & (f <= HUMMING_HIGH_FREQ))[0]
#     filtered_Zxx = np.abs(Zxx[freq_indices, :])
#     if filtered_Zxx.size == 0:
#         return 0
#     stft_intensity = 20 * np.log10(np.abs(filtered_Zxx) + 1e-6)
#     avg_intensity = np.mean(stft_intensity)
#     score = min(max(avg_intensity / 100, 0), 1)
#     return score

# def audio_callback(indata, frames, time, status):
#     if status:
#         print(f"Status: {status}")
#     if indata is not None:
#         print(f"Audio data captured: {indata.shape}")
#         audio_queue.put(indata[:, 0])

# # Streamlit App
# st.title("Live Audio Analyzer")
# st.write("Humming changes graph color dynamically.")

# fig, ax = plt.subplots()
# ax.set_xlim(0, 10)
# ax.set_ylim(0, 10)
# leaf = patches.Ellipse((5, 5), 8, 10, fc='green', ec='black')
# ax.add_patch(leaf)
# placeholder = st.empty()

# if st.button("Start Listening"):
#     st.write("Listening for 7 seconds... Please hum!")
#     try:
#         with sd.InputStream(callback=audio_callback, channels=1, samplerate=RATE, blocksize=CHUNK):
#             sd.sleep(7000)  # Wait for 7 seconds
#             while not audio_queue.empty():
#                 audio_data = audio_queue.get()
#                 score = calculate_patency_score(audio_data)
#                 leaf.set_facecolor(get_color(score))
#                 ax.set_title(f"Patency Score: {score:.2f}", fontsize=14)
#                 fig.canvas.draw()
#                 placeholder.pyplot(fig)
#     except Exception as e:
#         st.error(f"Error during audio capture: {e}")


import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.signal import stft
import sounddevice as sd
import queue
import time
import matplotlib

# Set up Matplotlib backend for deployment
matplotlib.use('Agg')  # Non-interactive backend for cloud environments

# Parameters for live audio capture
CHUNK = 1024
RATE = 44100
HUMMING_LOW_FREQ = 80  # Lower bound for human humming
HUMMING_HIGH_FREQ = 300  # Upper bound for human humming
NOISE_THRESHOLD = 50  # Minimum signal magnitude to consider

# Queue for audio data
audio_queue = queue.Queue()

# Shades of green for AP score mapping
def get_color(score):
    if score < 0.3:
        return '#b8e994'  # Light Green
    elif 0.3 <= score <= 0.6:
        return '#55efc4'  # Normal Green
    else:
        return '#00b894'  # Dark Green

# Function to calculate airway patency score from audio input
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

# Callback function for audio input
def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")
    audio_queue.put(indata[:, 0])  # Add audio data to the queue

# Streamlit App
st.title("Live Audio Analyzer with Real-Time Visualization")
st.write("Hum into your microphone for 7 seconds. The graph dynamically changes color based on the AP score.")

# Matplotlib setup for the oval leaf shape
fig, ax = plt.subplots()
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
leaf = patches.Ellipse((5, 5), 8, 10, fc='green', ec='black')
ax.add_patch(leaf)
placeholder = st.empty()

if st.button("Start Listening"):
    st.write("Listening for 7 seconds... Please hum!")

    # Initialize start time
    start_time = time.time()
    duration = 7  # Duration in seconds

    # Start audio capture
    try:
        with sd.InputStream(callback=audio_callback, channels=1, samplerate=RATE, blocksize=CHUNK):
            while time.time() - start_time < duration:  # Loop for 7 seconds
                if not audio_queue.empty():
                    audio_data = audio_queue.get()

                    # Calculate AP score
                    score = calculate_patency_score(audio_data)

                    # Update leaf color and graph title
                    leaf.set_facecolor(get_color(score))
                    ax.set_title(f'Patency Score: {score:.2f}', fontsize=14)

                    # Render the updated graph
                    fig.canvas.draw()
                    placeholder.pyplot(fig)

            st.write("Finished listening! Animation stopped.")
    except Exception as e:
        st.error(f"Error during audio capture: {e}")

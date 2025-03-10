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
from scipy.signal import stft
import sounddevice as sd
import queue
import time

# Parameters
CHUNK = 1024
RATE = 44100
DURATION = 7  # Record for 7 seconds
HUMMING_LOW_FREQ = 80
HUMMING_HIGH_FREQ = 300
THRESHOLDS = [0.2, 0.3, 0.4, 0.5, 0.6]

# Queue for audio data
audio_queue = queue.Queue()

# Initialize counters
threshold_counts = {
    ">0.6": 0,
    "0.5-0.6": 0,
    "0.3-0.4": 0,
    "<0.2": 0
}
cumulative_ap = 0  # Sum of all AP values
ap_updates = 0  # Number of AP updates

# Function to calculate airway patency score
def calculate_ap(audio_data):
    f, t, Zxx = stft(audio_data, fs=RATE, window='hamming', nperseg=CHUNK,
                     noverlap=CHUNK // 2, nfft=2 * CHUNK, boundary='zeros', padded=True)
    freq_indices = np.where((f >= HUMMING_LOW_FREQ) & (f <= HUMMING_HIGH_FREQ))[0]
    filtered_Zxx = np.abs(Zxx[freq_indices, :])
    if filtered_Zxx.size == 0:
        return 0
    stft_intensity = 20 * np.log10(np.abs(filtered_Zxx) + 1e-6)
    avg_intensity = np.mean(stft_intensity)
    return min(max(avg_intensity / 100, 0), 1)

# Callback for audio stream
def audio_callback(indata, frames, time, status):
    audio_queue.put(indata[:, 0])  # Save the first channel of audio

# Streamlit app
st.title("Real-Time AP Monitoring")
st.write("This app records live audio for 7 seconds, calculates AP values dynamically, and tracks thresholds.")

# Input for investment amount
investment = st.number_input("Enter the amount invested (in dollars):", min_value=0.0, step=0.01)

# Matplotlib setup for dynamic graph
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_xlim(0, DURATION)
ax.set_ylim(0, 1)
ax.set_xlabel("Time (s)")
ax.set_ylabel("AP Score")
st.pyplot(fig)

# Start recording
if st.button("Start Recording"):
    st.write("Recording... Please hum for 7 seconds.")

    # Start audio stream
    try:
        start_time = time.time()
        with sd.InputStream(callback=audio_callback, channels=1, samplerate=RATE, blocksize=CHUNK):
            # Variables for graph
            ap_values = []
            timestamps = []

            # Record for 7 seconds
            while time.time() - start_time < DURATION:
                if not audio_queue.empty():
                    audio_data = audio_queue.get()
                    ap = calculate_ap(audio_data)
                    ap_values.append(ap)
                    timestamps.append(time.time() - start_time)

                    # Update thresholds
                    if ap > 0.6:
                        threshold_counts[">0.6"] += 1
                    elif 0.5 <= ap <= 0.6:
                        threshold_counts["0.5-0.6"] += 1
                    elif 0.3 <= ap <= 0.4:
                        threshold_counts["0.3-0.4"] += 1
                    elif ap < 0.2:
                        threshold_counts["<0.2"] += 1

                    # Update cumulative AP
                    global cumulative_ap, ap_updates  # Declare before modifying
                    cumulative_ap += ap
                    ap_updates += 1

                    # Update graph
                    line.set_data(timestamps, ap_values)
                    ax.set_xlim(0, max(1, timestamps[-1]))
                    ax.set_ylim(0, 1)
                    st.pyplot(fig)

            st.write("Recording finished!")

    except Exception as e:
        st.error(f"Error: {e}")

    # Calculate weighted average of AP values
    total_weights = sum(threshold_counts.values())
    if total_weights > 0:
        weighted_average = (
            (threshold_counts[">0.6"] * 1.0 +
             threshold_counts["0.5-0.6"] * 0.8 +
             threshold_counts["0.3-0.4"] * 0.5 +
             threshold_counts["<0.2"] * 0.2) / total_weights
        )
    else:
        weighted_average = 0

    # Calculate health stock value
    health_stock = investment * weighted_average

    # Display results
    st.write("### Results:")
    st.write(f"AP Thresholds Crossed:")
    st.write(f" - Greater than 0.6: {threshold_counts['>0.6']} times")
    st.write(f" - Between 0.5 and 0.6: {threshold_counts['0.5-0.6']} times")
    st.write(f" - Between 0.3 and 0.4: {threshold_counts['0.3-0.4']} times")
    st.write(f" - Less than 0.2: {threshold_counts['<0.2']} times")
    st.write(f"Weighted Average of AP Values: {weighted_average:.2f}")
    st.write(f"Health Stock Value: ${health_stock:.2f}")

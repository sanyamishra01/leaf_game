import streamlit as st
import numpy as np
from scipy.signal import stft
import wave
import io
from pydub import AudioSegment
from pydub.utils import which

# Manually set FFmpeg path
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# Parameters for AP calculation
HUMMING_LOW_FREQ = 80  # Lower bound for human humming frequency
HUMMING_HIGH_FREQ = 300  # Upper bound for human humming frequency

# Initialize counters and variables
threshold_counts = {
    ">0.6": 0,
    "0.5-0.6": 0,
    "0.3-0.4": 0,
    "<0.2": 0
}
weighted_sum = 0
total_counts = 0

# Function to calculate AP scores over time
def calculate_ap(audio_data, rate):
    f, t, Zxx = stft(audio_data, fs=rate, window='hamming', nperseg=1024,
                     noverlap=512, nfft=2048, boundary='zeros', padded=True)
    freq_indices = np.where((f >= HUMMING_LOW_FREQ) & (f <= HUMMING_HIGH_FREQ))[0]
    filtered_Zxx = np.abs(Zxx[freq_indices, :])
    if filtered_Zxx.size == 0:
        return [0] * len(t)  # Return zero for all time steps if no data
    stft_intensity = 20 * np.log10(filtered_Zxx + 1e-6)
    avg_intensity = np.mean(stft_intensity, axis=0)  # Compute intensity over time
    ap_scores = np.clip(avg_intensity / 100, 0, 1)  # Normalize between 0 and 1
    return ap_scores

# Function to get color based on AP score
def get_color(ap):
    if ap < 0.2:
        return '#b8e994'  # Light green
    elif 0.2 <= ap <= 0.4:
        return '#55efc4'  # Normal green
    elif 0.4 < ap < 0.6:
        return '#00b894'  # Darker green
    else:
        return '#006d5b'  # Darkest green

# Function to convert audio files to WAV format
def convert_to_wav(uploaded_file):
    try:
        audio = AudioSegment.from_file(uploaded_file)  # Read any format
        buffer = io.BytesIO()  # Create a buffer to store WAV data
        audio.export(buffer, format="wav")  # Convert to WAV
        buffer.seek(0)
        return wave.open(buffer, "rb")  # Open as a WAV file
    except Exception as e:
        st.error(f"Error processing audio file: {e}")
        return None

# Streamlit app
st.title("Dynamic AP Analysis with Health Stock Calculation")
st.write("Upload an audio file (any format) to calculate AP values dynamically and visualize the results.")

# Input for investment amount
investment = st.number_input("Enter the amount invested (in ₹):", min_value=0.0, step=0.01)

# File upload
uploaded_file = st.file_uploader("Upload an audio file (any format):", type=["wav", "mp3", "m4a", "aac", "flac"])

if uploaded_file is not None:
    try:
        # Convert the uploaded file to WAV format
        wav_file = convert_to_wav(uploaded_file)
        if wav_file is None:
            st.error("Could not process the uploaded file.")
            st.stop()

        # Read the WAV file
        rate = wav_file.getframerate()
        frames = wav_file.getnframes()
        audio_data = np.frombuffer(wav_file.readframes(frames), dtype=np.int16)

        # Calculate AP scores over time
        ap_scores = calculate_ap(audio_data, rate)

        # Determine animation duration and update interval
        ANIMATION_DURATION = 7.0  # Total duration for animation (in seconds)
        interval = ANIMATION_DURATION / len(ap_scores)  # Time interval per update

        # Create a Matplotlib figure for the oval visualization
        fig, ax = plt.subplots()
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")  # Turn off the axes for better visualization
        oval = patches.Ellipse((5, 5), width=8, height=10, fc='white', ec='black')
        ax.add_patch(oval)
        placeholder = st.empty()
        ap_value_placeholder = st.empty()  # Placeholder for AP value display

        # Initialize result containers
        thresholds_placeholder = st.empty()
        health_stock_placeholder = st.empty()

        # Analyze AP thresholds and compute weighted sum dynamically
        for ap in ap_scores:
            # Update counters for thresholds
            total_counts += 1  # Increment the total count
            if ap > 0.6:
                threshold_counts[">0.6"] += 1
                weighted_sum += ap * 1.0  # Weight of 1.0
            elif 0.5 <= ap <= 0.6:
                threshold_counts["0.5-0.6"] += 1
                weighted_sum += ap * 0.8  # Weight of 0.8
            elif 0.3 <= ap <= 0.4:
                threshold_counts["0.3-0.4"] += 1
                weighted_sum += ap * 0.5  # Weight of 0.5
            elif ap < 0.2:
                threshold_counts["<0.2"] += 1
                weighted_sum += ap * 0.2  # Weight of 0.2

            # Calculate health stock dynamically
            if total_counts > 0:
                weighted_average = weighted_sum / total_counts
            else:
                weighted_average = 0
            health_stock = investment * weighted_average

            # Update oval color dynamically
            color = get_color(ap)
            oval.set_facecolor(color)
            placeholder.pyplot(fig)

            # Display the current AP score above the graph
            ap_value_placeholder.markdown(f"### Current AP Score: **{ap:.2f}**")

            # Update results dynamically
            thresholds_placeholder.write("### AP Thresholds Crossed (Dynamic):")
            thresholds_placeholder.write(f" - Greater than 0.6: {threshold_counts['>0.6']} times")
            thresholds_placeholder.write(f" - Between 0.5 and 0.6: {threshold_counts['0.5-0.6']} times")
            thresholds_placeholder.write(f" - Between 0.3 and 0.4: {threshold_counts['0.3-0.4']} times")
            thresholds_placeholder.write(f" - Less than 0.2: {threshold_counts['<0.2']} times")
            health_stock_placeholder.write(f"Health Stock Value (Dynamic): ₹{health_stock:.2f}")

            # Pause proportionally for smooth updates within 7 seconds
            time.sleep(0.5)

    except Exception as e:
        st.error(f"Error processing audio file: {e}")

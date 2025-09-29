import streamlit as st
import numpy as np
from scipy.signal import stft
import wave
import io
from pydub import AudioSegment
from pydub.utils import which
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set FFmpeg path
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

# Parameters for AP calculation
HUMMING_LOW_FREQ = 80
HUMMING_HIGH_FREQ = 300

# Function to calculate AP scores
def calculate_ap(audio_data, rate):
    f, t, Zxx = stft(audio_data, fs=rate, window='hamming', nperseg=1024,
                     noverlap=512, nfft=2048, boundary='zeros', padded=True)
    freq_indices = np.where((f >= HUMMING_LOW_FREQ) & (f <= HUMMING_HIGH_FREQ))[0]
    filtered_Zxx = np.abs(Zxx[freq_indices, :])
    if filtered_Zxx.size == 0:
        return np.zeros(len(t))
    stft_intensity = 20 * np.log10(filtered_Zxx + 1e-6)
    avg_intensity = np.mean(stft_intensity, axis=0)
    return np.clip(avg_intensity / 100, 0, 1)

# Function to get color based on AP
def get_color(ap):
    if ap < 0.2:
        return '#b8e994'
    elif 0.2 <= ap <= 0.4:
        return '#55efc4'
    elif 0.4 < ap < 0.6:
        return '#00b894'
    else:
        return '#006d5b'

# Convert audio to WAV
def convert_to_wav(uploaded_file):
    try:
        audio = AudioSegment.from_file(uploaded_file)
        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        buffer.seek(0)
        return wave.open(buffer, "rb")
    except Exception as e:
        st.error(f"Error processing audio file: {e}")
        return None

# Streamlit UI
st.title("Dynamic AP Analysis with Health Stock Calculation")
st.write("Upload an audio file to calculate AP values dynamically.")

investment = st.number_input("Enter the amount invested (in ₹):", min_value=0.0, step=0.01)
uploaded_file = st.file_uploader("Upload an audio file:", type=["wav", "mp3", "m4a", "aac", "flac"])

if uploaded_file is not None:
    try:
        wav_file = convert_to_wav(uploaded_file)
        if wav_file is None:
            st.stop()

        rate = wav_file.getframerate()
        frames = wav_file.getnframes()
        audio_data = np.frombuffer(wav_file.readframes(frames), dtype=np.int16)
        ap_scores = calculate_ap(audio_data, rate)

        # Subsample for speed
        max_steps = 50
        if len(ap_scores) > max_steps:
            indices = np.linspace(0, len(ap_scores)-1, max_steps, dtype=int)
            ap_scores = ap_scores[indices]

        # Vectorized weight calculation
        ap_scores = np.array(ap_scores)
        weights = np.where(ap_scores > 0.6, 1.0,
                  np.where((ap_scores > 0.5) & (ap_scores <= 0.6), 0.8,
                  np.where((ap_scores >= 0.3) & (ap_scores <= 0.5), 0.5,
                  np.where(ap_scores < 0.3, 0.2, 0))))
        weighted_avg = np.cumsum(ap_scores * weights) / np.arange(1, len(ap_scores)+1)
        health_stock = investment * weighted_avg

        # Threshold counts
        threshold_counts = {
            ">0.6": np.sum(ap_scores > 0.6),
            "0.5-0.6": np.sum((ap_scores >= 0.5) & (ap_scores <= 0.6)),
            "0.3-0.5": np.sum((ap_scores >= 0.3) & (ap_scores <= 0.4)),
            "<0.3": np.sum(ap_scores < 0.2)
        }

        # Initialize placeholders
        placeholder = st.empty()
        ap_value_placeholder = st.empty()
        thresholds_placeholder = st.empty()
        health_stock_placeholder = st.empty()

        # Matplotlib figure
        fig, ax = plt.subplots()
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")
        oval = patches.Ellipse((5, 5), width=8, height=10, fc='white', ec='black')
        ax.add_patch(oval)

        # Fast animation loop
        for i, ap in enumerate(ap_scores):
            oval.set_facecolor(get_color(ap))
            placeholder.pyplot(fig)

            ap_value_placeholder.markdown(f"### Current AP Score: **{ap:.2f}**")
            thresholds_placeholder.write(
                f"### AP Thresholds Crossed (Dynamic):\n"
                f" - >0.6: {threshold_counts['>0.6']} times\n"
                f" - 0.5-0.6: {threshold_counts['0.5-0.6']} times\n"
                f" - 0.3-0.4: {threshold_counts['0.3-0.5']} times\n"
                f" - <0.2: {threshold_counts['<0.3']} times"
            )
            health_stock_placeholder.write(f"Health Stock Value (Dynamic): ₹{health_stock[i]:.2f}")

        st.success("AP calculation completed!")

    except Exception as e:
        st.error(f"Error processing audio file: {e}")

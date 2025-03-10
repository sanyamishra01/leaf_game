import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import pyaudio
import struct
from scipy.signal import stft

# Parameters for live audio capture
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Frequency range for humming (in Hz)
HUMMING_LOW_FREQ = 20000
HUMMING_HIGH_FREQ = 30000

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

# Streamlit app layout
st.title("Live Airway Patency Score")
st.write("Humming into the microphone changes the leaf color based on your airway patency score.")

# Add a button to start the project
if st.button("Start Listening"):
    st.write("Listening... Please hum!")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)
    
    # Live visualization
    fig, ax = plt.subplots()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    leaf = patches.Ellipse((5, 5), 8, 10, fc='green', ec='black')
    ax.add_patch(leaf)
    plt.title("Live Patency Visualizer")

    try:
        while True:
            raw_data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.array(struct.unpack(str(CHUNK) + 'h', raw_data), dtype=np.int16)
            score = calculate_patency_score(audio_data)
            leaf.set_facecolor(get_color(score))
            ax.set_title(f'Patency Score: {score:.2f}', fontsize=14)
            st.pyplot(fig)
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
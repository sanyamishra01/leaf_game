FROM python:3.11-slim

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    libasound2 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the app
CMD ["sh", "-c", "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"]

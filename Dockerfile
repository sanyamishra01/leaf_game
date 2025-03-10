FROM jrottenberg/ffmpeg:4.4-slim

# Set the working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the app
CMD ["streamlit", "run", "app.py", "--server.port", "$PORT", "--server.address", "0.0.0.0"]

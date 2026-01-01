# Use an official lightweight Python image.
# 3.9-slim is a good balance of size and compatibility.
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any).
# reportlab sometimes needs build tools or fonts.
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements verification
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]

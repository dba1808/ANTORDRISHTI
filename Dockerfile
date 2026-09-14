FROM python:3.9-slim

# Prevent Python from creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Show Python output immediately
ENV PYTHONUNBUFFERED=1

# Qt configuration
ENV QT_X11_NO_MITSHM=1

WORKDIR /app

# --------------------------------------------------
# System dependencies
# --------------------------------------------------

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-keysyms1 \
    libxcb-image0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxkbcommon-x11-0 \
    libfontconfig1 \
    libfreetype6 \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Python dependencies
# --------------------------------------------------

COPY requirements-docker.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-docker.txt

# --------------------------------------------------
# Application
# --------------------------------------------------

COPY antordrishti ./antordrishti

# Application data/log directories
RUN mkdir -p \
    /root/.antordrishti \
    /root/.antordrishti/scans \
    /app/antordrishti/logs

# --------------------------------------------------
# Start application
# --------------------------------------------------

CMD ["python", "antordrishti/main.py"]
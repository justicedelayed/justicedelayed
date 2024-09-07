# Base image with a specific version for consistency
FROM python:3.11-slim-bookworm AS base

# Set environment variables for UID, GID, and user/group names
ENV WORKDIR=/code

# Set the working directory in the container
WORKDIR $WORKDIR

# Copy the current directory contents into the container at the working directory
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libglib2.0-0 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libgbm1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libpango-1.0-0 \
    libcups2 \
    libdrm2 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt $WORKDIR/
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Main stage for the scraping component
FROM base AS main
CMD ["python", "-u", "navigator.py"]
#CMD ["python", "-u", "/code/src/navigator.py"]

# Process stage for the HTML processing component
FROM base AS process
CMD ["python", "-u", "process_html.py"]
#CMD ["python", "-u", "/code/src/process_html.py"]


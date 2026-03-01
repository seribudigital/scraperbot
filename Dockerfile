# Menggunakan base image Python versi slim
FROM python:3.13-slim

# Menyiapkan environment variable agar interaksi Python non-interaktif
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Mengatur direktori kerja di dalam kontainer
WORKDIR /app

# Menginstal dependensi sistem yang dibutuhkan oleh Playwright (Chromium)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    libgbm-dev \
    libgtk-3-0 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Menyalin file konfigurasi dependensi Python
# Force cache invalidation for pip install, updated: 2026-03-02
COPY requirements.txt .

# Menginstal library Python
RUN pip install --no-cache-dir -r requirements.txt

# Menginstal browser spesifik untuk Playwright (Chromium saja) beserta dependensi OS tambahannya
RUN playwright install chromium
RUN playwright install-deps chromium

# Menyalin seluruh kode sumber bot ke dalam kontainer
COPY . .

# Membuat folder log jika belum ada di dalam kontainer
RUN mkdir -p logs

# Menjalankan bot saat kontainer dihidupkan
CMD ["python", "bot.py"]

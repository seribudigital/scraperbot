# Project Specifications: Google Maps Scraper to Airtable via Telegram Bot

## Overview
Sistem otomatisasi untuk men-scrape data dari Google Maps, menyimpannya ke Airtable, dan mengendalikannya melalui antarmuka Telegram Bot. Proyek ini dibangun menggunakan Python.

## Core Features

### 1. Google Maps Scraping (Playwright)
- Menggunakan **Playwright** (Python) untuk navigasi dan ekstraksi data dari Google Maps secara headless/non-headless.
- Mampu melakukan pencarian berdasarkan kata kunci dan lokasi.
- Mengekstrak informasi penting dari setiap tempat bisnis (Nama, Alamat, Nomor Telepon, Website, Rating, Jumlah Ulasan, dll).
- Menangani paginasi (scroll panel sebelah kiri untuk memuat lebih banyak hasil).

### 2. Airtable Integration (via MCP)
- Menggunakan framework Model Context Protocol (MCP) untuk berinteraksi dengan basis data Airtable.
- Melakukan pemetaan data (data mapping) dari hasil ekstraksi Playwright ke kolom-kolom yang sesuai di tabel Airtable.
- Mendukung operasi insert (menambahkan data baru) dan update (memperbarui data jika entri bisnis tersebut sudah ada di database untuk menghindari duplikasi).

### 3. Telegram Bot Interface
- Menggunakan library seperti `python-telegram-bot` atau `aiogram` untuk menyediakan antarmuka interaktif yang mudah digunakan.
- Perintah dasar yang dibutuhkan:
  - `/start`: Menampilkan pesan selamat datang, panduan, dan status sistem.
  - `/scrape [keyword] di [lokasi]`: Memulai proses scraping (contoh: `/scrape kedai kopi di Jakarta Selatan`).
  - `/status`: Mengecek status proses scraping yang sedang berjalan (progress).
  - `/stop`: Menghentikan proses scraping secara aman.
- Memberikan notifikasi realtime ke pengguna via pesan Telegram (contoh: "Memulai scraping...", "Ditemukan 50 data...", "Berhasil menyimpan 45 data ke Airtable").

## Tech Stack
- **Bahasa Pemrograman**: Python 3.10+
- **Scraping Engine**: `playwright`
- **Database/Storage**: Airtable via integrasi MCP (Model Context Protocol)
- **Bot Interface**: `python-telegram-bot` (REST API / Polling)
- **Environment Management**: `dotenv` untuk menyimpan API Keys (Telegram Token, Airtable API Key / MCP config)
- **Dependency Management**: `pip` dengan `requirements.txt`

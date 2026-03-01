# AI Standard Operating Procedure (SOP) & Instructions

Dokumen ini berisi pedoman sistematis yang WAJIB diikuti oleh AI saat menulis, memodifikasi, merancang, atau men-debug kode dalam proyek "Google Maps Scraper to Airtable via Telegram Bot".

## 1. Penanganan Log dan Error (Error Handling & Logging)
- **Wajib Menggunakan `try...except`**: Setiap operasi berisiko tinggi seperti request jaringan, interaksi DOM browser dengan Playwright, dan pemanggilan API Airtable harus dibungkus dengan `try...except`.
- **Implementasi Centralized Logging**: Jangan gunakan fungsi `print()` biasa untuk production. Gunakan library `logging` bawaan Python.
- Setiap error, exception, peringatan, dan info penting harus dicatat ke dalam file eksternal (misalnya: `logs/scraper.log` dan `logs/error.log`) beserta `traceback`-nya.
- **Resiliensi Telegram Bot**: Bot Telegram tidak boleh mati mendadak (crash silently) saat terjadi error di backend. Pastikan bot menangkap exception dan mengirimkan pesan notifikasi kegagalan/error kepada pengguna/admin agar transparan.

## 2. Instruksi Penanganan Google Maps Scraping
- **Penanganan Cookie Pop-ups**: Akses bot ke Google Maps sering memicu munculnya "Cookie Consent" atau pop-up Kebijakan Privasi layar penuh. AI WAJIB menyertakan logika pengecekan DOM untuk mendeteksi elemen pop-up ini dan secara otomatis mengklik "Accept" / "Setuju" / "Decline" sebelum melakukan scraping data.
- **Dynamic Scrolling**: Daftar lokasi Google Maps dimuat secara dinamis saat panel sebelah kiri digeser ke bawah (lazy loading). Gunakan logika loop untuk me-scroll panel tersebut sampai mentok atau batas limit yang diminta pengguna tercapai. **Gunakan Explicit Waits** (`page.wait_for_selector` / `locator.wait_for`) alih-alih `time.sleep()` yang statis.
- **Handling Selektor DOM Rentan**: Class HTML Google Maps sangat tidak stabil (obfuscated). Coba gunakan XPath berdasarkan hirarki dan teks atribut ARIA (`aria-label`) jika memungkinkan agar scraper tidak cepat rusak.

## 3. Integrasi Airtable yang Rapi dan Aman
- **Data Cleansing (Kerapian Data)**: Sebelum data dikirimkan ke Airtable, pastikan data telah dibersihkan secara proaktif:
  - Hapus whitespace atau spasi ganda (`.strip()`).
  - Standarisasi nomor telepon (misal: membuang karakter aneh, mendahulukan kode regional if re levant).
  - Validasi URL website dan berikan skema `https://` jika belum ada.
- **Anti-Duplikasi (Idempotensi)**: Saat memasukkan data ke Airtable, pertama-tama periksa (kueri) apakah data spesifik tersebut (bisa dengan acuan Nama + Nomor Telepon atau Nama + Alamat) sudah terekam di tabel Airtable. Lakukan *Update* jika sudah ada, atau *Insert* jika belum (logic Upsert).
- Manfaatkan protokol MCP untuk format request yang terstruktur. Pastikan skema data yang dikirim (*payload*) identik ketat dengan kolom yang dikonfigurasi pada Airtable.

## 4. Standar Penulisan Kode (Code Style)
- Gunakan modul yang terpisah dan terorganisir, contoh: `bot.py` (untuk event Telegram), `scraper.py` (logic Playwright), `airtable_mcp.py` (interface database), dan `logger.py`.
- Terapkan **Type Hints** (`def action(name: str) -> bool:`) secara merata di seluruh base code Python.
- Selalu tambahkan **Docstrings** di atas definisi class atau fungsi utama agar mempermudah pemahaman logika jika diubah di hari lain.

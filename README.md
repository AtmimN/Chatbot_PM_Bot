# PM-Bot: Chatbot Tematik Teori Dasar Manajemen Proyek

Aplikasi chatbot tematik berbasis aturan (*rule-based*) yang dibangun dengan **Python** dan **Flask**. PM-Bot dirancang sebagai asisten interaktif untuk membantu memahami konsep dasar manajemen proyek, seperti fase proyek, metodologi Agile & Waterfall, kerangka kerja Scrum, peran tim (PM, PO, Scrum Master), template dokumen proyek, rekomendasi tools, serta terminologi penting (Scope Creep, KPI, Stakeholder).

Aplikasi ini dilengkapi antarmuka web modern, persistensi riwayat obrolan berbasis **SQLite**, panel statistik/admin, antarmuka baris perintah (**CLI**), modul evaluasi akurasi (**evaluation sweep**), serta pengujian otomatis menyeluruh menggunakan **pytest**.

---

## Fitur Utama

- **Mesin NLP Berbasis Aturan Cerdas**: Menggabungkan tiga metrik kemiripan kata: *Jaccard Similarity* (40%), *SequenceMatcher / Levenshtein-like Fuzzy Matching* (30%), dan *Pattern Coverage* (30%).
- **Tahan Kesalahan Ketik (*Typo Tolerant*)**: Tetap mengenali variasi kata dan saltik ringan (misal: `"apa itu agle"` tetap teridentifikasi sebagai `apa_itu_agile`).
- **Antarmuka Web Responsif & Tanpa Reload**: Percakapan asinkronus menggunakan Vanilla JavaScript `fetch()` API, aman dari serangan XSS (menggunakan DOM API murni, tanpa `innerHTML`).
- **Mode Belajar Interaktif**: Menampilkan 3 kandidat intent teratas, skor kemiripan, dan pola pencocokan langsung di bawah pesan bot untuk keperluan edukasi dan debugging.
- **Penyimpanan Riwayat Percakapan**: Riwayat percakapan pengguna disimpan secara lokal dalam basis data SQLite per sesi unik.
- **Halaman Statistik & Admin**: Menyediakan ringkasan tingkat pemahaman bot, distribusi pertanyaan per intent, serta log pertanyaan yang belum dikenali untuk memperkaya dataset. Akses dapat diproteksi menggunakan kunci rahasia (*Admin Key*).
- **Antarmuka Terminal (CLI)**: Memungkinkan konsultasi dan debugging langsung di terminal tanpa membuka peramban web.
- **Pengukur Akurasi & Sweep Ambang Batas**: Modul evaluasi untuk menguji akurasi model terhadap data uji CSV dan visualisasi performa dalam bentuk grafik batang ASCII.
- **Pengujian Otomatis Komprehensif**: Dilengkapi 43 uji otomatis (unit test dan integration test) dengan pytest.

---

## Prasyarat Sistem

- Python 3.12 atau versi lebih baru (diuji pada Python 3.12 - 3.14)
- Pip (Python package manager)

---

## Instalasi

1. **Clone repositori atau buka direktori proyek**:
   ```bash
   cd PM-bot
   ```

2. **Buat dan aktifkan lingkungan virtual (virtual environment)**:
   - Di Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - Di Linux / macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Pasang dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Cara Menjalankan Aplikasi Web

Jalankan perintah berikut pada terminal di direktori utama:

```bash
python app.py
```

Setelah server aktif, buka peramban dan akses:
```
http://127.0.0.1:5000
```

### Variabel Lingkungan (*Environment Variables*)

Aplikasi dapat dikonfigurasi menggunakan variabel lingkungan berikut:

| Variabel | Default | Deskripsi |
|---|---|---|
| `SECRET_KEY` | `ganti-dengan-kunci-rahasia` | Kunci enkripsi untuk session cookie Flask |
| `DATABASE` | `chat_history.db` | Jalur file basis data SQLite |
| `THEMES_DIR` | `themes/` | Folder tempat berkas tema JSON disimpan |
| `THRESHOLD` | `0.45` | Ambang batas skor kemiripan klasifikasi intent |
| `ADMIN_KEY` | `""` (kosong) | Kunci pengaman halaman admin (jika kosong, admin terbuka) |
| `MAX_LEN` | `500` | Batas maksimum panjang karakter pesan pengguna |
| `FLASK_DEBUG` | `0` | Mode debug Flask (`1` untuk aktif, `0` untuk nonaktif) |

Contoh menjalankan dengan kunci admin di Windows PowerShell:
```powershell
$env:ADMIN_KEY="kuncirahasia123"; python app.py
```
Akses halaman admin dengan parameter query: `http://127.0.0.1:5000/admin/pm_bot?key=kuncirahasia123`

---

## Cara Menggunakan Antarmuka Terminal (CLI)

Gunakan `cli.py` untuk menguji bot secara cepat di terminal:

```bash
# Menjalankan tema default (pm_bot)
python cli.py

# Memilih tema spesifik
python cli.py --tema pm_bot

# Mengaktifkan mode debug (melihat 3 kandidat intent dan skor kemiripan)
python cli.py --debug

# Menyesuaikan ambang batas skor kemiripan
python cli.py --ambang 0.35
```

Ketik `keluar`, `exit`, atau tekan `Ctrl+C` untuk menutup sesi CLI.

---

## Evaluasi Akurasi Model

Modul `evaluate.py` digunakan untuk menguji akurasi model terhadap 50 kalimat uji independen pada `evaluasi/pm_bot.csv`:

```bash
# Evaluasi pada ambang batas default (0.45)
python evaluate.py --tema pm_bot

# Evaluasi rentang ambang batas (0.30 s.d. 0.70) dengan grafik batang ASCII
python evaluate.py --tema pm_bot --sweep
```

Hasil evaluasi pada dataset `evaluasi/pm_bot.csv` menghasilkan akurasi **100.0%** pada ambang batas rekomendasi (0.35 - 0.45).

---

## Menjalankan Pengujian Otomatis

Seluruh pengujian unit dan integrasi dijalankan menggunakan pytest:

```bash
pytest -v
```

Semua 43 skenario pengujian menggunakan database sementara (*in-memory/tmp_path*) sehingga tidak mengotori database operasional.

---

## Daftar Endpoint REST API

| Metode | URL | Payload / Parameter | Deskripsi |
|---|---|---|---|
| `GET` | `/` | - | Halaman utama pemilihan tema |
| `GET` | `/chat/<theme_id>` | - | Halaman antarmuka chat tema tertentu |
| `GET` | `/admin/<theme_id>` | `?key=<ADMIN_KEY>` | Halaman analitik dan log pertanyaan admin |
| `GET` | `/api/themes` | - | Mengambil daftar tema aktif (JSON) |
| `POST` | `/api/chat` | `{"message": "...", "theme": "pm_bot"}` | Mengirim pesan pengguna dan menerima balasan bot |
| `POST` | `/api/explain` | `{"message": "...", "theme": "pm_bot"}` | Mengambil kandidat intent teratas beserta skornya |
| `GET` | `/api/history/<theme_id>` | - | Mengambil riwayat percakapan sesi pengguna |
| `DELETE` | `/api/history/<theme_id>` | - | Menghapus riwayat percakapan sesi pengguna |
| `GET` | `/api/stats/<theme_id>` | `?key=<ADMIN_KEY>` | Mengambil agregasi statistik frekuensi intent |

---

## Struktur Repositori

```
PM-bot/
├── README.md                 # Dokumentasi utama proyek
├── instruction.md            # Spesifikasi teknis pengerjaan
├── requirements.txt          # Dependensi minimal (Flask, pytest)
├── pytest.ini                # Konfigurasi path pengujian pytest
├── .gitignore                # Berkas dan folder yang diabaikan git
├── template-tema.json        # Kerangka awal untuk membuat tema baru
├── app.py                    # Server Flask, routing web & REST API
├── cli.py                    # Antarmuka baris perintah (terminal)
├── evaluate.py               # Skrip evaluasi performa & sweep ambang batas
│
├── chatbot/                  # Paket modul logika inti chatbot
│   ├── __init__.py           # Ekspor publik paket
│   ├── engine.py             # Mesin NLP praproses, kemiripan, dan validasi
│   └── database.py           # Operasi basis data riwayat percakapan SQLite
│
├── themes/                   # Basis pengetahuan tema dalam format JSON
│   └── pm_bot.json           # Knowledge base PM-Bot (22 intent, 174 pola)
│
├── evaluasi/                 # Kumpulan dataset uji
│   └── pm_bot.csv            # 50 kalimat uji evaluasi
│
├── templates/                # Berkas template Jinja2 HTML
│   ├── base.html             # Layout dasar (induk)
│   ├── index.html            # Halaman katalog tema
│   ├── chat.html             # Halaman antarmuka obrolan
│   ├── admin.html            # Halaman statistik dan analitik admin
│   └── 404.html              # Halaman penanganan error ramah
│
├── static/                   # Aset web statis
│   ├── css/style.css         # Gaya tampilan (responsif & dark mode)
│   └── js/chat.js            # Logika interaksi frontend obrolan aman (anti-XSS)
│
└── tests/                    # Pengujian otomatis (43 tes)
    ├── __init__.py
    ├── test_engine.py        # Pengujian unit mesin inferensi chatbot
    └── test_app.py           # Pengujian integrasi route dan API Flask
```

---

## Alur Kerja Pencocokan Intent

```
[Input Pengguna]
       │
       ▼
1. Praproses Kalimat
   - Huruf kecil (case folding)
   - Konversi tanda hubung ke spasi (mis. "fase-fase" -> "fase fase")
   - Pembersihan simbol & tanda baca
   - Pemetaan kata tidak baku melalui NORMALISASI (mis. "gmn" -> "bagaimana")
   - Pembuangan kata umum melalui STOPWORDS (tanpa membuang kata kunci domain)
       │
       ▼
2. Perhitungan Kemiripan terhadap Seluruh Pola Intent
   Skor = (0.4 × Jaccard) + (0.3 × Fuzzy SequenceMatcher) + (0.3 × Cakupan Pola)
       │
       ▼
3. Evaluasi Ambang Batas (Threshold = 0.45)
   ├── Skor >= 0.45 ──> Intent teridentifikasi ──> Berikan respon yang sesuai
   └── Skor <  0.45 ──> Di bawah ambang       ──> Berikan respon Fallback
```

---

## Panduan Menambah Intent dan Tema Baru

### Menambah Intent pada Tema yang Sudah Ada
1. Buka berkas tema terkait (misal: `themes/pm_bot.json`).
2. Tambahkan objek intent baru ke dalam array `"intents"`:
   ```json
   {
     "tag": "nama_intent_baru",
     "patterns": [
       "pertanyaan pertama",
       "variasi pertanyaan kedua"
     ],
     "responses": [
       "Jawaban penjelasan untuk intent baru."
     ]
   }
   ```
   *Catatan*: Pastikan `tag` menggunakan format `snake_case` huruf kecil dan belum digunakan sebelumnya.
3. Jalankan pengujian tema:
   ```bash
   pytest tests/test_engine.py -k test_semua_tema_termuat_dan_valid
   ```

### Menambah Tema Baru
1. Salin template yang disediakan:
   ```bash
   cp template-tema.json themes/nama_tema_baru.json
   ```
2. Sesuaikan isi file `themes/nama_tema_baru.json`:
   - Kunci `"id"` **wajib sama persis** dengan nama file (tanpa ekstensi `.json`).
   - Isi seluruh 10 kunci wajib.
3. Buat berkas data uji di `evaluasi/nama_tema_baru.csv` dengan kolom `kalimat,intent`.
4. Jalankan evaluasi untuk memastikan akurasi di atas 90%:
   ```bash
   python evaluate.py --tema nama_tema_baru --sweep
   ```

---

## Catatan Keamanan

- **Anti-XSS**: Pesan pengguna dan balasan bot dirender secara aman menggunakan DOM API (`textContent` dan pembuatan node text/anchor), tanpa pemanggilan `innerHTML`. Autoescape Jinja2 tetap aktif.
- **Validasi Input Ketat**: Endpoint POST `/api/chat` memvalidasi tipe data JSON, keberadaan tema, pesan tidak kosong, dan membatasi panjang pesan maksimal 500 karakter.
- **Perlindungan Akses Admin**: Perbandingan kunci admin dilakukan menggunakan fungsi `hmac.compare_digest` untuk mencegah serangan *timing attack*.
- **Keamanan Cookie Sesi**: Pengaturan cookie Flask menggunakan atribut `SESSION_COOKIE_HTTPONLY=True` dan `SESSION_COOKIE_SAMESITE="Lax"`.
- **Header Keamanan**: Header `X-Content-Type-Options: nosniff` disertakan pada setiap respon server.
- **SQL Injection Prevention**: Seluruh interaksi database SQLite menggunakan parameter query bertanda tanya (`?`).

---
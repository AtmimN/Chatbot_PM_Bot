# Instruksi Pembangunan: PM-Bot (Chatbot Tematik Manajemen Proyek)

Dokumen ini adalah **spesifikasi lengkap** untuk membangun aplikasi PM-Bot. Baca seluruhnya sebelum menulis kode (mulai dari Bagian 0), lalu kerjakan sesuai urutan di Bagian 15. Jika ada hal yang tidak dijelaskan, ikuti konvensi aplikasi referensi di `chatbot-tematik-flask/` dan ambil keputusan yang paling sederhana. Untuk hal kecil, tidak perlu bertanya balik.

---

## 0. Peran dan Cara Kerja Kamu

**Peran.** Kamu adalah *senior Python/Flask engineer* sekaligus mentor yang sabar. Pengguna adalah mahasiswa Teknologi Informasi yang akan mengumpulkan, mempresentasikan, dan menjelaskan sendiri kode ini. Karena itu kode harus **bersih, mudah dibaca, dan mudah dijelaskan**, bukan sekadar jalan.

**Prinsip kerja.**
1. **Pelajari referensi dulu.** Baca `chatbot-tematik-flask/referensiProyek.md`, lalu kode di `chatbot-tematik-flask/aplikasi-final/` (terutama `chatbot/engine.py` dan `app.py`) untuk memahami konvensi. Detail di Bagian 2.
2. **Tulis sendiri, jangan menyalin utuh.** Tiru kontraknya (nama fungsi, endpoint, skema database), tetapi tulis implementasi yang rapi dan disesuaikan untuk PM-Bot.
3. **Sederhana dulu.** Pilih solusi paling sederhana yang memenuhi spesifikasi. Jangan menambah fitur, lapisan abstraksi, atau library yang tidak diminta.
4. **Hindari spaghetti code.** Aturan di Bagian 14 **wajib** dipatuhi sejak baris pertama, bukan dirapikan belakangan.
5. **Bertahap dan terverifikasi.** Ikuti urutan Bagian 15 dan jalankan tes pada setiap tahap sebelum lanjut.
6. **Jujur.** Jangan menyatakan tes lulus atau fitur berjalan jika belum benar-benar dijalankan. Laporkan setiap penyimpangan dari spesifikasi beserta alasannya.
7. **Komentar menjelaskan *mengapa*,** bukan mengulang *apa* yang sudah jelas dari kodenya.
8. **Laporan akhir ringkas:** apa yang dibuat, cara menjalankan, hasil `pytest` dan akurasi `evaluate.py`, serta penyimpangan (jika ada).

---

## 1. Konteks dan Tujuan

- Tugas kuliah **Scripting Language** (Teknologi Informasi): membuat **chatbot tematik berbasis aturan (rule-based)**.
- Tema: **PM-Bot**, asisten yang menjawab teori dasar manajemen proyek (fase proyek, Agile/Waterfall/Scrum, peran tim, template dokumen, tools, istilah).
- Aplikasi berupa **web app Flask** dengan antarmuka chat, riwayat percakapan di SQLite, halaman statistik admin, antarmuka terminal (CLI), skrip evaluasi akurasi, dan pengujian otomatis.
- Struktur dan algoritma **mengikuti aplikasi referensi dosen** yang sudah ada di folder kerja (`PM-bot/chatbot-tematik-flask/aplikasi-final/`). Folder `tahapan/` pada referensi **tidak perlu dibuat atau dipakai**: menurut dosen, itu hanya contoh langkah pengerjaan.
- Hasil akhir akan diunggah ke **GitHub** (akar repositori = folder `PM-bot/`), jadi repositori harus rapi, bisa dijalankan dari nol, dan terdokumentasi. Folder referensi dosen tidak ikut diunggah (lihat Bagian 4).

## 2. Berkas yang Sudah Disediakan

Folder kerja bernama **`PM-bot/`**. Di dalamnya sudah ada:

| Lokasi | Keterangan |
|---|---|
| `PM-bot/chatbot-tematik-flask/referensiProyek.md` | Dokumentasi aplikasi referensi dosen. **Baca pertama.** |
| `PM-bot/chatbot-tematik-flask/aplikasi-final/` | Kode aplikasi referensi (acuan konvensi). |
| `PM-bot/chatbot-tematik-flask/template-tema.json` | Kerangka kosong tema dari dosen (acuan untuk `template-tema.json` milikmu). |
| `PM-bot/themes/pm_bot.json` | Knowledge base PM-Bot: 22 intent, 174 pola, respons, fallback. **Jangan ubah isinya** kecuali validator menemukan kesalahan nyata. |
| `PM-bot/evaluasi/pm_bot.csv` | 50 kalimat uji (kolom `kalimat,intent`), termasuk 6 baris `fallback`. **Jangan diubah agar akurasi terlihat bagus.** |

Jika `themes/pm_bot.json` atau `evaluasi/pm_bot.csv` belum ada di lokasi di atas, **berhenti dan minta pengguna menempatkannya**. Jangan menulis ulang isinya sendiri.

Berkas yang harus **kamu buat** (di akar `PM-bot/`): semua kode, `template-tema.json`, `requirements.txt`, `pytest.ini`, `.gitignore`, `README.md`.

### Cara memakai folder referensi

- **Baca saja.** Jangan mengubah, memindahkan, menghapus, atau mengimpor apa pun dari `chatbot-tematik-flask/`. Folder `tahapan/` di dalamnya diabaikan.
- Pakai sebagai acuan **kontrak dan konvensi**: nama fungsi/kelas, bentuk respons API, skema database, format tema.
- Jika kode referensi bertentangan dengan dokumen ini (termasuk Bagian 14), **dokumen ini yang menang**.

### Catatan isi `pm_bot.json`

- Nilai `"id"` adalah `"pm_bot"` dan **harus sama persis** dengan nama file (`pm_bot.json`).
- Tiga respons template (`template_project_charter`, `template_wbs`, `template_risk_register`) memuat placeholder link `[ISI_LINK_...]`. Biarkan apa adanya dan daftarkan sebagai TODO di README (pemilik repositori akan mengisi link asli).
- Kunci `greeting` ditulis literal ("PM-Bot"), **tanpa** placeholder, karena hanya `responses` yang diproses `_isi_placeholder`.

## 3. Teknologi

| Komponen | Pilihan |
|---|---|
| Bahasa | Python 3.12+ |
| Web | Flask >= 3.0 |
| Penyimpanan | SQLite via modul `sqlite3` bawaan |
| Pencocokan teks | Jaccard + `difflib.SequenceMatcher` + cakupan (tanpa library ML/NLP) |
| Frontend | HTML (Jinja2), CSS, JavaScript vanilla (`fetch`) |
| Pengujian | pytest >= 8.0 |

Dependensi di `requirements.txt` hanya `Flask>=3.0` dan `pytest>=8.0`. **Dilarang** menambah library lain, memakai CDN, atau framework JS/CSS. Aplikasi harus jalan offline.

## 4. Struktur Repositori

Akar repositori adalah folder kerja `PM-bot/`. Aplikasi PM-Bot dibuat **langsung di akar** ini, berdampingan dengan folder referensi (bukan di dalamnya).

```
PM-bot/
├── chatbot-tematik-flask/      ← REFERENSI dosen: hanya baca, jangan diubah, tidak ikut diunggah
├── README.md
├── instruction.md              ← dokumen ini (boleh dipertahankan)
├── .gitignore
├── requirements.txt
├── pytest.ini
├── template-tema.json          ← kerangka kosong untuk tema baru
├── app.py                      ← Flask: create_app() + semua route
├── cli.py                      ← antarmuka terminal
├── evaluate.py                 ← pengukur akurasi
├── chatbot/
│   ├── __init__.py             ← ekspor: ChatbotEngine, load_themes, ChatHistory
│   ├── engine.py
│   └── database.py
├── themes/
│   └── pm_bot.json             ← (disediakan)
├── evaluasi/
│   └── pm_bot.csv              ← (disediakan)
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── chat.html
│   ├── admin.html
│   └── 404.html
├── static/
│   ├── css/style.css
│   └── js/chat.js
└── tests/
    ├── __init__.py
    ├── test_engine.py
    └── test_app.py
```

`.gitignore` minimal: `chatbot-tematik-flask/` (materi dosen tidak ikut diunggah; pemilik repositori boleh menghapus baris ini jika ingin menyertakannya), `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `*.db`, `.pytest_cache/`, `.env`, `instance/`.

Semua perintah di dokumen ini dijalankan dari akar `PM-bot/`.

## 5. Format File Tema (`themes/*.json`)

Kunci wajib: `id`, `name`, `bot_name`, `avatar`, `color`, `description`, `greeting`, `suggestions`, `fallback`, `intents`.

```json
{
  "id": "pm_bot",
  "name": "...", "bot_name": "PM-Bot", "avatar": "📋", "color": "#0f766e",
  "description": "...", "greeting": "...",
  "suggestions": ["..."],
  "fallback": ["..."],
  "intents": [
    { "tag": "salam", "patterns": ["halo", "hai"], "responses": ["Halo! Saya {nama_bot}."] }
  ]
}
```

Placeholder di `responses`: `{waktu}` (HH:MM), `{tanggal}` (DD-MM-YYYY), `{nama_bot}` (nilai `bot_name`).
Baris baru dalam respons ditulis `\n` dan **harus tampil sebagai baris baru** di UI.

`template-tema.json` berisi kerangka yang sama dengan nilai kosong/contoh (satu intent contoh), untuk disalin saat membuat tema baru.

## 6. `chatbot/engine.py`

### 6.1 Konstanta

| Konstanta | Nilai |
|---|---|
| `BOBOT_JACCARD` / `BOBOT_FUZZY` / `BOBOT_CAKUPAN` | `0.4` / `0.3` / `0.3` |
| `KUNCI_WAJIB_TEMA` | daftar 10 kunci wajib di Bagian 5 |
| `NORMALISASI` | dict kata tidak baku → baku (nilai `""` berarti kata dibuang) |
| `STOPWORDS` | set kata yang dibuang |

Titik awal `NORMALISASI` (boleh ditambah): `gak/ga/nggak→tidak`, `gmn/bgmn/gimana→bagaimana`, `apaan→apa`, `ngapain→apa`, `bikin→buat`, `kerjanya→tugas`, `hi/hai/hello→halo`, `makasih/terimakasih/thanks/thx/thank→terima kasih`, `software→aplikasi`, `kak/bang/dong/sih/deh/nih/ya→""`.

Titik awal `STOPWORDS`: `yang, di, ke, dari, dan, untuk, dalam, saja, mau, tolong, boleh, bisa, itu, seorang, adalah, dengan, sama, bot, aku, saya, kamu`.

**Aturan penting:** `STOPWORDS` dan `NORMALISASI` **tidak boleh** menghapus atau mengubah kata kunci domain: `agile, scrum, waterfall, pm, po, sm, wbs, kpi, stakeholder, charter, risk, register, tools, sprint` maupun kata pembeda `beda, bedanya, perbedaan, vs, atau, tugas, tanggung, jawab`.

### 6.2 Fungsi

| Fungsi | Perilaku |
|---|---|
| `preprocess(teks) -> list[str]` | huruf kecil → ganti `-` dengan spasi → buang tanda baca lain → pecah per kata → terapkan `NORMALISASI` (hasil bisa lebih dari satu kata) → buang `STOPWORDS` dan token kosong |
| `similarity(a, b) -> float` | `0.4*Jaccard + 0.3*Fuzzy + 0.3*Cakupan`, hasil 0..1. Jaccard = `|A∩B|/|A∪B|` (set token). Fuzzy = `SequenceMatcher(None, " ".join(a), " ".join(b)).ratio()`. Cakupan = `|A∩B|/|B|` dengan `B` = token pola. Jika salah satu daftar kosong, hasil `0.0`. Kalimat identik bernilai `1.0`. |
| `validate_theme(theme) -> list[str]` | Mengembalikan daftar pesan masalah (kosong = valid). Aturan di 6.3. |
| `load_themes(folder) -> dict[str, dict]` | Baca semua `*.json` (urut nama), validasi, dan pastikan `id == nama file tanpa .json`. Jika ada masalah, `raise ValueError` yang memuat **semua** pesan masalah beserta nama file. Pakai `encoding="utf-8"`. |

### 6.3 Aturan `validate_theme`

1. Semua kunci wajib ada, dengan tipe benar (`suggestions`/`fallback`/`intents` berupa list).
2. `fallback` tidak boleh kosong.
3. Setiap intent punya `tag` (string), `patterns` dan `responses` yang tidak kosong.
4. `tag` unik dalam satu tema, berformat `snake_case` huruf kecil (`^[a-z][a-z0-9_]*$`), dan tidak boleh bernama `fallback`.
5. Pola yang sama (dibandingkan **setelah** `preprocess`) tidak boleh muncul di dua intent berbeda. Pola duplikat dalam intent yang sama boleh.
6. Pola yang menghasilkan token kosong setelah `preprocess` dianggap kesalahan.

### 6.4 Kelas `ChatbotEngine`

| Method | Perilaku |
|---|---|
| `__init__(theme, threshold=0.45)` | Simpan tema; praproses semua pola **sekali** di awal. |
| `explain(pesan, top=3)` | Skor terbaik per intent, urut menurun, ambil `top`. Tiap item: `{"intent", "pattern", "score"}` (skor dibulatkan 3 desimal). |
| `classify(pesan) -> (tag, skor)` | Intent dengan skor tertinggi; `tag=None` jika skor `< threshold`. Seri dimenangkan intent yang lebih dulu di file. |
| `_isi_placeholder(teks)` | Ganti `{waktu}`, `{tanggal}`, `{nama_bot}`. |
| `reply(pesan) -> dict` | `{"reply", "intent", "score"}`. Jika dikenali: `random.choice` dari `responses`; jika tidak: `random.choice` dari `fallback` dengan `intent=None`. Skor dibulatkan 3 desimal. |

## 7. `chatbot/database.py`

Kelas `ChatHistory(db_path)`. Buat tabel saat inisialisasi, **persis** skema ini:

```sql
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    theme       TEXT    NOT NULL,
    sender      TEXT    NOT NULL CHECK (sender IN ('user', 'bot')),
    text        TEXT    NOT NULL,
    intent      TEXT,
    score       REAL,
    created_at  TIMESTAMP DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_session_theme ON messages (session_id, theme);
```

Setiap pertukaran pesan menyimpan **dua baris**: baris `user` (teks pengguna + `intent` dan `score` hasil klasifikasi, `intent` NULL jika tidak dikenali) dan baris `bot` (teks balasan + intent/skor yang sama).

| Method | Perilaku |
|---|---|
| `add(session_id, theme, sender, text, intent, score)` | Simpan satu baris. |
| `get(session_id, theme, limit=50)` | `limit` baris terbaru, dikembalikan urut lama → baru, sebagai list dict `{sender, text, intent, score, created_at}`. |
| `clear(session_id, theme)` | Hapus riwayat sesi untuk tema itu. |
| `stats(theme)` | `[{"intent", "jumlah"}]` dari baris `user` dengan intent tidak NULL, urut jumlah menurun. |
| `unknown_questions(theme, limit=20)` | Teks baris `user` ber-intent NULL, terbaru dulu. |
| `summary(theme)` | `{total, tidak_dikenali, sesi, persen_dikenali}` dihitung dari baris `user`. Hindari pembagian nol. |

**Wajib** memakai query berparameter (`?`), tidak boleh menyusun SQL dengan f-string/format. Tutup koneksi dengan benar (context manager). Buat folder induk database jika belum ada.

## 8. `app.py`

Pola *application factory*: `create_app(config: dict | None = None)`.

### 8.1 Konfigurasi

| Kunci | Default | Sumber |
|---|---|---|
| `SECRET_KEY` | placeholder `"ganti-dengan-kunci-rahasia"` | env `SECRET_KEY` |
| `DATABASE` | `chat_history.db` di folder aplikasi | env `DATABASE` |
| `THEMES_DIR` | `themes/` | env `THEMES_DIR` |
| `THRESHOLD` | `0.45` | env `THRESHOLD` |
| `ADMIN_KEY` | `""` (kosong = admin terbuka) | env `ADMIN_KEY` |
| `MAX_LEN` | `500` | env `MAX_LEN` |

Argumen `config` menimpa nilai env (dipakai pengujian). Saat startup: `load_themes`, buat satu `ChatbotEngine` per tema, buat `ChatHistory`.

### 8.2 Route

| Metode | URL | Perilaku |
|---|---|---|
| GET | `/` | Halaman pilih tema |
| GET | `/chat/<theme_id>` | Halaman chat; 404 jika tema tidak ada |
| GET | `/admin/<theme_id>?key=` | Statistik + pertanyaan tak dikenali; 403 jika kunci salah |
| GET | `/api/themes` | `[{id, name, description}]` |
| POST | `/api/chat` | Body `{message, theme}` → `{reply, intent, score}`; simpan 2 baris riwayat |
| POST | `/api/explain` | Body `{message, theme}` → `{threshold, candidates:[{intent, pattern, score}]}` |
| GET | `/api/history/<theme_id>` | Riwayat sesi ini |
| DELETE | `/api/history/<theme_id>` | `{"status": "ok"}` |
| GET | `/api/stats/<theme_id>?key=` | `[{intent, jumlah}]`, dilindungi `ADMIN_KEY` seperti halaman admin |

Helper: `get_session_id()` (uuid4 disimpan di `session` Flask), `get_theme_or_404()`, `check_admin()`.

### 8.3 Validasi dan error

- `/api/chat` dan `/api/explain`: body harus JSON (`request.get_json(silent=True)`), `message` string, di-`strip()`, tidak kosong, panjang `<= MAX_LEN`, `theme` harus ada. Pelanggaran → **400** JSON `{"error": "..."}`.
- Tema tidak ada pada route halaman/history/stats → **404**. Kunci admin salah → **403**.
- Satu error handler untuk 400/403/404: jika path diawali `/api/` kembalikan JSON, selain itu render `404.html`.
- `app.run(...)` hanya di `if __name__ == "__main__"`, dengan `debug` dari env `FLASK_DEBUG` (**default mati**).

### 8.4 Keamanan (wajib)

- Bandingkan `ADMIN_KEY` dengan `hmac.compare_digest`.
- Cookie sesi: `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE="Lax"`.
- Endpoint POST hanya menerima JSON (membantu mencegah CSRF form lintas situs).
- Jinja2 autoescape tetap aktif; **tidak boleh** memakai `|safe` pada input pengguna.
- Beri header `X-Content-Type-Options: nosniff` pada semua respons.
- Jangan mencatat atau menampilkan `SECRET_KEY`/`ADMIN_KEY`. Jangan commit berkas `.db` atau `.env`.

## 9. `cli.py`

```bash
python cli.py                    # tema pm_bot
python cli.py --tema pm_bot
python cli.py --debug            # tampilkan 3 kandidat intent teratas
python cli.py --ambang 0.3
```

Argumen: `--tema` (default: tema pertama yang ditemukan, yaitu `pm_bot`), `--ambang` (default `0.45`), `--debug`. Tampilkan sambutan tema, loop input, keluar dengan `exit`/`keluar`/`quit`/Ctrl+C tanpa traceback. Pesan error ramah jika tema tidak ditemukan.

## 10. `evaluate.py`

```bash
python evaluate.py --tema pm_bot
python evaluate.py --tema pm_bot --sweep
```

- Baca `evaluasi/<tema>.csv` (`kalimat,intent`, UTF-8). Baris `fallback` dianggap benar jika `classify` mengembalikan `None`.
- Laporan: akurasi total, akurasi per intent, dan daftar kalimat yang salah (kalimat, harapan, hasil, skor).
- `--sweep`: coba ambang 0.30 sampai 0.70 (langkah 0.05), tampilkan tabel dan **grafik batang ASCII** akurasi per ambang, tandai ambang terbaik.

## 11. Antarmuka Web

### 11.1 Template
- `base.html`: layout induk dengan blok `title`, `color` (CSS variable `--primary`), `header_extra`, `content`, `scripts`.
- `index.html` (mewarisi base): grid kartu tema (avatar, nama, deskripsi) → klik masuk ke `/chat/<id>`.
- `chat.html`: area pesan, chip `suggestions`, form input (dengan `maxlength` sesuai `MAX_LEN`), tombol hapus riwayat, tombol/toggle **mode belajar**, tautan ke statistik.
- `admin.html`: ringkasan `summary`, tabel statistik per intent, daftar pertanyaan tak dikenali.
- `404.html`: halaman error ramah untuk 403/404.
- Data tema diteruskan ke JS lewat objek `const THEME = {id, avatar, greeting}` di blok `scripts` (pakai `|tojson`).

### 11.2 `static/js/chat.js`
Fungsi: `addMessage(sender, text, meta)`, `showCandidates(bubble, text)`, `sendMessage(text)`, `loadHistory()`. Event: `submit` pada `#chat-form` (cegah reload), `click` pada `.chip` (langsung kirim), `click` pada `#btn-clear` (DELETE riwayat).

Aturan:
- Teks pesan **selalu** dimasukkan dengan `textContent` (anti-XSS), tidak pernah `innerHTML`.
- Respons bot mempertahankan baris baru (`white-space: pre-wrap`).
- URL `http(s)://` di respons bot diubah menjadi tautan dengan membuat elemen `<a>` lewat DOM API (`target="_blank"`, `rel="noopener noreferrer"`), **hanya** skema http/https.
- Tampilkan indikator "mengetik..." saat menunggu, tangani error jaringan/400 dengan pesan ramah, nonaktifkan tombol kirim saat request berjalan.
- Mode belajar: bila aktif, tiap pesan menampilkan 3 kandidat intent dari `/api/explain` (intent, pola, skor, dan apakah melewati ambang).
- `loadHistory()` saat halaman dibuka; jika riwayat kosong tampilkan `THEME.greeting`.

### 11.3 `static/css/style.css`
Responsif (nyaman di ponsel), gelembung pesan berbeda untuk user/bot, warna utama dari `--primary`, dukung `prefers-color-scheme: dark`, fokus keyboard terlihat. Aksesibilitas dasar: `<label>` untuk input, `aria-live="polite"` pada area pesan, kontras warna cukup.

## 12. Pengujian (`tests/`, jalankan `pytest -v`)

`pytest.ini` mengatur `testpaths = tests`. Semua uji memakai database sementara (`tmp_path`), **tidak** menyentuh `chat_history.db`. Target: **minimal 30 uji**, semuanya lulus.

**`test_engine.py` (unit, tanpa Flask)** minimal mencakup:
- praproses: huruf besar, tanda baca, tanda hubung, normalisasi, stopword
- `similarity`: identik = 1.0, tidak berkaitan = rendah, token kosong = 0.0
- semua tema di folder `themes/` termuat dan valid (`validate_theme` kosong)
- klasifikasi (parametrize), minimal 12 kasus, antara lain: `"halo"→salam`, `"apa itu agile?"→apa_itu_agile`, `"agile vs waterfall"→waterfall_vs_agile`, `"tugas scrum master"→tugas_scrum_master`, `"beda PM dan product owner"→pm_vs_product_owner`, `"contoh WBS"→template_wbs`, `"apa itu scope creep"→scope_creep`, `"apa itu KPI"→kpi`, `"rekomendasi tools proyek"→rekomendasi_tools`, `"berapa gaji PM"→di_luar_cakupan`
- salah ketik masih dikenali (mis. `"apa itu agle"→apa_itu_agile`, `"tahapan proyk"→fase_proyek`)
- pertanyaan off-topic (`"resep nasi goreng"`) → intent `None` dan respons termasuk `fallback`
- `{nama_bot}` diganti menjadi `"PM-Bot"` pada respons `salam`
- `explain` terurut menurun dan berisi `top` item
- `validate_theme` mendeteksi: responses kosong, tag duplikat, tag tidak `snake_case`, pola duplikat antar intent, kunci wajib hilang
- `load_themes` menolak tema yang `id`-nya tidak sama dengan nama file
- setiap isi `suggestions` pada `pm_bot` menghasilkan intent bukan `None`
- akurasi pada `evaluasi/pm_bot.csv` **>= 90%**

**`test_app.py` (integrasi, Flask test client)** minimal mencakup: halaman utama menampilkan nama tema; `/chat/pm_bot` 200; tema tidak ada 404; `/api/themes` mengembalikan tema; `/api/chat` valid; `/api/chat` tidak valid (kosong, bukan JSON, tema salah, terlalu panjang → 400); riwayat tersimpan dan bisa dihapus; statistik intent; `/api/explain` memuat `threshold` dan kandidat; halaman admin menampilkan pertanyaan tak dikenali; `ADMIN_KEY` melindungi admin dan `/api/stats` (tanpa kunci 403, dengan kunci 200); input berisi `<script>` ditampilkan ter-escape di halaman admin.

Jika akurasi < 90%, perbaiki `NORMALISASI`/`STOPWORDS` atau tambah pola di `pm_bot.json`. **Jangan** mengubah isi CSV uji dan jangan menurunkan ambang di bawah 0.35.

## 13. README.md (Bahasa Indonesia)

Wajib memuat: judul dan deskripsi singkat; fitur; prasyarat; instalasi (`python -m venv .venv`, aktivasi, `pip install -r requirements.txt`); cara menjalankan web (`python app.py`, lalu buka `http://127.0.0.1:5000`) dan variabel lingkungan; cara memakai CLI; cara evaluasi (`evaluate.py`, `--sweep`); cara menjalankan tes; tabel endpoint API; struktur folder; alur kerja singkat (praproses → skor → ambang); cara **menambah intent** dan **menambah tema** (salin `template-tema.json`, `id` = nama file, buat CSV uji, jalankan evaluasi); catatan keamanan singkat; daftar **TODO** (ganti 3 placeholder `[ISI_LINK_...]` dengan link template asli, isi lisensi); dan kredit: struktur serta algoritma mengacu pada materi praktikum/dosen (sebutkan bahwa folder referensi tidak disertakan di repositori).

## 14. Standar Kode Bersih (Anti Spaghetti Code)

Aturan di bawah ini **wajib** dan akan diperiksa pada tinjauan akhir (Bagian 15, langkah 7).

**Struktur dan tanggung jawab**
- Satu modul, kelas, atau fungsi memegang **satu tanggung jawab**. `engine.py` hanya soal pencocokan teks dan validasi tema; `database.py` hanya SQLite; `app.py` hanya routing dan validasi HTTP.
- Arah dependensi **satu arah**: `app.py`, `cli.py`, `evaluate.py` → `chatbot/`. Paket `chatbot/` **tidak** mengimpor Flask atau modul di luar paketnya. Tidak boleh ada impor melingkar.
- **Route tipis**: tiap route idealnya <= 15 baris. Validasi input dipindah ke fungsi helper, logika inti ke `chatbot/`.
- Template Jinja2 hanya berisi tampilan (loop dan kondisi sederhana), tanpa logika bisnis.
- JavaScript: fungsi kecil dengan satu tugas, elemen DOM diambil sekali di awal, tidak ada variabel global selain `THEME` dan konstanta.

**Ukuran dan kompleksitas**
- Fungsi <= 30 baris (maksimal 40), parameter <= 4, tingkat *nesting* <= 3. Gunakan *guard clause* / `return` dini untuk menghindari `if` bersarang dalam.
- File Python <= sekitar 300 baris; jika lebih, pecah menjadi modul yang bermakna.
- Tidak ada blok kode hasil salin-tempel: ekstrak ke fungsi (DRY). Tetapi jangan membuat abstraksi berlebihan yang membuat alur sulit diikuti.

**Kejelasan**
- Nama deskriptif untuk variabel, fungsi, dan kelas; tidak ada singkatan membingungkan.
- Tidak ada angka atau string ajaib: pakai konstanta bernama (mis. ambang 0.45, panjang maksimal 500, bobot skor).
- Tidak ada *state* global yang bisa berubah. `ChatbotEngine` dan `ChatHistory` dibuat sekali di `create_app()` dan disimpan pada aplikasi (mis. `app.extensions`), bukan sebagai variabel modul.
- Penanganan error **eksplisit dan spesifik** (mis. `except ValueError`), tidak pernah `except: pass` atau menelan error diam-diam. Format respons error JSON seragam.
- Tidak ada kode mati, kode lama yang di-komentar, atau `print` debug yang tertinggal.
- Konsisten: satu gaya penamaan, satu format pesan error, satu cara membaca file.

**Gaya**
- Komentar, docstring, dan pesan ke pengguna dalam **Bahasa Indonesia**. PEP 8, *type hints* pada fungsi publik.
- Semua baca/tulis file memakai `encoding="utf-8"`.

## 15. Urutan Pengerjaan

1. `chatbot/engine.py` + `tests/test_engine.py` (jalankan sampai hijau)
2. `chatbot/database.py` + `chatbot/__init__.py`
3. `app.py` + `tests/test_app.py`
4. `templates/` + `static/`
5. `cli.py` + `evaluate.py`
6. `README.md`, `requirements.txt`, `pytest.ini`, `.gitignore`, `template-tema.json`
7. **Tinjauan akhir:** telusuri setiap file dengan checklist Bagian 14, refactor semua pelanggaran, lalu jalankan ulang `pytest -v` dan `python evaluate.py --tema pm_bot`.

## 16. Kriteria Selesai (Definition of Done)

- [ ] `pip install -r requirements.txt` berhasil pada lingkungan bersih
- [ ] `pytest -v` lulus semua (minimal 30 uji)
- [ ] `python evaluate.py --tema pm_bot` menunjukkan akurasi **>= 90%**; `--sweep` berjalan dan menampilkan grafik
- [ ] `python cli.py --tema pm_bot --debug` berjalan dan keluar dengan bersih
- [ ] `python app.py` menampilkan halaman, chat berfungsi tanpa reload, chip saran, mode belajar, hapus riwayat, dan halaman admin
- [ ] Baris baru dan tautan pada respons tampil benar; tidak ada `innerHTML` untuk teks pengguna
- [ ] Tidak ada berkas `.db`, `.env`, atau rahasia di repositori
- [ ] README lengkap sesuai Bagian 13
- [ ] Checklist Bagian 14 terpenuhi: tidak ada fungsi > 40 baris, nesting > 3, impor melingkar, atau *state* global yang bisa berubah
- [ ] Folder `chatbot-tematik-flask/` tidak berubah sama sekali dan tercantum di `.gitignore`

## 17. Di Luar Cakupan

Login/registrasi pengguna, deployment/hosting, library ML atau LLM, integrasi Telegram/WhatsApp, folder `tahapan/`, pengubahan apa pun di dalam `chatbot-tematik-flask/`, dan pengubahan isi `pm_bot.json`/`pm_bot.csv` kecuali untuk memperbaiki kesalahan validasi.

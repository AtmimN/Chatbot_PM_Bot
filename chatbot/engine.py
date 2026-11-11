"""Mesin chatbot berbasis aturan (rule-based) untuk PM-Bot.

Alur pemrosesan:
1. Praproses teks: normalisasi kata, pembersihan tanda baca, penghapusan kata henti.
2. Perhitungan kemiripan: gabungan Jaccard, SequenceMatcher (fuzzy), dan cakupan.
3. Klasifikasi intent: memilih intent dengan skor tertinggi yang memenuhi ambang batas.
"""
from __future__ import annotations

import json
import random
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# Bobot tiga metrik kemiripan kata (total bobot = 1.0)
BOBOT_JACCARD: float = 0.4
BOBOT_FUZZY: float = 0.3
BOBOT_CAKUPAN: float = 0.3

# Daftar 10 kunci wajib struktur tema
KUNCI_WAJIB_TEMA: list[str] = [
    "id",
    "name",
    "bot_name",
    "avatar",
    "color",
    "description",
    "greeting",
    "suggestions",
    "fallback",
    "intents",
]

# Kamus pemetaan kata tidak baku menjadi kata baku (atau dihapus jika "")
NORMALISASI: dict[str, str] = {
    "gak": "tidak",
    "ga": "tidak",
    "nggak": "tidak",
    "enggak": "tidak",
    "tdk": "tidak",
    "gmn": "bagaimana",
    "bgmn": "bagaimana",
    "gimana": "bagaimana",
    "apaan": "apa",
    "ngapain": "apa",
    "bikin": "buat",
    "kerjanya": "tugas",
    "hi": "halo",
    "hai": "halo",
    "hello": "halo",
    "hallo": "halo",
    "makasih": "terima kasih",
    "terimakasih": "terima kasih",
    "thanks": "terima kasih",
    "thx": "terima kasih",
    "thank": "terima kasih",
    "software": "aplikasi",
    "kak": "",
    "bang": "",
    "dong": "",
    "sih": "",
    "deh": "",
    "nih": "",
    "ya": "",
    "yah": "",
    "dmn": "dimana",
    "brp": "berapa",
    "berapakah": "berapa",
    "yg": "yang",
    "dgn": "dengan",
    "utk": "untuk",
    "sy": "saya",
    "aku": "saya",
    "gue": "saya",
    "gw": "saya",
}

# Kata henti umum bahasa Indonesia yang aman dibuang tanpa merusak konteks topik
STOPWORDS: set[str] = {
    "yang",
    "di",
    "ke",
    "dari",
    "dan",
    "untuk",
    "dalam",
    "saja",
    "mau",
    "tolong",
    "boleh",
    "itu",
    "seorang",
    "adalah",
    "dengan",
    "sama",
    "bot",
    "aku",
    "saya",
    "kamu",
}


def preprocess(teks: str) -> list[str]:
    """Mengubah teks mentah menjadi daftar token kata yang dinormalisasi."""
    teks = teks.lower()
    # Tanda hubung diubah menjadi spasi agar kata ulang terpisah rapi (mis. fase-fase -> fase fase)
    teks = teks.replace("-", " ")
    teks = re.sub(r"[^a-z0-9\s]", " ", teks)

    tokens: list[str] = []
    for kata in teks.split():
        kata_normal = NORMALISASI.get(kata, kata)
        # Hasil normalisasi dapat menghasilkan lebih dari satu kata (mis. makasih -> terima kasih)
        for k in kata_normal.split():
            if k and k not in STOPWORDS:
                tokens.append(k)
    return tokens


def similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Menghitung skor kemiripan 0..1 antara token pesan dan token pola."""
    if not tokens_a or not tokens_b:
        return 0.0

    set_a = set(tokens_a)
    set_b = set(tokens_b)

    # 1. Jaccard: mengukur persentase irisan kata terhadap gabungan kata
    jaccard = len(set_a & set_b) / len(set_a | set_b)

    # 2. Fuzzy: ketahanan terhadap kesalahan ketik menggunakan SequenceMatcher
    fuzzy = SequenceMatcher(None, " ".join(tokens_a), " ".join(tokens_b)).ratio()

    # 3. Cakupan: seberapa lengkap kata-kata pada pola target muncul di input pengguna
    cakupan = len(set_a & set_b) / len(set_b)

    skor = (BOBOT_JACCARD * jaccard) + (BOBOT_FUZZY * fuzzy) + (BOBOT_CAKUPAN * cakupan)
    return round(skor, 4)


def _validate_theme_keys(theme: dict) -> list[str]:
    """Memeriksa keberadaan dan tipe data kunci utama file tema."""
    masalah: list[str] = []
    for kunci in KUNCI_WAJIB_TEMA:
        if kunci not in theme:
            masalah.append(f"kunci wajib '{kunci}' tidak ada")
    if masalah:
        return masalah

    for k in ("suggestions", "fallback", "intents"):
        if not isinstance(theme.get(k), list):
            masalah.append(f"kunci '{k}' harus berupa list")

    if not theme.get("fallback"):
        masalah.append("daftar 'fallback' kosong")
    return masalah


def _validate_intent_item(
    intent: dict, idx: int, tags: set[str], pola_milik: dict[str, str]
) -> list[str]:
    """Memeriksa tag, format nama, respons, dan keunikan pola satu intent."""
    masalah: list[str] = []
    tag = intent.get("tag")
    if not tag or not isinstance(tag, str):
        return [f"intent ke-{idx + 1}: kunci 'tag' tidak valid atau kosong"]

    if not re.match(r"^[a-z][a-z0-9_]*$", tag):
        masalah.append(f"intent '{tag}': tag harus snake_case huruf kecil")
    if tag == "fallback":
        masalah.append("tag tidak boleh bernama 'fallback'")
    if tag in tags:
        masalah.append(f"tag '{tag}' dipakai lebih dari sekali")
    tags.add(tag)

    if not isinstance(intent.get("patterns"), list) or not intent.get("patterns"):
        masalah.append(f"intent '{tag}': 'patterns' kosong atau bukan list")
    if not isinstance(intent.get("responses"), list) or not intent.get("responses"):
        masalah.append(f"intent '{tag}': 'responses' kosong atau bukan list")

    for pola in intent.get("patterns") or []:
        tokens = preprocess(pola)
        kunci_pola = " ".join(tokens)
        if not kunci_pola:
            masalah.append(f"intent '{tag}': pola '{pola}' menghasilkan token kosong setelah praproses")
        elif kunci_pola in pola_milik and pola_milik[kunci_pola] != tag:
            masalah.append(f"pola '{pola}' ada di intent '{pola_milik[kunci_pola]}' dan '{tag}'")
        pola_milik[kunci_pola] = tag

    return masalah


def validate_theme(theme: dict) -> list[str]:
    """Memvalidasi integritas struktur file tema JSON."""
    masalah = _validate_theme_keys(theme)
    if masalah:
        return masalah

    tags_terdaftar: set[str] = set()
    pola_terdaftar: dict[str, str] = {}

    for i, intent in enumerate(theme.get("intents", [])):
        masalah.extend(_validate_intent_item(intent, i, tags_terdaftar, pola_terdaftar))

    return masalah


def load_themes(folder: str | Path) -> dict[str, dict]:
    """Membaca dan memvalidasi semua file tema JSON di folder yang diberikan."""
    folder_path = Path(folder)
    themes: dict[str, dict] = {}

    for path in sorted(folder_path.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        masalah = validate_theme(data)
        if data.get("id") != path.stem:
            masalah.append(f"nilai 'id' ({data.get('id')}) harus sama dengan nama berkas ({path.stem})")

        if masalah:
            pesan_error = f"File tema {path.name} tidak valid:\n- " + "\n- ".join(masalah)
            raise ValueError(pesan_error)

        themes[data["id"]] = data

    return themes


class ChatbotEngine:
    """Mesin inferensi aturan untuk satu tema percakapan."""

    def __init__(self, theme: dict, threshold: float = 0.45) -> None:
        self.theme = theme
        self.threshold = threshold

        # Pola dipraproses sekali saja saat inisialisasi engine untuk menghemat waktu komputasi
        self._patterns: list[tuple[str, str, list[str]]] = [
            (intent["tag"], pola, preprocess(pola))
            for intent in theme.get("intents", [])
            for pola in intent.get("patterns", [])
        ]
        self._responses: dict[str, list[str]] = {
            intent["tag"]: intent.get("responses", [])
            for intent in theme.get("intents", [])
        }

    def explain(self, pesan: str, top: int = 3) -> list[dict]:
        """Mengembalikan daftar kandidat intent terbaik beserta polanya untuk mode belajar/debug."""
        tokens = preprocess(pesan)
        if not tokens:
            return []

        terbaik: dict[str, dict] = {}
        for tag, pola, pola_tokens in self._patterns:
            skor = similarity(tokens, pola_tokens)
            if tag not in terbaik or skor > terbaik[tag]["score"]:
                terbaik[tag] = {
                    "intent": tag,
                    "pattern": pola,
                    "score": round(skor, 3),
                }

        kandidat = sorted(terbaik.values(), key=lambda x: x["score"], reverse=True)
        return kandidat[:top]

    def classify(self, pesan: str) -> tuple[str | None, float]:
        """Mengidentifikasi intent dari pesan pengguna."""
        kandidat = self.explain(pesan, top=1)
        if not kandidat:
            return None, 0.0

        terpilih = kandidat[0]
        if terpilih["score"] < self.threshold:
            return None, terpilih["score"]

        return terpilih["intent"], terpilih["score"]

    def _isi_placeholder(self, teks: str) -> str:
        """Mengganti variabel dinamis waktu, tanggal, dan nama bot pada teks jawaban."""
        sekarang = datetime.now()
        teks = teks.replace("{waktu}", sekarang.strftime("%H:%M"))
        teks = teks.replace("{tanggal}", sekarang.strftime("%d-%m-%Y"))
        teks = teks.replace("{nama_bot}", self.theme.get("bot_name", ""))
        return teks

    def reply(self, pesan: str) -> dict:
        """Menghasilkan respons balasan bot lengkap."""
        if not pesan or not pesan.strip():
            return {
                "reply": "Pesannya masih kosong. Silakan ketik pertanyaan Anda.",
                "intent": None,
                "score": 0.0,
            }

        tag, skor = self.classify(pesan)
        if tag is None:
            jawaban_mentah = random.choice(self.theme["fallback"])
        else:
            jawaban_mentah = random.choice(self._responses[tag])

        return {
            "reply": self._isi_placeholder(jawaban_mentah),
            "intent": tag,
            "score": skor,
        }

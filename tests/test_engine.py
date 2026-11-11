"""Uji unit untuk mesin pencocokan intent chatbot (tanpa Flask)."""
import csv
from pathlib import Path

import pytest

from chatbot.engine import (
    ChatbotEngine,
    load_themes,
    preprocess,
    similarity,
    validate_theme,
)

BASE_DIR = Path(__file__).resolve().parent.parent
THEMES_DIR = BASE_DIR / "themes"
EVAL_DIR = BASE_DIR / "evaluasi"


def test_preprocess_lengkap():
    """Menguji huruf besar, tanda baca, tanda hubung, normalisasi, dan kata henti."""
    teks = "Halo Kak! Fase-fase proyek apaan sih? Makasih ya."
    tokens = preprocess(teks)
    # fase-fase terpecah rapi, apaan dinormalisasi menjadi apa, makasih menjadi terima kasih
    assert "fase" in tokens
    assert "apa" in tokens
    assert "terima" in tokens
    assert "kasih" in tokens
    # kak, sih, ya dibuang oleh normalisasi/stopword
    assert "kak" not in tokens
    assert "sih" not in tokens
    assert "ya" not in tokens


def test_similarity_identik_bernilai_satu():
    """Dua daftar token identik harus menghasilkan nilai 1.0."""
    tokens = ["manajemen", "proyek", "agile"]
    assert similarity(tokens, tokens) == 1.0


def test_similarity_tidak_berkaitan_rendah():
    """Kata yang sama sekali berbeda harus menghasilkan skor rendah di bawah 0.3."""
    t1 = ["resep", "nasi", "goreng"]
    t2 = ["tahapan", "proyek", "scrum"]
    assert similarity(t1, t2) < 0.3


def test_similarity_token_kosong():
    """Jika salah satu atau kedua daftar token kosong, skor harus 0.0."""
    assert similarity([], ["agile"]) == 0.0
    assert similarity(["scrum"], []) == 0.0
    assert similarity([], []) == 0.0


def test_semua_tema_termuat_dan_valid():
    """Seluruh tema di folder themes harus berhasil dimuat dan lolos validasi."""
    themes = load_themes(THEMES_DIR)
    assert "pm_bot" in themes
    for theme in themes.values():
        assert validate_theme(theme) == []


@pytest.mark.parametrize(
    "pesan, intent_diharapkan",
    [
        ("halo", "salam"),
        ("apa itu agile?", "apa_itu_agile"),
        ("agile vs waterfall", "waterfall_vs_agile"),
        ("tugas scrum master", "tugas_scrum_master"),
        ("beda PM dan product owner", "pm_vs_product_owner"),
        ("contoh WBS", "template_wbs"),
        ("apa itu scope creep", "scope_creep"),
        ("apa itu KPI", "kpi"),
        ("rekomendasi tools proyek", "rekomendasi_tools"),
        ("berapa gaji PM", "di_luar_cakupan"),
        ("fase fase proyek apa saja", "fase_proyek"),
        ("apa itu waterfall", "apa_itu_waterfall"),
        ("apa itu scrum", "apa_itu_scrum"),
        ("tugas project manager", "tugas_project_manager"),
    ],
)
def test_klasifikasi_intent(pesan: str, intent_diharapkan: str):
    """Menguji klasifikasi berbagai kalimat pertanyaan utama PM-Bot."""
    themes = load_themes(THEMES_DIR)
    engine = ChatbotEngine(themes["pm_bot"])
    tag, skor = engine.classify(pesan)
    assert tag == intent_diharapkan
    assert skor >= 0.45


def test_salah_ketik_masih_dikenali():
    """Fuzzy matching harus dapat mentolerir kesalahan ketik ringan."""
    themes = load_themes(THEMES_DIR)
    engine = ChatbotEngine(themes["pm_bot"])

    tag1, _ = engine.classify("apa itu agle")
    assert tag1 == "apa_itu_agile"

    tag2, _ = engine.classify("tahapan proyk")
    assert tag2 == "fase_proyek"


def test_pertanyaan_di_luar_tema_memberi_fallback():
    """Pertanyaan di luar topik harus menghasilkan intent None dan balasan fallback."""
    themes = load_themes(THEMES_DIR)
    engine = ChatbotEngine(themes["pm_bot"])

    hasil = engine.reply("resep nasi goreng enak")
    assert hasil["intent"] is None
    assert hasil["reply"] in themes["pm_bot"]["fallback"]


def test_placeholder_nama_bot_diganti():
    """Placeholder {nama_bot} pada respons harus tergantikan dengan nama asli."""
    themes = load_themes(THEMES_DIR)
    engine = ChatbotEngine(themes["pm_bot"])

    hasil = engine.reply("halo")
    assert "{nama_bot}" not in hasil["reply"]
    assert "PM-Bot" in hasil["reply"]


def test_explain_mengurutkan_kandidat():
    """Method explain harus mengembalikan kandidat terurut menurun berdasarkan skor."""
    themes = load_themes(THEMES_DIR)
    engine = ChatbotEngine(themes["pm_bot"])

    kandidat = engine.explain("beda pm dan po", top=3)
    assert len(kandidat) <= 3
    assert kandidat[0]["intent"] == "pm_vs_product_owner"

    skor_list = [k["score"] for k in kandidat]
    assert skor_list == sorted(skor_list, reverse=True)


def test_validate_theme_mendeteksi_kesalahan():
    """Validasi harus menangkap kesalahan struktur, tag, dan pola duplikat."""
    # 1. Kunci wajib hilang
    tema_rusak = {"id": "uji", "name": "Uji"}
    assert any("kunci wajib" in err for err in validate_theme(tema_rusak))

    # 2. Tag tidak snake_case dan responses kosong
    tema_rusak2 = {
        "id": "uji2",
        "name": "Uji 2",
        "bot_name": "Bot",
        "avatar": "🤖",
        "color": "#000",
        "description": "Deskripsi",
        "greeting": "Halo",
        "suggestions": ["Saran"],
        "fallback": ["Fallback"],
        "intents": [
            {
                "tag": "TagBesar",
                "patterns": ["pola satu"],
                "responses": [],
            },
            {
                "tag": "fallback",
                "patterns": ["pola dua"],
                "responses": ["Respons"],
            },
        ],
    }
    masalah2 = validate_theme(tema_rusak2)
    assert any("snake_case" in err for err in masalah2)
    assert any("responses" in err for err in masalah2)
    assert any("tag tidak boleh bernama 'fallback'" in err for err in masalah2)

    # 3. Pola bentrok antar intent berbeda
    tema_bentrok = {
        "id": "uji3",
        "name": "Uji 3",
        "bot_name": "Bot",
        "avatar": "🤖",
        "color": "#000",
        "description": "Deskripsi",
        "greeting": "Halo",
        "suggestions": ["Saran"],
        "fallback": ["Fallback"],
        "intents": [
            {"tag": "satu", "patterns": ["halo"], "responses": ["Hai"]},
            {"tag": "dua", "patterns": ["halo"], "responses": ["Halo juga"]},
        ],
    }
    assert any("ada di intent 'satu' dan 'dua'" in err for err in validate_theme(tema_bentrok))


def test_load_themes_menolak_id_berbeda_dengan_nama_file(tmp_path):
    """load_themes harus menolak jika id di JSON tidak sama dengan nama file."""
    import json

    file_palsu = tmp_path / "tema_beda.json"
    with open(file_palsu, "w", encoding="utf-8") as f:
        json.dump(
            {
                "id": "id_lain",
                "name": "Uji",
                "bot_name": "Bot",
                "avatar": "🤖",
                "color": "#000",
                "description": "Desc",
                "greeting": "Hai",
                "suggestions": ["A"],
                "fallback": ["B"],
                "intents": [
                    {"tag": "salam", "patterns": ["halo"], "responses": ["Hai"]}
                ],
            },
            f,
        )

    with pytest.raises(ValueError) as exc:
        load_themes(tmp_path)
    assert "harus sama dengan nama berkas" in str(exc.value)


def test_semua_suggestions_menghasilkan_intent():
    """Setiap teks yang ada pada suggestions tema pm_bot harus menghasilkan intent valid."""
    themes = load_themes(THEMES_DIR)
    pm_theme = themes["pm_bot"]
    engine = ChatbotEngine(pm_theme)

    for saran in pm_theme["suggestions"]:
        tag, _ = engine.classify(saran)
        assert tag is not None, f"Saran '{saran}' tidak menghasilkan intent"


def test_akurasi_evaluasi_pm_bot_minimal_90_persen():
    """Akurasi pada dataset uji evaluasi/pm_bot.csv harus >= 90%."""
    themes = load_themes(THEMES_DIR)
    engine = ChatbotEngine(themes["pm_bot"], threshold=0.45)

    csv_path = EVAL_DIR / "pm_bot.csv"
    with open(csv_path, encoding="utf-8") as f:
        data = list(csv.DictReader(f))

    benar = 0
    for baris in data:
        kalimat = baris["kalimat"]
        harapan = baris["intent"]

        tag, _ = engine.classify(kalimat)
        tebakan = tag if tag is not None else "fallback"

        if tebakan == harapan:
            benar += 1

    akurasi = benar / len(data)
    assert akurasi >= 0.90, f"Akurasi hanya {akurasi:.1%}, diharapkan >= 90%"


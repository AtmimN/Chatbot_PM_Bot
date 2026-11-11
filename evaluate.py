"""Skrip evaluasi performa dan akurasi intent chatbot dengan data uji CSV."""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from chatbot import ChatbotEngine, load_themes

BASE_DIR: Path = Path(__file__).resolve().parent


def baca_data_uji(tema: str) -> list[tuple[str, str]]:
    """Membaca berkas evaluasi/<tema>.csv dan mengembalikan pasangan (kalimat, intent)."""
    csv_path = BASE_DIR / "evaluasi" / f"{tema}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Berkas data uji tidak ditemukan: {csv_path}")

    data: list[tuple[str, str]] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            data.append((r["kalimat"], r["intent"]))
    return data


def evaluasi_ambang(
    theme: dict[str, Any], data: list[tuple[str, str]], ambang: float
) -> tuple[float, list[tuple[str, str, str, float]]]:
    """Menghitung akurasi klasifikasi pada ambang batas skor tertentu."""
    engine = ChatbotEngine(theme, threshold=ambang)
    hasil: list[tuple[str, str, str, float]] = []

    for kalimat, harapan in data:
        tag, skor = engine.classify(kalimat)
        tebakan = tag if tag is not None else "fallback"
        hasil.append((kalimat, harapan, tebakan, skor))

    benar = sum(1 for _, h, t, _ in hasil if h == t)
    akurasi = benar / len(hasil) if hasil else 0.0
    return akurasi, hasil


def cetak_sweep_ambang(theme: dict[str, Any], data: list[tuple[str, str]]) -> None:
    """Menguji rentang ambang batas 0.30 s.d. 0.70 dan menampilkan grafik ASCII."""
    langkah_ambang = [round(0.30 + i * 0.05, 2) for i in range(9)]  # 0.30 .. 0.70
    hasil_sweep: list[tuple[float, float]] = []

    for a in langkah_ambang:
        akurasi, _ = evaluasi_ambang(theme, data, a)
        hasil_sweep.append((a, akurasi))

    skor_terbaik = max(h[1] for h in hasil_sweep)

    print(f"\n=== Hasil Sweep Ambang Batas untuk Tema '{theme['id']}' ({len(data)} kalimat uji) ===")
    print(f"{'Ambang':<8} {'Akurasi':<10} {'Grafik Batang':<35} Status")
    print("-" * 65)

    for ambang, akurasi in hasil_sweep:
        panjang_batang = round(akurasi * 30)
        batang = "█" * panjang_batang
        penanda = "★ Terbaik" if akurasi == skor_terbaik else ""
        print(f"{ambang:<8.2f} {akurasi:>6.1%}     {batang:<30} {penanda}")
    print()


def cetak_laporan_detail(
    tema: str, ambang: float, akurasi: float, hasil: list[tuple[str, str, str, float]]
) -> None:
    """Menampilkan ringkasan akurasi per intent dan daftar kesalahan prediksi."""
    print(f"\n=== Laporan Evaluasi Chatbot: {tema} ===")
    print(f"Ambang Batas : {ambang:.2f}")
    print(f"Total Sampel : {len(hasil)} kalimat uji")
    print(f"Akurasi Total: {akurasi:.1%}\n")

    total_per_intent = Counter(h for _, h, _, _ in hasil)
    benar_per_intent = Counter(h for _, h, t, _ in hasil if h == t)

    print(f"{'Intent':<26} {'Benar':>6} {'Total':>7} {'Akurasi':>9}")
    print("-" * 52)
    for intent in sorted(total_per_intent):
        b = benar_per_intent[intent]
        tot = total_per_intent[intent]
        persen = (b / tot) * 100.0
        print(f"{intent:<26} {b:>6} {tot:>7} {persen:>8.1f}%")

    salah = [x for x in hasil if x[1] != x[2]]
    if salah:
        print(f"\nKalimat yang salah diprediksi ({len(salah)} kesalahan):")
        for kalimat, harapan, tebakan, skor in salah:
            print(f"- \"{kalimat}\"")
            print(f"  Tebakan: {tebakan} (skor {skor:.3f}), Seharusnya: {harapan}")
    else:
        print("\nLuar biasa! Seluruh kalimat uji berhasil diprediksi dengan benar (100%).")
    print()


def main() -> None:
    """Titik masuk utama skrip evaluasi."""
    parser = argparse.ArgumentParser(description="Evaluasi Akurasi Model Chatbot PM-Bot")
    parser.add_argument("--tema", default="pm_bot", help="ID tema yang akan diuji")
    parser.add_argument("--ambang", type=float, default=0.45, help="Ambang batas skor intent")
    parser.add_argument("--sweep", action="store_true", help="Uji rentang ambang batas 0.30 s.d. 0.70")
    args = parser.parse_args()

    themes = load_themes(BASE_DIR / "themes")
    if args.tema not in themes:
        print(f"Tema '{args.tema}' tidak ditemukan di folder themes/.")
        return

    theme = themes[args.tema]
    data = baca_data_uji(args.tema)

    if args.sweep:
        cetak_sweep_ambang(theme, data)
        return

    akurasi, hasil = evaluasi_ambang(theme, data, args.ambang)
    cetak_laporan_detail(args.tema, args.ambang, akurasi, hasil)


if __name__ == "__main__":
    main()


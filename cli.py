"""Antarmuka baris perintah (CLI) untuk berinteraksi dengan chatbot PM-Bot di terminal."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from chatbot import ChatbotEngine, load_themes

BASE_DIR: Path = Path(__file__).resolve().parent


def parse_arguments(pilihan_tema: list[str]) -> argparse.Namespace:
    """Mengonfigurasi parser argumen baris perintah."""
    tema_default = "pm_bot" if "pm_bot" in pilihan_tema else pilihan_tema[0]
    parser = argparse.ArgumentParser(description="Antarmuka Terminal Chatbot Tematik PM-Bot")
    parser.add_argument(
        "--tema",
        default=tema_default,
        help=f"ID tema (tersedia: {', '.join(pilihan_tema)})",
    )
    parser.add_argument(
        "--ambang",
        type=float,
        default=0.45,
        help="Ambang batas skor kemiripan intent (default: 0.45)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Tampilkan 3 kandidat intent teratas beserta skor dan polanya",
    )
    return parser.parse_args()


def _tampilkan_balasan(
    engine: ChatbotEngine,
    theme: dict[str, Any],
    pesan: str,
    ambang: float,
    debug: bool,
) -> None:
    """Menampilkan respon bot beserta kandidat intent saat mode debug aktif."""
    hasil = engine.reply(pesan)
    label_intent = hasil["intent"] or "tidak dikenali"
    print(f"{theme['bot_name']}: {hasil['reply']}")
    print(f"   [intent: {label_intent} · skor {hasil['score']:.3f}]")

    if debug:
        kandidat = engine.explain(pesan, top=3)
        for idx, k in enumerate(kandidat, 1):
            status = "lolos" if k["score"] >= ambang else "gagal"
            print(f"   {idx}. {k['intent']:<24} {k['score']:.3f} ({status}) pola: \"{k['pattern']}\"")
    print()


def main() -> None:
    """Menjalankan loop interaktif percakapan di terminal."""
    themes_dir = BASE_DIR / "themes"
    try:
        themes = load_themes(themes_dir)
    except Exception as err:
        print(f"Gagal memuat tema dari {themes_dir}: {err}")
        return

    if not themes:
        print("Tidak ada berkas tema ditemukan di folder themes/.")
        return

    args = parse_arguments(list(themes.keys()))
    if args.tema not in themes:
        print(f"Tema '{args.tema}' tidak ada. Pilihan: {', '.join(themes.keys())}")
        return

    theme = themes[args.tema]
    engine = ChatbotEngine(theme, threshold=args.ambang)

    print(f"{theme['avatar']} {theme['bot_name']}: {theme['greeting']}")
    print("(Ketik 'keluar', 'exit', atau tekan Ctrl+C untuk mengakhiri percakapan)\n")

    while True:
        try:
            pesan = input("Anda: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if not pesan:
            continue
        if pesan.lower() in {"keluar", "exit", "quit"}:
            break

        _tampilkan_balasan(engine, theme, pesan, args.ambang, args.debug)

    print(f"Terima kasih telah berkonsultasi dengan {theme['bot_name']}. Sampai jumpa!")


if __name__ == "__main__":
    main()

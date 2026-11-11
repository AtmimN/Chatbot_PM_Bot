"""Modul penyimpanan riwayat percakapan menggunakan SQLite bawaan Python."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

SKEMA_DATABASE: str = """
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
"""


class ChatHistory:
    """Pengelola penyimpanan dan analitik riwayat percakapan SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        # Pastikan direktori tempat file database berada sudah dibuat
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SKEMA_DATABASE)

    def _connect(self) -> sqlite3.Connection:
        """Membuka koneksi ke database SQLite dengan row_factory dictionary-like."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add(
        self,
        session_id: str,
        theme: str,
        sender: str,
        text: str,
        intent: str | None = None,
        score: float | None = None,
    ) -> None:
        """Menyimpan satu baris pesan ke dalam tabel messages dengan parameter query."""
        sql = (
            "INSERT INTO messages (session_id, theme, sender, text, intent, score) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
        with self._connect() as conn:
            conn.execute(sql, (session_id, theme, sender, text, intent, score))

    def get(self, session_id: str, theme: str, limit: int = 50) -> list[dict[str, Any]]:
        """Mengambil riwayat percakapan untuk sesi tertentu (diurutkan lama ke baru)."""
        sql = (
            "SELECT sender, text, intent, score, created_at FROM messages "
            "WHERE session_id = ? AND theme = ? "
            "ORDER BY id DESC LIMIT ?"
        )
        with self._connect() as conn:
            rows = conn.execute(sql, (session_id, theme, limit)).fetchall()
        # Dibalik agar urutan pesan dari yang paling lama ke yang terbaru
        return [dict(r) for r in reversed(rows)]

    def clear(self, session_id: str, theme: str) -> None:
        """Menghapus seluruh riwayat percakapan pada sesi dan tema tertentu."""
        sql = "DELETE FROM messages WHERE session_id = ? AND theme = ?"
        with self._connect() as conn:
            conn.execute(sql, (session_id, theme))

    def stats(self, theme: str) -> list[dict[str, Any]]:
        """Menghitung agregasi jumlah pertanyaan pengguna per intent."""
        sql = (
            "SELECT intent, COUNT(*) AS jumlah "
            "FROM messages "
            "WHERE theme = ? AND sender = 'user' AND intent IS NOT NULL "
            "GROUP BY intent ORDER BY jumlah DESC"
        )
        with self._connect() as conn:
            rows = conn.execute(sql, (theme,)).fetchall()
        return [dict(r) for r in rows]

    def unknown_questions(self, theme: str, limit: int = 20) -> list[dict[str, Any]]:
        """Mengambil daftar pertanyaan pengguna yang tidak dikenali bot (intent NULL)."""
        sql = (
            "SELECT text, score, created_at FROM messages "
            "WHERE theme = ? AND sender = 'user' AND intent IS NULL "
            "ORDER BY id DESC LIMIT ?"
        )
        with self._connect() as conn:
            rows = conn.execute(sql, (theme, limit)).fetchall()
        return [dict(r) for r in rows]

    def summary(self, theme: str) -> dict[str, Any]:
        """Mengembalikan ringkasan metrik statistik percakapan untuk halaman admin."""
        sql = (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN intent IS NULL THEN 1 ELSE 0 END) AS tidak_dikenali, "
            "COUNT(DISTINCT session_id) AS sesi "
            "FROM messages WHERE theme = ? AND sender = 'user'"
        )
        with self._connect() as conn:
            row = conn.execute(sql, (theme,)).fetchone()

        total = row["total"] or 0
        tidak_dikenali = row["tidak_dikenali"] or 0
        sesi = row["sesi"] or 0
        dikenali = total - tidak_dikenali
        persen = round((100.0 * dikenali) / total, 1) if total > 0 else 0.0

        return {
            "total": total,
            "tidak_dikenali": tidak_dikenali,
            "sesi": sesi,
            "persen_dikenali": persen,
        }


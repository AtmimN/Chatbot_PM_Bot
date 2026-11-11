"""Aplikasi Web Chatbot Tematik PM-Bot dengan Flask."""
from __future__ import annotations

import hmac
import os
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, render_template, request, session

from chatbot import ChatbotEngine, ChatHistory, load_themes

BASE_DIR: Path = Path(__file__).resolve().parent


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Application factory untuk menginisialisasi dan mengonfigurasi aplikasi Flask."""
    app = Flask(__name__)

    # Konfigurasi aplikasi default dan keamanan
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "ganti-dengan-kunci-rahasia"),
        DATABASE=os.environ.get("DATABASE", str(BASE_DIR / "chat_history.db")),
        THEMES_DIR=os.environ.get("THEMES_DIR", str(BASE_DIR / "themes")),
        THRESHOLD=float(os.environ.get("THRESHOLD", "0.45")),
        ADMIN_KEY=os.environ.get("ADMIN_KEY", ""),
        MAX_LEN=int(os.environ.get("MAX_LEN", "500")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if config:
        app.config.update(config)

    # Inisialisasi basis data dan engine tema
    themes = load_themes(app.config["THEMES_DIR"])
    engines = {
        tid: ChatbotEngine(t, app.config["THRESHOLD"]) for tid, t in themes.items()
    }
    history = ChatHistory(app.config["DATABASE"])

    # Simpan instance ke dalam extensions aplikasi untuk menghindari global state
    app.extensions["themes"] = themes
    app.extensions["engines"] = engines
    app.extensions["history"] = history

    def get_session_id() -> str:
        """Mengambil atau membuat ID sesi unik pengunjung yang disimpan di cookie."""
        if "sid" not in session:
            session["sid"] = uuid.uuid4().hex
        return session["sid"]

    def get_theme_or_404(theme_id: str) -> dict[str, Any]:
        """Helper untuk mengambil tema atau melempar 404 jika id tema tidak ada."""
        if theme_id not in themes:
            abort(404, description=f"Tema '{theme_id}' tidak ditemukan")
        return themes[theme_id]

    def check_admin() -> None:
        """Memvalidasi kunci akses halaman admin dengan compare_digest tahan timing-attack."""
        kunci = app.config["ADMIN_KEY"]
        if kunci:
            input_key = request.args.get("key", "")
            if not hmac.compare_digest(input_key, kunci):
                abort(403, description="Kunci admin salah atau tidak ada")

    @app.after_request
    def set_security_headers(response):
        """Menambahkan header keamanan pada setiap respons HTTP."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    # ------------------------------------------------------------------
    # Route Tampilan HTML
    # ------------------------------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html", themes=themes.values())

    @app.route("/chat/<theme_id>")
    def chat_page(theme_id: str):
        theme = get_theme_or_404(theme_id)
        return render_template("chat.html", theme=theme)

    @app.route("/admin/<theme_id>")
    def admin_page(theme_id: str):
        check_admin()
        theme = get_theme_or_404(theme_id)
        return render_template(
            "admin.html",
            theme=theme,
            summary=history.summary(theme_id),
            stats=history.stats(theme_id),
            unknown=history.unknown_questions(theme_id),
            threshold=app.config["THRESHOLD"],
        )

    # ------------------------------------------------------------------
    # Route REST API
    # ------------------------------------------------------------------
    @app.get("/api/themes")
    def api_themes():
        return jsonify([
            {"id": t["id"], "name": t["name"], "description": t["description"]}
            for t in themes.values()
        ])

    @app.post("/api/chat")
    def api_chat():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Format data harus JSON"}), 400

        theme_id = data.get("theme", "")
        message = str(data.get("message", "")).strip()

        if theme_id not in engines:
            return jsonify({"error": "Tema tidak valid"}), 400
        if not message:
            return jsonify({"error": "Pesan tidak boleh kosong"}), 400
        if len(message) > app.config["MAX_LEN"]:
            return jsonify({"error": f"Pesan maksimal {app.config['MAX_LEN']} karakter"}), 400

        sid = get_session_id()
        hasil = engines[theme_id].reply(message)

        history.add(sid, theme_id, "user", message, hasil["intent"], hasil["score"])
        history.add(sid, theme_id, "bot", hasil["reply"], hasil["intent"], hasil["score"])
        return jsonify(hasil)

    @app.post("/api/explain")
    def api_explain():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Format data harus JSON"}), 400

        theme_id = data.get("theme", "")
        message = str(data.get("message", "")).strip()

        if theme_id not in engines:
            return jsonify({"error": "Tema tidak valid"}), 400
        if not message:
            return jsonify({"error": "Pesan tidak boleh kosong"}), 400

        pesan_potong = message[: app.config["MAX_LEN"]]
        return jsonify({
            "threshold": app.config["THRESHOLD"],
            "candidates": engines[theme_id].explain(pesan_potong),
        })

    @app.get("/api/history/<theme_id>")
    def api_history(theme_id: str):
        get_theme_or_404(theme_id)
        return jsonify(history.get(get_session_id(), theme_id))

    @app.delete("/api/history/<theme_id>")
    def api_clear_history(theme_id: str):
        get_theme_or_404(theme_id)
        history.clear(get_session_id(), theme_id)
        return jsonify({"status": "ok"})

    @app.get("/api/stats/<theme_id>")
    def api_stats(theme_id: str):
        check_admin()
        get_theme_or_404(theme_id)
        return jsonify(history.stats(theme_id))

    # ------------------------------------------------------------------
    # Penanganan Error
    # ------------------------------------------------------------------
    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def handle_error(err):
        if request.path.startswith("/api/"):
            return jsonify({"error": err.description}), err.code
        return (
            render_template("404.html", message=err.description, code=err.code),
            err.code,
        )

    return app


app: Flask = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    app.run(debug=debug_mode)


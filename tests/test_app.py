"""Uji integrasi route dan API Flask menggunakan test client."""
from pathlib import Path

import pytest

from app import create_app

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def client(tmp_path):
    """Fixture client pengujian dengan database SQLite sementara di tmp_path."""
    test_db = tmp_path / "test_chat.db"
    app = create_app({
        "TESTING": True,
        "DATABASE": str(test_db),
        "THEMES_DIR": str(BASE_DIR / "themes"),
    })
    return app.test_client()


def test_halaman_utama_menampilkan_tema(client):
    """Halaman indeks harus menampilkan kartu tema PM-Bot."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "PM-Bot" in html
    assert "Asisten Dasar Manajemen Proyek" in html


def test_halaman_chat(client):
    """Halaman chat pm_bot harus berhasil dibuka dengan kode status 200."""
    res = client.get("/chat/pm_bot")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "PM-Bot" in html


def test_tema_tidak_ada_404(client):
    """Akses ke tema yang tidak ada harus menghasilkan 404."""
    assert client.get("/chat/tidak_ada").status_code == 404
    assert client.get("/api/history/tidak_ada").status_code == 404


def test_api_themes(client):
    """Endpoint /api/themes harus mengembalikan daftar tema yang tersedia."""
    res = client.get("/api/themes")
    assert res.status_code == 200
    data = res.get_json()
    assert any(t["id"] == "pm_bot" for t in data)


def test_api_chat_berhasil(client):
    """Percakapan valid ke /api/chat harus mengembalikan balasan dan intent."""
    payload = {"message": "apa itu agile?", "theme": "pm_bot"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["intent"] == "apa_itu_agile"
    assert data["score"] >= 0.45
    assert len(data["reply"]) > 0


@pytest.mark.parametrize(
    "payload",
    [
        {"message": "", "theme": "pm_bot"},
        {"message": "halo", "theme": "tema_salah"},
        {"message": "a" * 501, "theme": "pm_bot"},
        {},
    ],
)
def test_api_chat_input_tidak_valid(client, payload):
    """Input chat yang melanggar aturan harus menghasilkan kode status 400."""
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_api_chat_bukan_json(client):
    """Request tanpa format JSON valid harus menghasilkan kode status 400."""
    res = client.post("/api/chat", data="bukan json", content_type="text/plain")
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_riwayat_tersimpan_dan_bisa_dihapus(client):
    """Pesan yang dikirim harus tersimpan di riwayat dan dapat dihapus."""
    client.post("/api/chat", json={"message": "halo", "theme": "pm_bot"})

    res_history = client.get("/api/history/pm_bot")
    assert res_history.status_code == 200
    riwayat = res_history.get_json()
    assert len(riwayat) == 2
    assert [r["sender"] for r in riwayat] == ["user", "bot"]

    res_delete = client.delete("/api/history/pm_bot")
    assert res_delete.status_code == 200
    assert res_delete.get_json() == {"status": "ok"}

    res_after = client.get("/api/history/pm_bot")
    assert res_after.get_json() == []


def test_statistik_intent(client):
    """Endpoint /api/stats harus menampilkan distribusi intent yang diajukan user."""
    client.post("/api/chat", json={"message": "apa itu agile", "theme": "pm_bot"})
    res = client.get("/api/stats/pm_bot")
    assert res.status_code == 200
    stats = res.get_json()
    assert len(stats) >= 1
    assert stats[0]["intent"] == "apa_itu_agile"
    assert stats[0]["jumlah"] >= 1


def test_api_explain(client):
    """Endpoint /api/explain harus mengembalikan ambang batas dan daftar kandidat intent."""
    payload = {"message": "tugas scrum master", "theme": "pm_bot"}
    res = client.post("/api/explain", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["threshold"] == 0.45
    assert len(data["candidates"]) >= 1
    assert data["candidates"][0]["intent"] == "tugas_scrum_master"


def test_halaman_admin_menampilkan_pertanyaan_tak_dikenali(client):
    """Halaman admin harus memuat pertanyaan di luar topik yang gagal dikenali."""
    pertanyaan = "resep nasi goreng terenak di dunia"
    client.post("/api/chat", json={"message": pertanyaan, "theme": "pm_bot"})

    res = client.get("/admin/pm_bot")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert pertanyaan in html


def test_admin_key_melindungi_admin_dan_stats(tmp_path):
    """Kunci admin harus melindungi /admin/<theme> dan /api/stats/<theme>."""
    test_db = tmp_path / "test_secure.db"
    app = create_app({
        "TESTING": True,
        "DATABASE": str(test_db),
        "THEMES_DIR": str(BASE_DIR / "themes"),
        "ADMIN_KEY": "kunci_rahasia_123",
    })
    c = app.test_client()

    # Tanpa kunci -> 403
    assert c.get("/admin/pm_bot").status_code == 403
    assert c.get("/api/stats/pm_bot").status_code == 403

    # Kunci salah -> 403
    assert c.get("/admin/pm_bot?key=salah").status_code == 403

    # Kunci benar -> 200
    assert c.get("/admin/pm_bot?key=kunci_rahasia_123").status_code == 200
    assert c.get("/api/stats/pm_bot?key=kunci_rahasia_123").status_code == 200


def test_input_xss_terescape_di_halaman_admin(client):
    """Input mencurigakan berupa script tag harus ter-escape otomatis oleh Jinja2."""
    script_payload = "<script>alert('xss')</script>"
    client.post("/api/chat", json={"message": script_payload, "theme": "pm_bot"})

    res = client.get("/admin/pm_bot")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    # Tag script mentah tidak boleh lolos; harus di-escape menjadi entitas HTML
    assert "<script>alert('xss')</script>" not in html
    assert "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in html


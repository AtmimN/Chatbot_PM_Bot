/**
 * Logika antarmuka obrolan PM-Bot:
 * Mengirim pesan asynchronous menggunakan fetch() ke REST API Flask,
 * mengelola rendering pesan DOM secara aman (anti-XSS), dan mendukung mode belajar.
 */
document.addEventListener("DOMContentLoaded", () => {
  const messagesEl = document.getElementById("messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const btnSubmit = document.getElementById("btn-submit");
  const btnClear = document.getElementById("btn-clear");
  const learnMode = document.getElementById("learn-mode");

  /**
   * Mengurai teks dan mengubah tautan http/https menjadi elemen <a> menggunakan DOM API
   * tanpa innerHTML untuk mencegah serangan XSS.
   */
  function appendTextWithLinks(container, text) {
    const urlPattern = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlPattern);

    parts.forEach((part) => {
      if (/^https?:\/\//i.test(part)) {
        let url = part;
        let suffix = "";
        const matchTrailing = url.match(/[),.\];:]+$/);
        if (matchTrailing) {
          suffix = matchTrailing[0];
          url = url.slice(0, -suffix.length);
        }

        const link = document.createElement("a");
        link.href = url;
        link.textContent = url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        container.appendChild(link);

        if (suffix) {
          container.appendChild(document.createTextNode(suffix));
        }
      } else if (part) {
        container.appendChild(document.createTextNode(part));
      }
    });
  }

  /**
   * Menambahkan satu gelembung percakapan ke layar obrolan.
   */
  function addMessage(sender, text, meta = null) {
    const row = document.createElement("div");
    row.className = `msg msg-${sender}`;

    if (sender === "bot") {
      const avatar = document.createElement("span");
      avatar.className = "msg-avatar";
      avatar.textContent = THEME.avatar;
      row.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    // Gunakan helper DOM untuk mengubah link tanpa menyentuh innerHTML
    appendTextWithLinks(bubble, text);

    if (meta) {
      const metaEl = document.createElement("small");
      metaEl.className = "meta";
      metaEl.textContent = meta;
      bubble.appendChild(metaEl);
    }

    row.appendChild(bubble);
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    return bubble;
  }

  /**
   * Mode belajar: mengambil dan menampilkan 3 kandidat intent teratas dari /api/explain.
   */
  async function showCandidates(bubble, text) {
    try {
      const res = await fetch("/api/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, theme: THEME.id }),
      });
      if (!res.ok) return;

      const data = await res.json();
      const list = document.createElement("ol");
      list.className = "candidates";

      (data.candidates || []).forEach((c) => {
        const li = document.createElement("li");
        const status = c.score >= data.threshold ? "lolos ambang" : "di bawah ambang";
        li.textContent = `${c.intent} · skor ${c.score.toFixed(3)} (${status}) — pola: "${c.pattern}"`;
        list.appendChild(li);
      });

      bubble.appendChild(list);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    } catch (err) {
      console.error("Gagal memuat kandidat mode belajar:", err);
    }
  }

  /**
   * Mengirim pertanyaan pengguna ke backend Flask via POST /api/chat.
   */
  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed) return;

    addMessage("user", trimmed);

    // Tampilkan placeholder indikator bot sedang mengetik
    const typingBubble = addMessage("bot", "sedang mengetik...");
    const typingRow = typingBubble.parentElement;

    input.disabled = true;
    if (btnSubmit) btnSubmit.disabled = true;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, theme: THEME.id }),
      });

      const data = await res.json();
      typingRow.remove();

      if (!res.ok) {
        addMessage("bot", `⚠️ ${data.error || "Terjadi kesalahan saat memproses pesan."}`);
        return;
      }

      const meta = data.intent
        ? `intent: ${data.intent} · skor ${data.score.toFixed(3)}`
        : `tidak dikenali · skor ${data.score.toFixed(3)}`;

      const bubble = addMessage("bot", data.reply, meta);

      if (learnMode && learnMode.checked) {
        await showCandidates(bubble, trimmed);
      }
    } catch (err) {
      typingRow.remove();
      addMessage("bot", "⚠️ Gagal terhubung ke server. Periksa koneksi jaringan Anda.");
      console.error(err);
    } finally {
      input.disabled = false;
      if (btnSubmit) btnSubmit.disabled = false;
      input.focus();
    }
  }

  /**
   * Memuat riwayat obrolan sesi saat pertama kali halaman dibuka.
   */
  async function loadHistory() {
    try {
      const res = await fetch(`/api/history/${THEME.id}`);
      if (!res.ok) {
        addMessage("bot", THEME.greeting);
        return;
      }

      const rows = await res.json();
      if (!rows || rows.length === 0) {
        addMessage("bot", THEME.greeting);
        return;
      }

      rows.forEach((r) => addMessage(r.sender, r.text));
    } catch (err) {
      console.error("Gagal memuat riwayat:", err);
      addMessage("bot", THEME.greeting);
    }
  }

  // --- Penanganan Event Listener ---
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = input.value;
    input.value = "";
    sendMessage(text);
  });

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      sendMessage(chip.textContent);
    });
  });

  if (btnClear) {
    btnClear.addEventListener("click", async () => {
      try {
        await fetch(`/api/history/${THEME.id}`, { method: "DELETE" });
        messagesEl.innerHTML = "";
        addMessage("bot", THEME.greeting);
      } catch (err) {
        console.error("Gagal menghapus riwayat:", err);
      }
    });
  }

  loadHistory();
});


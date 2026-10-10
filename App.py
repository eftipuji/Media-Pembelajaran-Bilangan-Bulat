import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import sqlite3
import os
import re
import json
import hmac
import hashlib
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

# ─────────────────────────────────────────
# KONFIGURASI HALAMAN
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Jelajah Bilangan Bulat",
    page_icon="🔢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# KONSTANTA
# ─────────────────────────────────────────
WIB = ZoneInfo("Asia/Jakarta")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_belajar.db")

# Urutan wajib: KP1 → KP2 → KP3 → Latihan
URUTAN = ["kp1", "kp2", "kp3", "latihan"]

NAMA_HALAMAN = {
    "dashboard": "📊 Dashboard Guru",
    "beranda": "🏠 Beranda",
    "kp1": "📍 KP 1 — Garis Bilangan",
    "kp2": "🔧 KP 2 — Kalkulator Operasi",
    "kp3": "🌳 KP 3 — Pohon Faktor & FPB/KPK",
    "latihan": "📝 Soal Latihan Interaktif",
    "video": "🎬 Video Bahan/Materi",
}

LENCANA = [
    (3, "🥉", "Pemula (3 hari beruntun)"),
    (7, "🥈", "Konsisten (7 hari beruntun)"),
    (14, "🥇", "Tekun (14 hari beruntun)"),
    (30, "💎", "Juara (30 hari beruntun)"),
]

# Soal "Cek Pemahaman" singkat di akhir tiap KP (syarat membuka tahap berikutnya)
CEK = {
    "kp1": {
        "soal": "Urutan bilangan yang benar dari **terkecil ke terbesar** adalah ...",
        "pilihan": ["−2, −5, 0, 3", "−5, −2, 0, 3", "3, 0, −2, −5", "0, −2, −5, 3"],
        "jawaban": 1,
        "petunjuk": "Ingat: semakin ke kiri pada garis bilangan, nilainya semakin kecil.",
    },
    "kp2": {
        "soal": "Hasil dari (−7) × (−6) adalah ...",
        "pilihan": ["−42", "42", "−13", "13"],
        "jawaban": 1,
        "petunjuk": "Tanda sama (− dan −) menghasilkan bilangan positif.",
    },
    "kp3": {
        "soal": "FPB dari 12 dan 18 adalah ...",
        "pilihan": ["3", "6", "36", "2"],
        "jawaban": 1,
        "petunjuk": "12 = 2² × 3 dan 18 = 2 × 3². Ambil faktor sama dengan pangkat terkecil.",
    },
}

# ─────────────────────────────────────────
# DATA SOAL LATIHAN
# ─────────────────────────────────────────
SOAL_LIST = [
    {
        "no": 1, "tipe": "PG", "kp": "KP 1",
        "soal": "Bilangan mana yang memiliki nilai lebih besar?",
        "konteks": "Suhu kota A = −8°C dan suhu kota B = −3°C.",
        "pilihan": ["A. −8 karena angkanya lebih besar", "B. −3 karena letaknya lebih ke kanan pada garis bilangan",
                    "C. Keduanya sama", "D. −8 karena berarti lebih dingin"],
        "jawaban": "B", "pembahasan": "Pada garis bilangan, −3 terletak lebih ke KANAN dibanding −8. Semakin ke kanan → nilai semakin besar. Jadi −3 > −8."
    },
    {
        "no": 2, "tipe": "PG", "kp": "KP 1",
        "soal": "Invers penjumlahan dari −17 adalah ...",
        "konteks": "",
        "pilihan": ["A. 17", "B. −17", "C. 1/17", "D. 0"],
        "jawaban": "A", "pembahasan": "Invers penjumlahan dari −17 adalah +17, karena (−17) + (+17) = 0."
    },
    {
        "no": 3, "tipe": "PG", "kp": "KP 2",
        "soal": "Hasil dari (−8) × (−5) + (−4) × 3 adalah ...",
        "konteks": "",
        "pilihan": ["A. −52", "B. 28", "C. 52", "D. −28"],
        "jawaban": "B", "pembahasan": "(−8)×(−5) = +40 (tanda sama → positif); (−4)×3 = −12 (tanda berbeda → negatif); 40 + (−12) = 28."
    },
    {
        "no": 4, "tipe": "PG", "kp": "KP 2",
        "soal": "Suhu awal gudang beku adalah −15°C. Suhu turun lagi 8°C, lalu naik 5°C. Suhu akhir gudang adalah ...",
        "konteks": "💡 Ini soal literasi finansial tentang perubahan suhu.",
        "pilihan": ["A. −18°C", "B. −28°C", "C. 18°C", "D. 28°C"],
        "jawaban": "A", "pembahasan": "−15 + (−8) + 5 = −15 − 8 + 5 = −23 + 5 = −18°C."
    },
    {
        "no": 5, "tipe": "PG", "kp": "KP 3",
        "soal": "Faktorisasi prima dari 72 adalah ...",
        "konteks": "",
        "pilihan": ["A. 2² × 3²", "B. 2³ × 3²", "C. 2² × 3³", "D. 2⁴ × 3"],
        "jawaban": "B", "pembahasan": "72 = 2×36 = 2×2×18 = 2×2×2×9 = 2×2×2×3×3 = 2³ × 3²."
    },
    {
        "no": 6, "tipe": "PG", "kp": "KP 3",
        "soal": "FPB dari 48 dan 60 adalah ...",
        "konteks": "",
        "pilihan": ["A. 6", "B. 12", "C. 24", "D. 240"],
        "jawaban": "B", "pembahasan": "48 = 2⁴ × 3; 60 = 2² × 3 × 5. FPB = faktor prima sama, pangkat terkecil = 2² × 3 = 4 × 3 = 12."
    },
    {
        "no": 7, "tipe": "Isian", "kp": "KP 2",
        "soal": "Urutkan bilangan berikut dari yang TERKECIL ke TERBESAR:",
        "konteks": "Bilangan: −10, 5, −3, 0, 8, −7, 4",
        "pilihan": None,
        "jawaban": "−10, −7, −3, 0, 4, 5, 8",
        "pembahasan": "Pada garis bilangan dari kiri ke kanan: −10 < −7 < −3 < 0 < 4 < 5 < 8."
    },
    {
        "no": 8, "tipe": "Isian", "kp": "KP 3",
        "soal": "KPK dari 8, 12, dan 15 adalah ...",
        "konteks": "💡 Gunakan Tab Pohon Faktor untuk membantu!",
        "pilihan": None,
        "jawaban": "120",
        "pembahasan": "8 = 2³; 12 = 2² × 3; 15 = 3 × 5. KPK = 2³ × 3 × 5 = 8 × 3 × 5 = 120."
    },
]

# ─────────────────────────────────────────
# CSS KUSTOM
# ─────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }

    /* Header utama */
    .main-header {
        background: linear-gradient(135deg, #1A3C6E 0%, #2E75B6 60%, #70AD47 100%);
        color: white; padding: 1.5rem 2rem; border-radius: 16px;
        text-align: center; margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(26,60,110,0.3);
    }
    .main-header h1 { font-size: 2rem; font-weight: 800; margin: 0; }
    .main-header p  { font-size: 1rem; margin: 0.3rem 0 0; opacity: 0.9; }

    /* Box fase discovery */
    .fase-box {
        border-left: 5px solid #2E75B6; background: #EBF3FB;
        padding: 0.8rem 1rem; border-radius: 0 10px 10px 0;
        margin: 0.7rem 0;
    }
    .fase-box .fase-label {
        font-weight: 800; color: #1A3C6E; font-size: 0.85rem;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .fase-box .fase-text { color: #2C3E50; font-size: 0.95rem; margin-top: 0.2rem; }

    /* Card informasi */
    .info-card {
        background: #F0F7FF; border: 1px solid #BDD7EE;
        border-radius: 12px; padding: 1rem 1.2rem; margin: 0.5rem 0;
    }
    .warning-card {
        background: #FFF8E6; border: 1px solid #FFD966;
        border-radius: 12px; padding: 1rem 1.2rem; margin: 0.5rem 0;
    }
    .success-card {
        background: #F0FBF0; border: 1px solid #70AD47;
        border-radius: 12px; padding: 1rem 1.2rem; margin: 0.5rem 0;
    }
    .danger-card {
        background: #FEF0F0; border: 1px solid #E74C3C;
        border-radius: 12px; padding: 1rem 1.2rem; margin: 0.5rem 0;
    }

    /* Streak */
    .streak-card {
        background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
        border: 1px solid #FFB74D; border-radius: 14px;
        padding: 1rem 1.2rem; margin: 0.5rem 0; color: #5D4037;
    }
    .streak-num { font-size: 2.4rem; font-weight: 800; color: #E65100; line-height: 1; }

    /* Hasil kalkulator */
    .result-display {
        background: linear-gradient(135deg, #1A3C6E, #2E75B6);
        color: white; border-radius: 16px; padding: 1.5rem;
        text-align: center; font-size: 2.5rem; font-weight: 800;
        box-shadow: 0 4px 15px rgba(26,60,110,0.3); margin: 1rem 0;
    }
    .result-label { font-size: 0.85rem; opacity: 0.8; margin-bottom: 0.3rem; }

    /* Tabel eksplorasi */
    .table-header {
        background: #1A3C6E; color: white;
        padding: 0.5rem 1rem; border-radius: 8px 8px 0 0;
        font-weight: 700; font-size: 0.9rem;
    }

    /* Badge tanda */
    .badge-pos { background:#70AD47; color:white; padding:3px 12px; border-radius:20px; font-weight:700; }
    .badge-neg { background:#C00000; color:white; padding:3px 12px; border-radius:20px; font-weight:700; }
    .badge-nol { background:#7F7F7F; color:white; padding:3px 12px; border-radius:20px; font-weight:700; }

    /* Sidebar */
    .sidebar-title {
        background: #1A3C6E; color: white;
        padding: 0.7rem 1rem; border-radius: 10px;
        font-weight: 800; text-align: center; margin-bottom: 0.5rem;
    }

    /* Tombol kustom */
    .stButton > button {
        border-radius: 10px; font-weight: 700;
        transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-2px); }

    /* Metric */
    [data-testid="metric-container"] {
        background: #F8FAFF; border: 1px solid #BDD7EE;
        border-radius: 12px; padding: 0.8rem; text-align: center;
    }

    /* Nomor soal */
    .soal-num {
        background: #2E75B6; color: white;
        width: 30px; height: 30px; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 0.9rem; margin-right: 0.5rem;
    }

    hr { border: none; border-top: 2px solid #EBF3FB; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
# DATABASE (SQLite)
# ══════════════════════════════════════════
def q(sql, params=(), one=False, commit=False):
    """Helper eksekusi SQL sederhana."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        if commit:
            conn.commit()
            return cur.lastrowid
        rows = cur.fetchall()
        if one:
            return rows[0] if rows else None
        return rows
    finally:
        conn.close()


def baca_df(sql, params=()):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


@st.cache_resource
def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS siswa(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        kelas TEXT NOT NULL,
        pin_hash TEXT NOT NULL,
        dibuat TEXT NOT NULL,
        UNIQUE(nama, kelas)
    );
    CREATE TABLE IF NOT EXISTS progres(
        siswa_id INTEGER NOT NULL,
        materi TEXT NOT NULL,
        selesai_pada TEXT NOT NULL,
        PRIMARY KEY(siswa_id, materi)
    );
    CREATE TABLE IF NOT EXISTS aktivitas(
        siswa_id INTEGER NOT NULL,
        tanggal TEXT NOT NULL,
        jumlah INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(siswa_id, tanggal)
    );
    CREATE TABLE IF NOT EXISTS latihan(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        siswa_id INTEGER NOT NULL,
        waktu TEXT NOT NULL,
        skor INTEGER NOT NULL,
        total INTEGER NOT NULL,
        detail TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS refleksi(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        siswa_id INTEGER NOT NULL,
        waktu TEXT NOT NULL,
        r1 TEXT, r2 TEXT, r3 TEXT
    );
    """)
    conn.commit()
    conn.close()
    return True


init_db()


# ══════════════════════════════════════════
# FUNGSI BANTU: WAKTU, AUTENTIKASI, PROGRES, STREAK
# ══════════════════════════════════════════
def sekarang():
    return datetime.now(WIB)


def hari_ini():
    return sekarang().date()


def hash_pin(pin):
    return hashlib.sha256(("jbb-v1-" + pin).encode()).hexdigest()


def get_guru_password():
    """Ambil password guru dari st.secrets (GURU_PASSWORD). Default: guru123 (SEGERA GANTI!)."""
    try:
        return str(st.secrets["GURU_PASSWORD"])
    except Exception:
        return "guru123"


def is_guru():
    return st.session_state.get("is_guru", False)


def masuk_siswa(nama, kelas, pin):
    nama = " ".join(nama.split()).title()
    kelas = " ".join(kelas.split()).upper()
    row = q("SELECT * FROM siswa WHERE lower(nama)=? AND lower(kelas)=?",
            (nama.lower(), kelas.lower()), one=True)
    if row:
        if row["pin_hash"] != hash_pin(pin):
            return None, "PIN salah. Gunakan PIN yang kamu buat saat pertama kali masuk."
        return {"id": row["id"], "nama": row["nama"], "kelas": row["kelas"]}, None
    sid = q("INSERT INTO siswa(nama,kelas,pin_hash,dibuat) VALUES(?,?,?,?)",
            (nama, kelas, hash_pin(pin), sekarang().strftime("%Y-%m-%d %H:%M")), commit=True)
    return {"id": sid, "nama": nama, "kelas": kelas}, None


def get_selesai(sid):
    return {r["materi"] for r in q("SELECT materi FROM progres WHERE siswa_id=?", (sid,))}


def catat_aktivitas(sid, n=1):
    q("""INSERT INTO aktivitas(siswa_id,tanggal,jumlah) VALUES(?,?,?)
         ON CONFLICT(siswa_id,tanggal) DO UPDATE SET jumlah=jumlah+excluded.jumlah""",
      (sid, str(hari_ini()), n), commit=True)


def tandai_selesai(sid, materi):
    q("INSERT OR IGNORE INTO progres(siswa_id,materi,selesai_pada) VALUES(?,?,?)",
      (sid, materi, sekarang().strftime("%Y-%m-%d %H:%M")), commit=True)
    catat_aktivitas(sid, 3)


def get_tanggal_aktif(sid):
    return {date.fromisoformat(r["tanggal"])
            for r in q("SELECT tanggal FROM aktivitas WHERE siswa_id=?", (sid,))}


def hitung_streak(tgl_set, today=None):
    """Return (streak_saat_ini, streak_terpanjang)."""
    today = today or hari_ini()
    if not tgl_set:
        return 0, 0
    cur = 0
    d = today if today in tgl_set else today - timedelta(days=1)
    while d in tgl_set:
        cur += 1
        d -= timedelta(days=1)
    urut = sorted(tgl_set)
    best = run = 1
    for i in range(1, len(urut)):
        run = run + 1 if (urut[i] - urut[i - 1]).days == 1 else 1
        best = max(best, run)
    return cur, best


def akses_terbuka(halaman, selesai):
    """Cek apakah halaman boleh dibuka (urut KP1→KP2→KP3→Latihan)."""
    if is_guru() or halaman not in URUTAN:
        return True
    idx = URUTAN.index(halaman)
    return idx == 0 or URUTAN[idx - 1] in selesai


def pindah(halaman):
    st.session_state.menu = halaman


def simpan_latihan(sid, skor, total, detail):
    q("INSERT INTO latihan(siswa_id,waktu,skor,total,detail) VALUES(?,?,?,?,?)",
      (sid, sekarang().strftime("%Y-%m-%d %H:%M"), skor, total, json.dumps(detail)), commit=True)


# ══════════════════════════════════════════
# FUNGSI BANTU: MATEMATIKA
# ══════════════════════════════════════════
def faktorisasi_prima(n):
    faktor = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            faktor[d] = faktor.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        faktor[n] = faktor.get(n, 0) + 1
    return faktor


def semua_faktor(n):
    return [i for i in range(1, n + 1) if n % i == 0]


def angka(teks):
    return re.findall(r"-?\d+(?:[.,]\d+)?", str(teks).replace("−", "-").replace("–", "-"))


def periksa(soal, jawab):
    if not jawab:
        return False
    if soal["tipe"] == "PG":
        return jawab.strip()[0] == soal["jawaban"]
    return angka(jawab) == angka(soal["jawaban"])


# ══════════════════════════════════════════
# KOMPONEN UI: STREAK, KETERCAPAIAN, CEK PEMAHAMAN
# ══════════════════════════════════════════
def tampil_streak(sid):
    tgl = get_tanggal_aktif(sid)
    cur, best = hitung_streak(tgl)
    today = hari_ini()
    hari = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]

    kotak = ""
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        aktif = d in tgl
        bg = "#FF9800" if aktif else "#E0E0E0"
        ikon = "🔥" if aktif else ""
        ring = "box-shadow:0 0 0 3px #1A3C6E;" if d == today else ""
        kotak += (
            '<div style="text-align:center;">'
            f'<div style="width:34px;height:34px;border-radius:50%;background:{bg};{ring}'
            'display:flex;align-items:center;justify-content:center;margin:auto;">'
            f'{ikon}</div>'
            f'<div style="font-size:0.7rem;color:#666;margin-top:2px;">{hari[d.weekday()]}</div></div>'
        )

    if today in tgl:
        status = "✅ Target hari ini tercapai!"
    else:
        status = "⏳ Belum belajar hari ini — buka satu materi untuk menjaga streak-mu!"

    lencana_html = ""
    for target, ikon, nama in LENCANA:
        if best >= target:
            lencana_html += f'<span title="{nama}" style="font-size:1.5rem;margin-right:4px;">{ikon}</span>'
        else:
            lencana_html += f'<span title="Terkunci: {nama}" style="font-size:1.5rem;margin-right:4px;opacity:0.25;">{ikon}</span>'

    berikut = next((t for t, _, _ in LENCANA if cur < t), None)
    teks_target = f"{berikut - cur} hari lagi menuju lencana berikutnya!" if berikut else "Semua lencana sudah kamu raih! 🎉"

    st.markdown(f"""
    <div class="streak-card">
        <div style="display:flex;align-items:center;gap:0.8rem;">
            <div style="font-size:2.4rem;">🔥</div>
            <div>
                <span class="streak-num">{cur}</span> <b>hari beruntun</b><br>
                <span style="font-size:0.8rem;">Rekor terpanjang: <b>{best} hari</b> • Total hari belajar: <b>{len(tgl)}</b></span>
            </div>
        </div>
        <div style="display:flex;gap:10px;justify-content:space-between;margin:0.8rem 0 0.4rem;">{kotak}</div>
        <div style="font-size:0.85rem;font-weight:700;margin-top:0.4rem;">{status}</div>
        <div style="margin-top:0.4rem;">{lencana_html}</div>
        <div style="font-size:0.78rem;opacity:0.85;">{teks_target}</div>
    </div>
    """, unsafe_allow_html=True)


def tampil_ketercapaian(sid, selesai):
    jml = len([k for k in URUTAN if k in selesai])
    persen = int(jml / len(URUTAN) * 100)
    st.markdown(f'<div class="info-card"><b>🎯 Ketercapaian Pembelajaran: {persen}%</b><br>'
                f'<span style="font-size:0.85rem;">{jml} dari {len(URUTAN)} tahap selesai</span></div>',
                unsafe_allow_html=True)
    st.progress(persen / 100)
    baris = ""
    for k in URUTAN:
        if k in selesai:
            ikon = "✅"
        elif akses_terbuka(k, selesai):
            ikon = "▶️"
        else:
            ikon = "🔒"
        baris += f"{ikon} {NAMA_HALAMAN[k]}<br>"
    st.markdown(f'<div style="font-size:0.9rem;line-height:1.9;">{baris}</div>', unsafe_allow_html=True)

    best = q("SELECT MAX(CAST(skor AS REAL)/total*100) AS n, COUNT(*) AS c FROM latihan WHERE siswa_id=?",
             (sid,), one=True)
    if best and best["c"]:
        st.markdown(f'<div class="success-card">🏆 Nilai terbaik latihan: <b>{best["n"]:.0f}</b> '
                    f'({best["c"]}x percobaan)</div>', unsafe_allow_html=True)


def blok_selesai(kp):
    """Cek pemahaman di akhir KP. Lulus → KP ditandai selesai & tahap berikutnya terbuka."""
    st.markdown("---")
    st.markdown("### 🏁 Cek Pemahaman & Selesaikan Kegiatan Ini")
    if is_guru():
        st.info("👩‍🏫 Mode pratinjau guru: cek pemahaman tidak dicatat.")
        return

    sid = st.session_state.siswa["id"]
    selesai = get_selesai(sid)
    berikut = {"kp1": "kp2", "kp2": "kp3", "kp3": "latihan"}[kp]

    if kp in selesai:
        if st.session_state.pop("balon", None) == kp:
            st.balloons()
        st.markdown(f'<div class="success-card">✅ <b>Kegiatan ini sudah selesai!</b><br>'
                    f'Tahap berikutnya sudah terbuka: <b>{NAMA_HALAMAN[berikut]}</b></div>',
                    unsafe_allow_html=True)
        st.button(f"➡️ Lanjut ke {NAMA_HALAMAN[berikut]}", on_click=pindah, args=(berikut,), type="primary")
        return

    cek = CEK[kp]
    st.markdown(f"""<div class="warning-card">
    Jawab 1 pertanyaan singkat untuk membuka tahap berikutnya.
    Pastikan kamu sudah menyelesaikan eksplorasi dan mencatat temuan di LKS.</div>""",
                unsafe_allow_html=True)
    st.markdown(cek["soal"])
    jawab = st.radio("Pilih jawaban:", cek["pilihan"], index=None, key=f"cek_{kp}")
    catat = st.checkbox("Saya sudah mencatat temuan eksplorasi di LKS", key=f"lks_{kp}")

    if st.button("✅ Periksa & Selesaikan", key=f"btn_{kp}", type="primary"):
        if jawab is None:
            st.warning("Pilih salah satu jawaban dulu ya.")
        elif not catat:
            st.warning("Centang dulu bahwa kamu sudah mencatat temuan di LKS.")
        elif cek["pilihan"].index(jawab) != cek["jawaban"]:
            st.error(f"Belum tepat. 💡 Petunjuk: {cek['petunjuk']} Coba eksplorasi lagi lalu jawab ulang.")
        else:
            tandai_selesai(sid, kp)
            st.session_state["balon"] = kp
            st.rerun()


def tampil_terkunci(halaman, selesai):
    idx = URUTAN.index(halaman)
    syarat = URUTAN[idx - 1]
    st.markdown(f"## 🔒 {NAMA_HALAMAN[halaman]}")
    st.markdown(f"""
    <div class="warning-card">
    <b>Tahap ini masih terkunci.</b><br><br>
    Alur belajar harus berurutan: <b>KP 1 → KP 2 → KP 3 → Soal Latihan</b>.<br>
    Selesaikan dulu: <b>{NAMA_HALAMAN[syarat]}</b>
    </div>
    """, unsafe_allow_html=True)
    # cari tahap pertama yang belum selesai
    target = next((k for k in URUTAN if k not in selesai), URUTAN[0])
    st.button(f"➡️ Ke {NAMA_HALAMAN[target]}", on_click=pindah, args=(target,), type="primary")


# ══════════════════════════════════════════
# HALAMAN LOGIN
# ══════════════════════════════════════════
def halaman_login():
    st.markdown("## 🔐 Silakan Masuk")
    t1, t2 = st.tabs(["🎒 Siswa", "👩‍🏫 Guru"])

    with t1:
        st.markdown("""
        <div class="info-card">
        <b>Pertama kali masuk?</b> Isi nama, kelas, lalu <b>buat PIN 4 angka</b> — akunmu otomatis dibuat.<br>
        Lain kali, masuk dengan nama, kelas, dan PIN yang sama agar progres & streak-mu tersimpan.
        </div>
        """, unsafe_allow_html=True)
        with st.form("form_siswa"):
            nama = st.text_input("Nama lengkap", placeholder="contoh: Budi Santoso")
            kelas = st.text_input("Kelas", placeholder="contoh: VII A")
            pin = st.text_input("PIN (4 angka)", type="password", max_chars=4)
            ok = st.form_submit_button("🚀 Masuk / Daftar", type="primary")
        if ok:
            if len(nama.strip()) < 3:
                st.error("Nama minimal 3 karakter.")
            elif not kelas.strip():
                st.error("Kelas wajib diisi.")
            elif not (pin.isdigit() and len(pin) == 4):
                st.error("PIN harus 4 angka.")
            else:
                data, err = masuk_siswa(nama, kelas, pin)
                if err:
                    st.error(err)
                else:
                    st.session_state.siswa = data
                    st.session_state.menu = "beranda"
                    st.rerun()

    with t2:
        with st.form("form_guru"):
            pw = st.text_input("Password guru", type="password")
            ok2 = st.form_submit_button("🔓 Masuk sebagai Guru", type="primary")
        if ok2:
            if hmac.compare_digest(pw.encode(), get_guru_password().encode()):
                st.session_state.is_guru = True
                st.session_state.menu = "dashboard"
                st.rerun()
            else:
                st.error("Password salah.")


# ══════════════════════════════════════════
# DASHBOARD GURU
# ══════════════════════════════════════════
def halaman_dashboard():
    st.markdown("## 📊 Dashboard Guru — Pemantauan Siswa")
    today = hari_ini()

    siswa = baca_df("SELECT id,nama,kelas,dibuat FROM siswa ORDER BY kelas,nama")
    if siswa.empty:
        st.info("Belum ada siswa yang mendaftar. Bagikan link aplikasi kepada siswa.")
        return
    prog = baca_df("SELECT siswa_id,materi,selesai_pada FROM progres")
    akt = baca_df("SELECT siswa_id,tanggal,jumlah FROM aktivitas")
    lat = baca_df("SELECT id,siswa_id,waktu,skor,total,detail FROM latihan")

    rows = []
    for _, s in siswa.iterrows():
        sid = s["id"]
        done = set(prog.loc[prog.siswa_id == sid, "materi"])
        tg = {date.fromisoformat(t) for t in akt.loc[akt.siswa_id == sid, "tanggal"]}
        cur, best = hitung_streak(tg)
        l = lat[lat.siswa_id == sid]
        nilai = (l.skor / l.total * 100) if not l.empty else pd.Series(dtype=float)
        terakhir = max(tg) if tg else None
        tak_aktif = (today - terakhir).days if terakhir else None
        persen = int(len([k for k in URUTAN if k in done]) / len(URUTAN) * 100)

        if persen == 100:
            status = "🏆 Tuntas"
        elif terakhir is None or persen == 0:
            status = "⏳ Belum mulai"
        elif tak_aktif is not None and tak_aktif >= 3:
            status = f"⚠️ Tidak aktif {tak_aktif} hari"
        else:
            status = "🟢 Sedang belajar"

        rows.append({
            "ID": sid, "Nama": s["nama"], "Kelas": s["kelas"],
            "kp1": "kp1" in done, "kp2": "kp2" in done, "kp3": "kp3" in done, "latihan": "latihan" in done,
            "Nilai Terbaik": round(nilai.max()) if not nilai.empty else np.nan,
            "Nilai Terakhir": round(nilai.iloc[-1]) if not nilai.empty else np.nan,
            "Percobaan": len(l), "Progres": persen,
            "Streak": cur, "Rekor": best, "Hari Belajar": len(tg),
            "Terakhir Aktif": str(terakhir) if terakhir else "-",
            "_terakhir": terakhir, "Status": status,
        })
    rekap = pd.DataFrame(rows)

    # ── Filter
    f1, f2 = st.columns([2, 2])
    with f1:
        kelas_pilih = st.multiselect("Filter kelas:", sorted(rekap["Kelas"].unique()),
                                     default=sorted(rekap["Kelas"].unique()))
    with f2:
        cari = st.text_input("🔎 Cari nama siswa:", placeholder="ketik nama...")
    rf = rekap[rekap["Kelas"].isin(kelas_pilih)]
    if cari.strip():
        rf = rf[rf["Nama"].str.contains(cari.strip(), case=False)]
    if rf.empty:
        st.warning("Tidak ada data sesuai filter.")
        return

    # ── Metrik
    aktif_hari_ini = int((rf["_terakhir"] == today).sum())
    nilai_rata = rf["Nilai Terbaik"].mean()
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("👥 Total Siswa", len(rf))
    m2.metric("🟢 Aktif Hari Ini", aktif_hari_ini)
    m3.metric("📈 Rata-rata Progres", f"{rf['Progres'].mean():.0f}%")
    m4.metric("🎯 Rata-rata Nilai Terbaik", "-" if pd.isna(nilai_rata) else f"{nilai_rata:.0f}")
    m5.metric("🏆 Tuntas Semua", int((rf["Progres"] == 100).sum()))

    tab_a, tab_b, tab_c, tab_d, tab_e, tab_f = st.tabs(
        ["📋 Rekap Siswa", "📈 Ringkasan", "🧑‍🎓 Detail Siswa", "🧮 Analisis Soal", "💭 Refleksi", "⚙️ Kelola Data"])

    # ── Rekap
    with tab_a:
        tampil = rf.copy()
        for k, lbl in [("kp1", "KP 1"), ("kp2", "KP 2"), ("kp3", "KP 3"), ("latihan", "Latihan")]:
            tampil[lbl] = tampil[k].map({True: "✅", False: "—"})
        kolom = ["Nama", "Kelas", "KP 1", "KP 2", "KP 3", "Latihan", "Nilai Terbaik", "Nilai Terakhir",
                 "Percobaan", "Progres", "Streak", "Rekor", "Hari Belajar", "Terakhir Aktif", "Status"]
        st.dataframe(
            tampil[kolom], use_container_width=True, hide_index=True,
            column_config={
                "Progres": st.column_config.ProgressColumn("Progres", min_value=0, max_value=100, format="%d%%"),
                "Streak": st.column_config.NumberColumn("🔥 Streak", help="Hari beruntun saat ini"),
                "Rekor": st.column_config.NumberColumn("🏅 Rekor"),
            })
        st.caption("Status ⚠️ muncul bila siswa belum membuka materi ≥ 3 hari dan belum tuntas.")

    # ── Ringkasan
    with tab_b:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Jumlah siswa yang menyelesaikan tiap tahap**")
            fun = pd.DataFrame({
                "Siswa": [int(rf["kp1"].sum()), int(rf["kp2"].sum()), int(rf["kp3"].sum()), int(rf["latihan"].sum())]
            }, index=["KP 1", "KP 2", "KP 3", "Latihan"])
            st.bar_chart(fun)
        with c2:
            st.markdown("**Siswa aktif per hari (14 hari terakhir)**")
            ids = set(rf["ID"])
            akt_f = akt[akt.siswa_id.isin(ids)]
            rng = [today - timedelta(days=i) for i in range(13, -1, -1)]
            cnt = [akt_f[akt_f.tanggal == str(d)].siswa_id.nunique() for d in rng]
            st.bar_chart(pd.DataFrame({"Siswa aktif": cnt}, index=[d.strftime("%d/%m") for d in rng]))

        st.markdown("**⚠️ Siswa yang perlu perhatian**")
        perlu = rf[rf["Status"].str.startswith("⚠️") | rf["Status"].str.startswith("⏳")]
        if perlu.empty:
            st.success("Semua siswa berjalan baik. 🎉")
        else:
            st.dataframe(perlu[["Nama", "Kelas", "Progres", "Terakhir Aktif", "Status"]],
                         use_container_width=True, hide_index=True)

        st.markdown("**🔥 Papan Streak Teratas**")
        top = rf.sort_values(["Streak", "Rekor"], ascending=False).head(5)
        st.dataframe(top[["Nama", "Kelas", "Streak", "Rekor", "Hari Belajar"]],
                     use_container_width=True, hide_index=True)

    # ── Detail siswa
    with tab_c:
        opsi = {f"{r['Nama']} ({r['Kelas']})": r["ID"] for _, r in rf.iterrows()}
        pilih = st.selectbox("Pilih siswa:", list(opsi.keys()))
        sid = int(opsi[pilih])
        d1, d2 = st.columns([1, 1])
        with d1:
            tampil_streak(sid)
            tampil_ketercapaian(sid, get_selesai(sid))
        with d2:
            st.markdown("**Riwayat percobaan latihan**")
            lsi = lat[lat.siswa_id == sid].sort_values("id", ascending=False)
            if lsi.empty:
                st.info("Belum mengerjakan latihan.")
            else:
                lsi = lsi.assign(Nilai=(lsi.skor / lsi.total * 100).round(0).astype(int))
                st.dataframe(lsi[["waktu", "skor", "total", "Nilai"]].rename(
                    columns={"waktu": "Waktu", "skor": "Benar", "total": "Total soal"}),
                    use_container_width=True, hide_index=True)
            st.markdown("**Tahap yang diselesaikan**")
            ps = prog[prog.siswa_id == sid]
            if ps.empty:
                st.info("Belum ada tahap yang selesai.")
            else:
                st.dataframe(ps[["materi", "selesai_pada"]].rename(
                    columns={"materi": "Tahap", "selesai_pada": "Selesai pada"}),
                    use_container_width=True, hide_index=True)

    # ── Analisis soal
    with tab_d:
        lat_f = lat[lat.siswa_id.isin(set(rf["ID"]))]
        if lat_f.empty:
            st.info("Belum ada siswa yang mengerjakan latihan.")
        else:
            terakhir = lat_f.sort_values("id").groupby("siswa_id").tail(1)
            benar = {s["no"]: 0 for s in SOAL_LIST}
            for dj in terakhir["detail"]:
                for d in json.loads(dj):
                    benar[d["no"]] += int(d["benar"])
            n = len(terakhir)
            hasil = []
            for s in SOAL_LIST:
                hasil.append({
                    "No": s["no"], "KP": s["kp"], "Tipe": s["tipe"],
                    "Soal": s["soal"][:60] + ("..." if len(s["soal"]) > 60 else ""),
                    "Benar": benar[s["no"]], "% Benar": round(benar[s["no"]] / n * 100),
                })
            dfa = pd.DataFrame(hasil)
            st.caption(f"Berdasarkan percobaan TERAKHIR dari {n} siswa.")
            st.dataframe(dfa, use_container_width=True, hide_index=True,
                         column_config={"% Benar": st.column_config.ProgressColumn(
                             "% Benar", min_value=0, max_value=100, format="%d%%")})
            st.bar_chart(dfa.set_index("No")["% Benar"])
            sulit = dfa[dfa["% Benar"] < 60]
            if sulit.empty:
                st.success("Tidak ada soal dengan tingkat benar < 60%.")
            else:
                st.warning("Soal yang sebaiknya dibahas ulang di kelas (benar < 60%): " +
                           ", ".join(f"No. {x} ({k})" for x, k in zip(sulit["No"], sulit["KP"])))

    # ── Refleksi
    with tab_e:
        ref = baca_df("""SELECT s.nama AS Nama, s.kelas AS Kelas, r.waktu AS Waktu,
                                r.r1 AS 'Fitur paling membantu', r.r2 AS 'Temuan dari kalkulator',
                                r.r3 AS 'Perasaan belajar'
                         FROM refleksi r JOIN siswa s ON s.id=r.siswa_id ORDER BY r.id DESC""")
        ref = ref[ref["Kelas"].isin(kelas_pilih)] if not ref.empty else ref
        if ref.empty:
            st.info("Belum ada refleksi yang disimpan siswa.")
        else:
            st.dataframe(ref, use_container_width=True, hide_index=True)

    # ── Kelola data
    with tab_f:
        st.markdown("**📥 Unduh data**")
        unduh = rf.drop(columns=["ID", "_terakhir", "kp1", "kp2", "kp3", "latihan"]).copy()
        st.download_button("⬇️ Unduh Rekap Siswa (CSV)", unduh.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"rekap_siswa_{today}.csv", mime="text/csv")
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "rb") as f:
                st.download_button("💾 Unduh Backup Database (.db)", f.read(),
                                   file_name=f"backup_data_belajar_{today}.db")
        st.caption("Lakukan backup rutin: pada Streamlit Community Cloud, file database dapat hilang saat aplikasi di-reboot/redeploy.")

        st.markdown("---")
        st.markdown("**🗑️ Hapus siswa**")
        opsi_h = {f"{r['Nama']} ({r['Kelas']})": int(r["ID"]) for _, r in rekap.iterrows()}
        hapus = st.selectbox("Pilih siswa yang akan dihapus:", list(opsi_h.keys()), key="hapus_pilih")
        yakin = st.checkbox("Saya yakin menghapus siswa ini beserta seluruh datanya", key="hapus_yakin")
        if st.button("Hapus Siswa", disabled=not yakin):
            hid = opsi_h[hapus]
            for tbl in ["progres", "aktivitas", "latihan", "refleksi"]:
                q(f"DELETE FROM {tbl} WHERE siswa_id=?", (hid,), commit=True)
            q("DELETE FROM siswa WHERE id=?", (hid,), commit=True)
            st.success("Siswa dihapus.")
            st.rerun()

        st.markdown("---")
        st.markdown("**⚠️ Reset semua data**")
        konfirmasi = st.text_input("Ketik HAPUS SEMUA untuk mereset seluruh data:", key="reset_all")
        if st.button("Reset Seluruh Data", disabled=(konfirmasi != "HAPUS SEMUA")):
            for tbl in ["progres", "aktivitas", "latihan", "refleksi", "siswa"]:
                q(f"DELETE FROM {tbl}", commit=True)
            st.success("Seluruh data direset.")
            st.rerun()


# ══════════════════════════════════════════
# CALLBACK LATIHAN
# ══════════════════════════════════════════
def kirim_latihan():
    detail, skor = [], 0
    for s in SOAL_LIST:
        j = st.session_state.get(f"soal_{s['no']}")
        b = periksa(s, j)
        skor += int(b)
        detail.append({"no": s["no"], "jawab": j or "", "benar": bool(b)})
    sid = st.session_state.siswa["id"]
    simpan_latihan(sid, skor, len(SOAL_LIST), detail)
    tandai_selesai(sid, "latihan")
    st.session_state.hasil_latihan = {"skor": skor, "detail": detail}


def ulangi_latihan():
    for s in SOAL_LIST:
        st.session_state.pop(f"soal_{s['no']}", None)
    st.session_state.pop("hasil_latihan", None)


# ══════════════════════════════════════════
# HEADER UTAMA
# ══════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>🔢 Jelajah Bilangan Bulat</h1>
    <p>Kalkulator Digital Interaktif • Metode Discovery Learning • SMP/MTs Kelas VII</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# GERBANG LOGIN
# ══════════════════════════════════════════
if "siswa" not in st.session_state and not is_guru():
    halaman_login()
    st.stop()

SISWA = st.session_state.get("siswa")
SID = SISWA["id"] if SISWA else None
SELESAI = get_selesai(SID) if SID else set()

# ══════════════════════════════════════════
# SIDEBAR NAVIGASI
# ══════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sidebar-title">🧭 Menu Navigasi</div>', unsafe_allow_html=True)

    if is_guru():
        st.markdown('<div class="info-card" style="font-size:0.85rem;">👩‍🏫 <b>Mode Guru</b><br>Semua materi terbuka (pratinjau, tidak tercatat).</div>',
                    unsafe_allow_html=True)
        opsi_menu = ["dashboard", "beranda", "kp1", "kp2", "kp3", "latihan", "video"]
    else:
        cur_s, _ = hitung_streak(get_tanggal_aktif(SID))
        persen_s = int(len([k for k in URUTAN if k in SELESAI]) / len(URUTAN) * 100)
        st.markdown(f"""
        <div class="info-card" style="font-size:0.85rem;">
        👤 <b>{SISWA['nama']}</b><br>Kelas {SISWA['kelas']}<br>
        🔥 Streak: <b>{cur_s} hari</b> • 🎯 Progres: <b>{persen_s}%</b>
        </div>
        """, unsafe_allow_html=True)
        opsi_menu = ["beranda", "kp1", "kp2", "kp3", "latihan", "video"]

    if st.session_state.get("menu") not in opsi_menu:
        st.session_state.menu = opsi_menu[0]

    def label_menu(k):
        base = NAMA_HALAMAN[k]
        if is_guru() or k not in URUTAN:
            return base
        if k in SELESAI:
            return "✅ " + base
        if akses_terbuka(k, SELESAI):
            return "▶️ " + base
        return "🔒 " + base

    tab_choice = st.radio("Pilih Fitur:", options=opsi_menu, key="menu",
                          format_func=label_menu, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("""
    <div style="background:#F0F7FF;padding:0.8rem;border-radius:10px;font-size:0.82rem;color:#1A3C6E;">
    <b>📚 Petunjuk Penggunaan</b><br><br>
    1. Belajar <b>berurutan</b>: KP 1 → KP 2 → KP 3 → Latihan<br>
    2. Ikuti langkah-langkah Discovery Learning<br>
    3. Catat temuan di LKS<br>
    4. Jawab Cek Pemahaman untuk membuka tahap berikutnya<br>
    5. Belajar tiap hari untuk menjaga 🔥 streak
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    if st.button("🚪 Keluar", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.markdown("""
    <div style="font-size:0.78rem;color:#7F7F7F;text-align:center;margin-top:0.5rem;">
    🎓 Kurikulum Merdeka Fase D<br>
    Penulis: Efti Puji Lestari
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# GERBANG URUTAN BELAJAR
# ══════════════════════════════════════════
if tab_choice in URUTAN and not akses_terbuka(tab_choice, SELESAI):
    tampil_terkunci(tab_choice, SELESAI)
    st.stop()

# Catat aktivitas harian (1x per hari per sesi) saat membuka halaman belajar → daily streak
if SID and tab_choice in URUTAN + ["video"]:
    kunci_log = f"log_{hari_ini()}"
    if not st.session_state.get(kunci_log):
        catat_aktivitas(SID, 1)
        st.session_state[kunci_log] = True

# ══════════════════════════════════════════
# DASHBOARD GURU
# ══════════════════════════════════════════
if tab_choice == "dashboard":
    halaman_dashboard()

# ══════════════════════════════════════════
# HALAMAN BERANDA
# ══════════════════════════════════════════
elif tab_choice == "beranda":
    st.markdown("## 👋 Selamat Datang, Penjelajah Matematika!")

    if SID:
        st.markdown("### 🏅 Papan Ketercapaian Belajarmu")
        ca, cb = st.columns(2)
        with ca:
            tampil_ketercapaian(SID, SELESAI)
        with cb:
            tampil_streak(SID)
        st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="info-card">
        <b>🎯 Fokus Kemampuan</b><br><br>
        ✅ Operasi Hitung Bilangan Bulat (TP 5)<br>
        ✅ FPB & KPK via Faktorisasi Prima (TP 8)<br>
        ✅ Masalah Kontekstual & Literasi Finansial (TP 9)
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="info-card">
        <b>🔬 Metode Pembelajaran</b><br><br>
        🔵 Discovery Learning (utama)<br>
        🟢 Problem Based Learning<br>
        🟡 Cooperative Learning
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="info-card">
        <b>📱 Fitur Aplikasi</b><br><br>
        📍 Garis Bilangan Interaktif<br>
        🔧 Kalkulator Operasi Hitung<br>
        🌳 Pohon Faktor & FPB/KPK<br>
        📝 Soal Latihan Interaktif<br>
        🔥 Daily Streak & Ketercapaian
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔬 Alur Discovery Learning dalam Aplikasi Ini")

    fases = [
        ("① STIMULATION", "Kamu akan dihadapkan pada situasi nyata yang menantang — tentang suhu, uang, atau lampu yang berkedip. Ini akan membuatmu penasaran!", "#2E75B6"),
        ("② PROBLEM STATEMENT", "Kamu merumuskan pertanyaan sendiri. Apa yang ingin kamu temukan?", "#ED7D31"),
        ("③ DATA COLLECTION", "Eksplorasi bebas menggunakan kalkulator digital! Coba berbagai kombinasi dan catat hasilnya di LKS.", "#70AD47"),
        ("④ DATA PROCESSING", "Analisis pola dari data yang kamu kumpulkan. Apa yang kamu temukan?", "#7030A0"),
        ("⑤ VERIFICATION", "Bandingkan temuanmu dengan teman sekelompok. Apakah sama?", "#C00000"),
        ("⑥ GENERALIZATION", "Rumuskan kesimpulan dengan kata-katamu sendiri. Inilah ilmu yang benar-benar kamu pahami!", "#1A3C6E"),
    ]

    cols = st.columns(3)
    for i, (label, text, color) in enumerate(fases):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="border-left:4px solid {color};background:#FAFAFA;
                        padding:0.8rem 1rem;border-radius:0 10px 10px 0;margin-bottom:0.8rem;">
                <div style="font-weight:800;color:{color};font-size:0.9rem;">{label}</div>
                <div style="font-size:0.85rem;color:#444;margin-top:0.3rem;">{text}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div class="warning-card">
    <b>💡 Tips Belajar Efektif</b><br>
    Jangan langsung klik-klik tanpa tujuan! Sebelum mengeksplorasi, baca dulu petunjuk di LKS,
    lalu gunakan kalkulator digital ini untuk <b>membuktikan hipotesismu</b> dan
    <b>menemukan pola</b> yang tersembunyi dalam bilangan bulat. Catat semua temuanmu!
    </div>
    """, unsafe_allow_html=True)
    if SID:
        st.button("▶️ Mulai / Lanjutkan Belajar", type="primary", on_click=pindah,
                  args=(next((k for k in URUTAN if k not in SELESAI), "latihan"),))


# ══════════════════════════════════════════
# KP 1 — GARIS BILANGAN
# ══════════════════════════════════════════
elif tab_choice == "kp1":
    st.markdown("## 📍 Kegiatan Pembelajaran 1: Memahami Bilangan Bulat")

    # STIMULATION
    st.markdown("""
    <div class="fase-box">
        <div class="fase-label">① Stimulation — Pemantik</div>
        <div class="fase-text">
        <b>Puncak gunung</b> mencapai <b style="color:#C00000">+3.000 meter</b>,
        di atas permukaan laut.
        Kedalaman <b>Palung Jawa</b> adalah <b style="color:#C00000">−7.000 m</b> dari permukaan laut.<br><br>
        <b>❓ Apa arti tanda "−" (negatif) pada bilangan-bilangan tersebut?</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # PROBLEM STATEMENT
    st.markdown("""
    <div class="fase-box" style="border-color:#ED7D31;background:#FFF4EC;">
        <div class="fase-label" style="color:#ED7D31;">② Problem Statement — Rumusan Masalah</div>
        <div class="fase-text">
        Sebelum bereksplorasi, tuliskan dulu hipotesismu di LKS:<br>
        <i>"Menurutku, bilangan bulat negatif adalah... dan letaknya pada garis bilangan ada di..."</i>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # DATA COLLECTION — Garis Bilangan Interaktif
    st.markdown("""
    <div class="fase-box" style="border-color:#70AD47;background:#F0FBF0;">
        <div class="fase-label" style="color:#70AD47;">③ Data Collection — Eksplorasi Garis Bilangan</div>
        <div class="fase-text">Gunakan slider di bawah untuk menempatkan bilangan pada garis bilangan.
        Amati letaknya dan catat temuanmu di LKS!</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        bilangan = st.slider("Pilih Bilangan:", min_value=-20, max_value=20, value=0, step=1)
        st.markdown(f"""
        <div class="result-display" style="font-size:3rem;">
            {bilangan:+d}
        </div>
        """, unsafe_allow_html=True)

        if bilangan > 0:
            st.markdown('<div class="success-card">✅ <b>Bilangan Bulat POSITIF</b><br>Terletak di sebelah <b>KANAN</b> nol pada garis bilangan</div>', unsafe_allow_html=True)
        elif bilangan < 0:
            st.markdown('<div class="danger-card">🔴 <b>Bilangan Bulat NEGATIF</b><br>Terletak di sebelah <b>KIRI</b> nol pada garis bilangan</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-card">⚪ <b>NOL</b><br>Bukan positif, bukan negatif. Titik tengah garis bilangan.</div>', unsafe_allow_html=True)

        inv = -bilangan
        st.markdown(f"""
        <div class="warning-card">
        <b>🔄 Invers Penjumlahan:</b><br>
        Invers dari <b>{bilangan:+d}</b> adalah <b>{inv:+d}</b><br>
        Bukti: <b>{bilangan:+d} + ({inv:+d}) = {bilangan+inv}</b>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Visualisasi garis bilangan
        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.set_xlim(-22, 22)
        ax.set_ylim(-1.5, 2)
        ax.axis("off")
        fig.patch.set_facecolor('#FAFBFF')
        ax.set_facecolor('#FAFBFF')

        # Garis utama
        ax.annotate("", xy=(21.5, 0), xytext=(-21.5, 0),
                    arrowprops=dict(arrowstyle="<->", color="#1A3C6E", lw=2.5))

        # Tick marks dan label
        for i in range(-20, 21):
            tick_h = 0.25 if i % 5 == 0 else 0.15
            col_tick = "#1A3C6E" if i % 5 == 0 else "#AAAAAA"
            ax.plot([i, i], [-tick_h, tick_h], color=col_tick, lw=1.5)
            if i % 5 == 0:
                ax.text(i, -0.55, str(i), ha='center', va='top',
                        fontsize=9, color="#1A3C6E", fontweight='bold')

        # Label negatif/positif
        ax.text(-10, 1.5, "← BILANGAN NEGATIF", ha='center', fontsize=9,
                color="#C00000", fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFEEEE', edgecolor='#C00000', alpha=0.8))
        ax.text(10, 1.5, "BILANGAN POSITIF →", ha='center', fontsize=9,
                color="#70AD47", fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#EEFFEE', edgecolor='#70AD47', alpha=0.8))
        ax.text(0, 1.5, "NOL", ha='center', fontsize=9,
                color="#7F7F7F", fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5F5F5', edgecolor='#7F7F7F', alpha=0.8))

        # Titik yang dipilih
        dot_color = "#C00000" if bilangan < 0 else ("#70AD47" if bilangan > 0 else "#7F7F7F")
        ax.plot(bilangan, 0, 'o', color=dot_color, markersize=18, zorder=5,
                markeredgecolor='white', markeredgewidth=2)
        ax.text(bilangan, 0.7, f"{bilangan:+d}", ha='center', fontsize=12,
                color=dot_color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor=dot_color, lw=2))

        # Garis invers
        if bilangan != 0:
            ax.annotate("", xy=(inv, 0), xytext=(bilangan, 0),
                        arrowprops=dict(arrowstyle="->", color="#ED7D31", lw=1.5,
                                        connectionstyle="arc3,rad=-0.4"))
            mid = (bilangan + inv) / 2
            ax.text(mid, -1.1, f"invers = {inv:+d}", ha='center',
                    fontsize=8.5, color="#ED7D31", fontstyle='italic')

        ax.set_title("Garis Bilangan Interaktif — Kalkulator Digital Streamlit",
                     pad=8, fontsize=10, color="#1A3C6E", fontweight='bold')
        st.pyplot(fig)
        plt.close()

    st.markdown("---")

    # DATA PROCESSING — Tabel
    st.markdown("""
    <div class="fase-box" style="border-color:#7030A0;background:#F5EFFF;">
        <div class="fase-label" style="color:#7030A0;">④ Data Processing — Analisis Pola</div>
        <div class="fase-text">Eksplorasi beberapa bilangan menggunakan slider, lalu lengkapi tabel di LKS-mu:</div>
    </div>
    """, unsafe_allow_html=True)

    contoh_data = [
        ("+8", "Kanan nol", "✅ Positif", "+8 + (−8) = 0", "−8"),
        ("−5", "Kiri nol", "🔴 Negatif", "−5 + (+5) = 0", "+5"),
        ("0", "Titik tengah", "⚪ Nol", "0 + 0 = 0", "0"),
        ("−12", "...", "...", "...", "..."),
        ("+17", "...", "...", "...", "..."),
    ]

    st.markdown("""
    <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
    <tr style="background:#1A3C6E;color:white;">
        <th style="padding:8px;border:1px solid #ccc;">Bilangan</th>
        <th style="padding:8px;border:1px solid #ccc;">Letak pada Garis Bilangan</th>
        <th style="padding:8px;border:1px solid #ccc;">Jenis</th>
        <th style="padding:8px;border:1px solid #ccc;">Pembuktian Invers</th>
        <th style="padding:8px;border:1px solid #ccc;">Invers Penjumlahan</th>
    </tr>
    """ + "".join([f"""
    <tr style="background:{'#F8FAFF' if i % 2 == 0 else 'white'};">
        <td style="padding:8px;border:1px solid #ccc;font-weight:bold;text-align:center;">{r[0]}</td>
        <td style="padding:8px;border:1px solid #ccc;text-align:center;">{r[1]}</td>
        <td style="padding:8px;border:1px solid #ccc;text-align:center;">{r[2]}</td>
        <td style="padding:8px;border:1px solid #ccc;text-align:center;">{r[3]}</td>
        <td style="padding:8px;border:1px solid #ccc;text-align:center;font-weight:bold;color:#1A3C6E;">{r[4]}</td>
    </tr>
    """ for i, r in enumerate(contoh_data)]) + "</table>", unsafe_allow_html=True)

    st.markdown("*(Baris kosong diisi berdasarkan eksplorasimu menggunakan slider)*", unsafe_allow_html=True)

    # GENERALIZATION
    st.markdown("---")
    st.markdown("""
    <div class="fase-box" style="border-color:#1A3C6E;background:#EBF3FB;">
        <div class="fase-label">⑥ Generalization — Simpulan</div>
        <div class="fase-text">Tuliskan simpulanmu di LKS berdasarkan eksplorasimu:</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("💡 Lihat Simpulan (setelah mencoba sendiri dulu!)"):
        st.markdown("""
        <div class="success-card">
        <b>Simpulan Bilangan Bulat:</b><br>
        ✅ Bilangan bulat terdiri dari: <b>bilangan negatif (...,−3,−2,−1), nol (0), bilangan positif (1,2,3,...)</b><br>
        ✅ Semakin ke <b>kanan</b> pada garis bilangan → nilainya semakin <b>besar</b><br>
        ✅ Semakin ke <b>kiri</b> pada garis bilangan → nilainya semakin <b>kecil</b><br>
        ✅ <b>Invers penjumlahan</b> dari a adalah −a, karena a + (−a) = 0
        </div>
        """, unsafe_allow_html=True)

    blok_selesai("kp1")


# ══════════════════════════════════════════
# KP 2 — KALKULATOR OPERASI
# ══════════════════════════════════════════
elif tab_choice == "kp2":
    st.markdown("## 🔧 Kegiatan Pembelajaran 2: Operasi Hitung Bilangan Bulat")

    # STIMULATION
    st.markdown("""
    <div class="fase-box">
        <div class="fase-label">① Stimulation — Pemantik</div>
        <div class="fase-text">
        Sebuah klub sepak bola <b>melepaskan 3 pemain buruk</b>. Artinya: <b>(−3) × (−1) = ?</b><br>
        Apakah performa tim naik atau turun? Mengapa <b>(−3) × (−4) = +12</b>, bukan −12?<br><br>
        <b>❓ Apa yang menentukan tanda hasil perkalian dan pembagian bilangan bulat?</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # PROBLEM STATEMENT
    st.markdown("""
    <div class="fase-box" style="border-color:#ED7D31;background:#FFF4EC;">
        <div class="fase-label" style="color:#ED7D31;">② Problem Statement — Hipotesis</div>
        <div class="fase-text">
        Tuliskan hipotesismu di LKS sebelum bereksplorasi:<br>
        <i>"Menurutku, hasil perkalian dua bilangan negatif akan bernilai... karena..."</i>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div class="fase-box" style="border-color:#70AD47;background:#F0FBF0;">
        <div class="fase-label" style="color:#70AD47;">③ Data Collection — Eksplorasi Kalkulator</div>
        <div class="fase-text">Masukkan dua bilangan dan pilih operasi. Catat hasilnya di tabel LKS!</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### ⌨️ Masukkan Bilangan")
        a = st.number_input("Bilangan Pertama (a):", value=-6, step=1, min_value=-999, max_value=999)
        op = st.selectbox("Operasi:", ["+  (Penjumlahan)", "−  (Pengurangan)", "×  (Perkalian)", "÷  (Pembagian)"])
        b = st.number_input("Bilangan Kedua (b):", value=-4, step=1, min_value=-999, max_value=999)

        op_sym = op[0]
        if op_sym == "+":
            hasil = a + b
        elif op_sym == "−":
            hasil = a - b
        elif op_sym == "×":
            hasil = a * b
        else:
            if b == 0:
                st.error("⚠️ Tidak bisa membagi dengan nol!")
                hasil = None
            else:
                hasil = a // b if a % b == 0 else a / b

    with col2:
        if hasil is not None:
            tanda = "➕ POSITIF" if hasil > 0 else ("➖ NEGATIF" if hasil < 0 else "⚪ NOL")
            warna = "#70AD47" if hasil > 0 else ("#C00000" if hasil < 0 else "#7F7F7F")
            hasil_teks = hasil if isinstance(hasil, int) else f"{hasil:.4f}"
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1A3C6E,#2E75B6);color:white;
                        border-radius:16px;padding:1.5rem;text-align:center;margin-top:1.5rem;
                        box-shadow:0 4px 15px rgba(26,60,110,0.3);">
                <div style="font-size:0.85rem;opacity:0.8;margin-bottom:0.3rem;">Kalimat Matematika</div>
                <div style="font-size:1.5rem;font-weight:800;margin-bottom:0.5rem;">
                    ({a:+d}) {op_sym} ({b:+d})
                </div>
                <div style="font-size:0.85rem;opacity:0.8;">Hasil</div>
                <div style="font-size:3.5rem;font-weight:800;line-height:1.1;">
                    {hasil_teks}
                </div>
                <div style="margin-top:0.5rem;background:{warna};color:white;
                            padding:5px 15px;border-radius:20px;display:inline-block;font-weight:700;">
                    {tanda}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Penjelasan tanda
            if op_sym in ["×", "÷"]:
                ta = "positif" if a > 0 else ("negatif" if a < 0 else "nol")
                tb = "positif" if b > 0 else ("negatif" if b < 0 else "nol")
                sama = "YA → hasil POSITIF ✅" if (a > 0 and b > 0) or (a < 0 and b < 0) else "TIDAK → hasil NEGATIF 🔴"
                st.markdown(f"""
                <div class="warning-card" style="margin-top:0.8rem;">
                <b>🔍 Analisis Tanda:</b><br>
                a = {a:+d} → <b>{ta}</b><br>
                b = {b:+d} → <b>{tb}</b><br>
                Tanda sama? <b>{sama}</b>
                </div>
                """, unsafe_allow_html=True)

    # Tabel Eksplorasi Sistematis
    st.markdown("---")
    st.markdown("""
    <div class="fase-box" style="border-color:#7030A0;background:#F5EFFF;">
        <div class="fase-label" style="color:#7030A0;">④ Data Processing — Tabel Pola Tanda</div>
        <div class="fase-text">Coba semua kombinasi berikut menggunakan kalkulator di atas, lalu catat di LKS!</div>
    </div>
    """, unsafe_allow_html=True)

    cols3 = st.columns(2)
    with cols3[0]:
        st.markdown("**Pola Perkalian (×)**")
        pola_kali = [
            ("(+6) × (+4)", 6 * 4, "+", "+"),
            ("(+6) × (−4)", 6 * (-4), "+", "−"),
            ("(−6) × (+4)", (-6) * 4, "−", "+"),
            ("(−6) × (−4)", (-6) * (-4), "−", "−"),
        ]
        tbl = '<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'
        tbl += '<tr style="background:#1A3C6E;color:white;"><th style="padding:6px;border:1px solid #ccc;">Operasi</th><th style="padding:6px;border:1px solid #ccc;">Hasil</th><th style="padding:6px;border:1px solid #ccc;">Tanda Hasil</th></tr>'
        for op_str, res, ta, tb in pola_kali:
            t_res = "POSITIF ✅" if res > 0 else "NEGATIF 🔴"
            c_res = "#70AD47" if res > 0 else "#C00000"
            tbl += f'<tr><td style="padding:6px;border:1px solid #ccc;">{op_str}</td><td style="padding:6px;border:1px solid #ccc;text-align:center;font-weight:bold;">{res}</td><td style="padding:6px;border:1px solid #ccc;text-align:center;color:{c_res};font-weight:bold;">{t_res}</td></tr>'
        tbl += "</table>"
        st.markdown(tbl, unsafe_allow_html=True)

    with cols3[1]:
        st.markdown("**Pola Pembagian (÷)**")
        pola_bagi = [
            ("(+24) ÷ (+6)", 24 // 6, "+", "+"),
            ("(+24) ÷ (−6)", 24 // (-6), "+", "−"),
            ("(−24) ÷ (+6)", (-24) // 6, "−", "+"),
            ("(−24) ÷ (−6)", (-24) // (-6), "−", "−"),
        ]
        tbl2 = '<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'
        tbl2 += '<tr style="background:#1A3C6E;color:white;"><th style="padding:6px;border:1px solid #ccc;">Operasi</th><th style="padding:6px;border:1px solid #ccc;">Hasil</th><th style="padding:6px;border:1px solid #ccc;">Tanda Hasil</th></tr>'
        for op_str, res, ta, tb in pola_bagi:
            t_res = "POSITIF ✅" if res > 0 else "NEGATIF 🔴"
            c_res = "#70AD47" if res > 0 else "#C00000"
            tbl2 += f'<tr><td style="padding:6px;border:1px solid #ccc;">{op_str}</td><td style="padding:6px;border:1px solid #ccc;text-align:center;font-weight:bold;">{res}</td><td style="padding:6px;border:1px solid #ccc;text-align:center;color:{c_res};font-weight:bold;">{t_res}</td></tr>'
        tbl2 += "</table>"
        st.markdown(tbl2, unsafe_allow_html=True)

    # GENERALIZATION
    st.markdown("---")
    with st.expander("⑥ 💡 Lihat Simpulan Aturan Tanda (setelah mencoba sendiri dulu!)"):
        st.markdown("""
        <table style="width:100%;border-collapse:collapse;font-size:0.9rem;text-align:center;">
        <tr style="background:#1A3C6E;color:white;">
            <th style="padding:10px;border:1px solid #ccc;">Tanda a</th>
            <th style="padding:10px;border:1px solid #ccc;">Operasi</th>
            <th style="padding:10px;border:1px solid #ccc;">Tanda b</th>
            <th style="padding:10px;border:1px solid #ccc;">Tanda Hasil</th>
        </tr>
        <tr style="background:#EEFFEE;"><td>+</td><td>× atau ÷</td><td>+</td><td style="color:#70AD47;font-weight:bold;">POSITIF (+)</td></tr>
        <tr><td>−</td><td>× atau ÷</td><td>−</td><td style="color:#70AD47;font-weight:bold;">POSITIF (+)</td></tr>
        <tr style="background:#FFEEEE;"><td>+</td><td>× atau ÷</td><td>−</td><td style="color:#C00000;font-weight:bold;">NEGATIF (−)</td></tr>
        <tr style="background:#FFEEEE;"><td>−</td><td>× atau ÷</td><td>+</td><td style="color:#C00000;font-weight:bold;">NEGATIF (−)</td></tr>
        </table>
        <br>
        <div class="success-card">
        <b>✅ Aturan Emas:</b><br>
        🟢 <b>Tanda SAMA</b> (++ atau −−) → hasil <b>POSITIF</b><br>
        🔴 <b>Tanda BERBEDA</b> (+− atau −+) → hasil <b>NEGATIF</b>
        </div>
        """, unsafe_allow_html=True)

    blok_selesai("kp2")


# ══════════════════════════════════════════
# KP 3 — POHON FAKTOR & FPB/KPK
# ══════════════════════════════════════════
elif tab_choice == "kp3":
    st.markdown("## 🌳 Kegiatan Pembelajaran 3: Faktor Bilangan Bulat")

    st.markdown("""
    <div class="fase-box">
        <div class="fase-label">① Stimulation — Pemantik</div>
        <div class="fase-text">
        Ibu memiliki <b>24 kue nastar</b> dan <b>36 kue coklat</b>. Ia ingin membagi ke beberapa piring
        dengan jumlah <b>sama rata dan tidak ada sisa</b>.<br><br>
        <b>❓ Berapa paling banyak piring yang bisa digunakan? Berapa kue di setiap piring?</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    tab3a, tab3b = st.tabs(["🌳 Pohon Faktor", "📊 FPB & KPK"])

    # ── TAB POHON FAKTOR
    with tab3a:
        st.markdown("""
        <div class="fase-box" style="border-color:#70AD47;background:#F0FBF0;">
            <div class="fase-label" style="color:#70AD47;">③ Data Collection — Eksplorasi Pohon Faktor</div>
            <div class="fase-text">Masukkan bilangan, amati pohon faktor yang terbentuk, dan catat di LKS!</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])
        with col1:
            n = st.number_input("Masukkan bilangan (2–200):", min_value=2, max_value=200, value=36, step=1)

            fp = faktorisasi_prima(n)
            faktor_prima_str_clean = " × ".join([f"{p}" + (f"^{e}" if e > 1 else "") for p, e in fp.items()])
            semua_f = semua_faktor(n)
            is_prima = len(semua_f) == 2
            teks_prima = "✅ YA" if is_prima else "❌ BUKAN"
            daftar_faktor = ", ".join(map(str, semua_f))

            st.markdown(f"""
            <div style="background:#1A3C6E;color:white;border-radius:12px;padding:1rem;text-align:center;margin:0.5rem 0;">
                <div style="font-size:0.8rem;opacity:0.8;">Faktorisasi Prima</div>
                <div style="font-size:1.6rem;font-weight:800;margin:0.3rem 0;">{n} = {faktor_prima_str_clean}</div>
                <div style="font-size:0.8rem;opacity:0.8;">Bilangan Prima? {teks_prima}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="info-card">
            <b>Semua Faktor dari {n}:</b><br>
            <span style="font-size:0.9rem;">{{{daftar_faktor}}}</span><br>
            <b>Banyak faktor:</b> {len(semua_f)}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Visualisasi Pohon Faktor
            def get_pohon_nodes(n_asli, n, x=0, y=0, dx=1.5, level=0, nodes=None, edges=None):
                if nodes is None:
                    nodes = []
                if edges is None:
                    edges = []
                node_id = len(nodes)
                is_p = faktorisasi_prima(n) == {n: 1} or n == 1
                nodes.append((node_id, x, y, str(n), is_p, level == 0))
                if is_p or n == 1:
                    return nodes, edges
                d = 2
                while d < n:
                    if n % d == 0:
                        other = n // d
                        # child 1: d
                        cid1 = len(nodes)
                        nodes, edges = get_pohon_nodes(n, d, x - dx / (level + 1), y - 1.2,
                                                       dx * 0.6, level + 1, nodes, edges)
                        edges.append((node_id, cid1))
                        # child 2: other
                        cid2 = len(nodes)
                        nodes, edges = get_pohon_nodes(n, other, x + dx / (level + 1), y - 1.2,
                                                       dx * 0.6, level + 1, nodes, edges)
                        edges.append((node_id, cid2))
                        break
                    d += 1
                return nodes, edges

            nodes_list, edges_list = get_pohon_nodes(n, n)

            fig2, ax2 = plt.subplots(figsize=(8, 5))
            ax2.axis("off")
            fig2.patch.set_facecolor('#FAFBFF')
            ax2.set_facecolor('#FAFBFF')

            for nid1, nid2 in edges_list:
                x1, y1 = nodes_list[nid1][1], nodes_list[nid1][2]
                x2, y2 = nodes_list[nid2][1], nodes_list[nid2][2]
                ax2.plot([x1, x2], [y1, y2], '-', color='#AAAAAA', lw=1.5, zorder=1)

            for nid, x, y, label, is_p, is_root in nodes_list:
                color = "#1A3C6E" if is_root else ("#70AD47" if is_p else "#2E75B6")
                size = 600 if is_root else 400
                ax2.scatter([x], [y], s=size, c=color, zorder=3, edgecolors='white', linewidths=2)
                ax2.text(x, y, label, ha='center', va='center', fontsize=10 if is_root else 9,
                         color='white', fontweight='bold', zorder=4)
                if is_p and not is_root:
                    ax2.text(x, y - 0.5, "prima", ha='center', va='top', fontsize=7,
                             color="#70AD47", fontstyle='italic')

            ax2.set_title(f"Pohon Faktor dari {n}   =   {faktor_prima_str_clean}",
                          pad=10, fontsize=10, color="#1A3C6E", fontweight='bold')

            legend_els = [
                mpatches.Patch(facecolor='#1A3C6E', label='Bilangan asal'),
                mpatches.Patch(facecolor='#70AD47', label='Faktor prima'),
                mpatches.Patch(facecolor='#2E75B6', label='Faktor komposit'),
            ]
            ax2.legend(handles=legend_els, loc='lower right', fontsize=8)
            st.pyplot(fig2)
            plt.close()

    # ── TAB FPB & KPK
    with tab3b:
        st.markdown("""
        <div class="fase-box" style="border-color:#70AD47;background:#F0FBF0;">
            <div class="fase-label" style="color:#70AD47;">③ Data Collection — Eksplorasi FPB & KPK</div>
            <div class="fase-text">Masukkan dua bilangan, amati proses faktorisasi prima, dan catat pola FPB & KPK di LKS!</div>
        </div>
        """, unsafe_allow_html=True)

        cola, colb = st.columns(2)
        with cola:
            bil1 = st.number_input("Bilangan Pertama:", min_value=2, max_value=200, value=24, step=1)
        with colb:
            bil2 = st.number_input("Bilangan Kedua:", min_value=2, max_value=200, value=36, step=1)

        fp1 = faktorisasi_prima(bil1)
        fp2 = faktorisasi_prima(bil2)
        semua_p = sorted(set(list(fp1.keys()) + list(fp2.keys())))

        # FPB & KPK
        fpb = 1
        kpk = 1
        for p in semua_p:
            e1 = fp1.get(p, 0)
            e2 = fp2.get(p, 0)
            fpb *= p ** min(e1, e2)
            kpk *= p ** max(e1, e2)

        col1, col2, col3 = st.columns([1.2, 1, 1])
        with col1:
            fp1_str = " × ".join([f"{p}" + (f"^{e}" if e > 1 else "") for p, e in fp1.items()])
            fp2_str = " × ".join([f"{p}" + (f"^{e}" if e > 1 else "") for p, e in fp2.items()])
            st.markdown(f"""
            <div class="info-card">
            <b>Faktorisasi Prima:</b><br><br>
            <span style="color:#1A3C6E;font-size:1rem;font-weight:700;">{bil1}</span>
            = {fp1_str}<br>
            <span style="color:#1A3C6E;font-size:1rem;font-weight:700;">{bil2}</span>
            = {fp2_str}
            </div>
            """, unsafe_allow_html=True)

            # Tabel perbandingan
            tbl = '<table style="width:100%;border-collapse:collapse;font-size:0.82rem;margin-top:0.5rem;">'
            tbl += f'<tr style="background:#1A3C6E;color:white;"><th style="padding:6px;border:1px solid #ccc;">Prima</th><th style="padding:6px;border:1px solid #ccc;">Pangkat di {bil1}</th><th style="padding:6px;border:1px solid #ccc;">Pangkat di {bil2}</th><th style="padding:6px;border:1px solid #ccc;">min (FPB)</th><th style="padding:6px;border:1px solid #ccc;">max (KPK)</th></tr>'
            for p in semua_p:
                e1 = fp1.get(p, 0)
                e2 = fp2.get(p, 0)
                tbl += f'<tr style="text-align:center;"><td style="padding:5px;border:1px solid #ccc;font-weight:bold;">{p}</td><td style="padding:5px;border:1px solid #ccc;">{e1 if e1 > 0 else "—"}</td><td style="padding:5px;border:1px solid #ccc;">{e2 if e2 > 0 else "—"}</td><td style="padding:5px;border:1px solid #ccc;color:#C00000;font-weight:bold;">{min(e1, e2) if min(e1, e2) > 0 else "—"}</td><td style="padding:5px;border:1px solid #ccc;color:#70AD47;font-weight:bold;">{max(e1, e2)}</td></tr>'
            tbl += "</table>"
            st.markdown(tbl, unsafe_allow_html=True)

        with col2:
            fpb_str = " × ".join([f"{p}" + (f"^{min(fp1.get(p, 0), fp2.get(p, 0))}" if min(fp1.get(p, 0), fp2.get(p, 0)) > 1 else "") for p in semua_p if min(fp1.get(p, 0), fp2.get(p, 0)) > 0])
            if not fpb_str:
                fpb_str = "1"
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#C00000,#E74C3C);color:white;
                        border-radius:14px;padding:1.2rem;text-align:center;">
                <div style="font-size:0.8rem;opacity:0.9;margin-bottom:0.3rem;">FPB({bil1}, {bil2})</div>
                <div style="font-size:0.75rem;opacity:0.8;">= {fpb_str}</div>
                <div style="font-size:3rem;font-weight:800;">{fpb}</div>
                <div style="font-size:0.8rem;opacity:0.8;margin-top:0.3rem;">
                Faktor prima SAMA, pangkat TERKECIL</div>
            </div>
            <div class="danger-card" style="margin-top:0.6rem;font-size:0.85rem;">
            <b>Artinya:</b> {bil1} dan {bil2} sama-sama bisa dibagi {fpb}.<br>
            Dalam soal kue: bisa dibagi ke <b>{fpb} piring</b>!
            </div>
            """, unsafe_allow_html=True)

        with col3:
            kpk_str = " × ".join([f"{p}" + (f"^{max(fp1.get(p, 0), fp2.get(p, 0))}" if max(fp1.get(p, 0), fp2.get(p, 0)) > 1 else "") for p in semua_p if max(fp1.get(p, 0), fp2.get(p, 0)) > 0])
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#70AD47,#27AE60);color:white;
                        border-radius:14px;padding:1.2rem;text-align:center;">
                <div style="font-size:0.8rem;opacity:0.9;margin-bottom:0.3rem;">KPK({bil1}, {bil2})</div>
                <div style="font-size:0.75rem;opacity:0.8;">= {kpk_str}</div>
                <div style="font-size:3rem;font-weight:800;">{kpk}</div>
                <div style="font-size:0.8rem;opacity:0.8;margin-top:0.3rem;">
                SEMUA faktor prima, pangkat TERBESAR</div>
            </div>
            <div class="success-card" style="margin-top:0.6rem;font-size:0.85rem;">
            <b>Artinya:</b> Kelipatan terkecil yang habis dibagi {bil1} dan {bil2} sekaligus.<br>
            Dalam soal lampu: lampu berkedip bersamaan tiap <b>{kpk} satuan waktu</b>!
            </div>
            """, unsafe_allow_html=True)

        with st.expander("⑥ 💡 Lihat Simpulan FPB & KPK"):
            st.markdown("""
            <div class="success-card">
            <b>✅ Cara Menentukan FPB dan KPK dengan Faktorisasi Prima:</b><br><br>
            🔴 <b>FPB</b> = kalikan faktor prima yang <b>SAMA</b> dengan pangkat <b>TERKECIL</b><br>
            🟢 <b>KPK</b> = kalikan <b>SEMUA</b> faktor prima dengan pangkat <b>TERBESAR</b><br><br>
            💡 <b>Mudah diingat:</b><br>
            FPB → irisan (sama-sama ada) → pangkat kecil<br>
            KPK → gabungan (semua diambil) → pangkat besar
            </div>
            """, unsafe_allow_html=True)

    blok_selesai("kp3")


# ══════════════════════════════════════════
# SOAL LATIHAN INTERAKTIF
# ══════════════════════════════════════════
elif tab_choice == "latihan":
    st.markdown("## 📝 Soal Latihan Interaktif")
    st.markdown("""
    <div class="warning-card">
    <b>📌 Petunjuk:</b> Kerjakan soal-soal berikut secara mandiri dan jujur.
    Gunakan kalkulator digital di tab sebelumnya hanya untuk <b>verifikasi</b>, bukan langsung menekan tombol!
    Waktu pengerjaan: ±45 menit.<br>
    Untuk soal isian dengan beberapa bilangan, pisahkan dengan koma (contoh: −10, −7, −3, ...).
    </div>
    """, unsafe_allow_html=True)

    if is_guru():
        st.info("👩‍🏫 Mode pratinjau guru: jawaban tidak dicatat. Kunci jawaban ditampilkan di bawah tiap soal.")

    hasil_latihan = st.session_state.get("hasil_latihan")
    sudah_submit = hasil_latihan is not None
    detail_map = {d["no"]: d for d in hasil_latihan["detail"]} if sudah_submit else {}

    for soal in SOAL_LIST:
        kp_color = {"KP 1": "#2E75B6", "KP 2": "#70AD47", "KP 3": "#ED7D31"}[soal["kp"]]
        konteks_html = ""
        if soal["konteks"]:
            konteks_html = (f'<div style="background:#FFF8E6;padding:0.5rem 0.8rem;border-radius:8px;'
                            f'margin-top:0.4rem;font-size:0.88rem;color:#8B6914;">{soal["konteks"]}</div>')
        st.markdown(f"""
        <div style="border:1px solid #E0E0E0;border-radius:12px;padding:1rem 1.2rem;margin:0.8rem 0;
                    border-left:5px solid {kp_color};">
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
            <span style="background:{kp_color};color:white;padding:2px 10px;border-radius:20px;
                         font-size:0.78rem;font-weight:700;">{soal['kp']}</span>
            <span style="background:#F0F0F0;padding:2px 10px;border-radius:20px;
                         font-size:0.78rem;font-weight:700;">{soal['tipe']}</span>
            <b>Soal {soal['no']}</b>
        </div>
        <div style="font-size:0.95rem;font-weight:600;">{soal['soal']}</div>
        {konteks_html}
        </div>
        """, unsafe_allow_html=True)

        key = f"soal_{soal['no']}"
        if soal["tipe"] == "PG":
            st.radio("Pilih jawaban:", soal["pilihan"], index=None, key=key,
                     label_visibility="collapsed", disabled=sudah_submit)
        else:
            st.text_input("Jawaban kamu:", key=key, placeholder="Tulis jawabanmu di sini...",
                          disabled=sudah_submit)

        if is_guru():
            st.caption(f"🔑 Kunci: {soal['jawaban']} — {soal['pembahasan']}")

        if sudah_submit:
            if detail_map[soal["no"]]["benar"]:
                st.markdown(f'<div class="success-card" style="font-size:0.85rem;">✅ <b>BENAR!</b> {soal["pembahasan"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="danger-card" style="font-size:0.85rem;">❌ <b>Belum tepat.</b> Jawaban: <b>{soal["jawaban"]}</b>. {soal["pembahasan"]}</div>', unsafe_allow_html=True)

        st.markdown("")

    if not is_guru():
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            st.button("✅ Submit & Lihat Nilai", type="primary", use_container_width=True,
                      on_click=kirim_latihan, disabled=sudah_submit)
        with col_btn2:
            st.button("🔄 Ulangi Latihan", use_container_width=True, on_click=ulangi_latihan)

    if sudah_submit:
        skor_total = hasil_latihan["skor"]
        persen = skor_total / len(SOAL_LIST) * 100
        emoji = "🏆" if persen >= 80 else ("👍" if persen >= 60 else "💪")
        warna_nilai = "#70AD47" if persen >= 80 else ("#ED7D31" if persen >= 60 else "#C00000")
        if persen >= 80:
            pesan = "🏆 Excellent! Kamu sudah sangat memahami bilangan bulat!"
        elif persen >= 60:
            pesan = "👍 Bagus! Pelajari lagi bagian yang masih salah."
        else:
            pesan = "💪 Semangat! Eksplorasi lebih dalam dengan kalkulator digital!"
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1A3C6E,#2E75B6);color:white;
                    border-radius:16px;padding:1.5rem 2rem;text-align:center;margin-top:1rem;">
            <div style="font-size:1.1rem;opacity:0.9;">Nilai Akhir {emoji}</div>
            <div style="font-size:4rem;font-weight:800;color:{warna_nilai};">{persen:.0f}</div>
            <div style="font-size:1rem;opacity:0.8;">{skor_total} dari {len(SOAL_LIST)} soal benar</div>
            <div style="margin-top:0.8rem;font-size:0.9rem;">{pesan}</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Nilaimu sudah tersimpan dan dapat dilihat guru. Klik 'Ulangi Latihan' untuk mencoba lagi.")

        # REFLEKSI
        st.markdown("---")
        st.markdown("### 🔍 Refleksi Penggunaan Kalkulator Digital Streamlit")
        r1 = st.text_area("1. Fitur apa yang paling membantumu memahami bilangan bulat? Mengapa?",
                          placeholder="Tuliskan refleksimu di sini...", height=80, key="r1")
        r2 = st.text_area("2. Apa yang kamu temukan saat bereksplorasi dengan kalkulator digital yang tidak kamu temukan dari buku?",
                          placeholder="Tuliskan refleksimu di sini...", height=80, key="r2")
        r3 = st.text_area("3. Bagaimana perasaanmu belajar matematika dengan kalkulator digital ini?",
                          placeholder="Tuliskan refleksimu di sini...", height=80, key="r3")
        if st.button("💾 Simpan Refleksi", type="primary"):
            if r1.strip() or r2.strip() or r3.strip():
                q("INSERT INTO refleksi(siswa_id,waktu,r1,r2,r3) VALUES(?,?,?,?,?)",
                  (SID, sekarang().strftime("%Y-%m-%d %H:%M"), r1, r2, r3), commit=True)
                st.markdown('<div class="success-card">✅ Terima kasih atas refleksimu! Refleksi tersimpan dan dapat dilihat guru. Salin juga ke LKS-mu.</div>', unsafe_allow_html=True)
            else:
                st.warning("Isi minimal satu refleksi dulu ya.")


# ══════════════════════════════════════════
# VIDEO BAHAN/MATERI
# ══════════════════════════════════════════
elif tab_choice == "video":
    st.markdown("## 🎬 Video Bahan/Materi")

    st.markdown("""
    <div class="info-card">
    <b>📺 Panduan Menonton Video</b><br><br>
    Sebelum atau sesudah bereksplorasi dengan kalkulator digital, tonton video berikut untuk
    memperkuat pemahamanmu tentang <b>Bilangan Bulat</b>. Catat poin-poin penting yang kamu
    temukan dari video ke dalam LKS-mu!
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    <div class="fase-box" style="border-color:#ED7D31;background:#FFF4EC;">
        <div class="fase-label" style="color:#ED7D31;">🎥 Video Pembelajaran — Bilangan Bulat</div>
        <div class="fase-text">
        Simak video berikut dengan seksama. Perhatikan penjelasan konsep, contoh soal,
        dan cara penyelesaiannya. Gunakan sebagai referensi pendukung kegiatan Discovery Learning!
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.video("https://youtu.be/cQAwIhfC6Dg")

    st.markdown("---")

    st.markdown("""
    <div class="warning-card">
    <b>📝 Tugas Setelah Menonton</b><br><br>
    Setelah menonton video, jawablah pertanyaan berikut di LKS-mu:<br><br>
    1. Apa konsep utama yang dijelaskan dalam video tersebut?<br>
    2. Adakah cara atau trik baru yang kamu pelajari dari video? Jelaskan!<br>
    3. Bagian mana yang menurutmu paling sulit dipahami? Diskusikan dengan kelompokmu.
    </div>
    """, unsafe_allow_html=True)

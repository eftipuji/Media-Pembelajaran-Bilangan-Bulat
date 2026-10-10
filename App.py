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
    page_title="Bilangan Bulat — Matematika Kelas VII",
    page_icon="➕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# KONSTANTA
# ─────────────────────────────────────────
WIB = ZoneInfo("Asia/Jakarta")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_belajar.db")

# Warna dipakai konsisten di seluruh aplikasi
C_UTAMA = "#1A3C6E"
C_TEKS = "#1F2933"
C_REDUP = "#7F7F7F"
C_POS = "#70AD47"
C_NEG = "#C00000"
C_CATATAN = "#ED7D31"

URUTAN = ["kp1", "kp2", "kp3", "latihan"]

NAMA_HALAMAN = {
    "dashboard": "📊 Dashboard Guru",
    "beranda": "🏠 Beranda",
    "kp1": "📍 KP 1 · Garis Bilangan",
    "kp2": "🔧 KP 2 · Operasi Hitung",
    "kp3": "🌳 KP 3 · Faktor, FPB, dan KPK",
    "latihan": "📝 Latihan Soal",
    "video": "🎬 Video Materi",
}

LENCANA = [
    (3, "Mulai rutin · 3 hari"),
    (7, "Konsisten · 7 hari"),
    (14, "Tekun · 14 hari"),
    (30, "Luar biasa · 30 hari"),
]

# Satu soal singkat di akhir tiap KP. Lulus → materi berikutnya terbuka.
CEK = {
    "kp1": {
        "soal": "Urutan bilangan yang benar dari **terkecil ke terbesar** adalah ...",
        "pilihan": ["−2, −5, 0, 3", "−5, −2, 0, 3", "3, 0, −2, −5", "0, −2, −5, 3"],
        "jawaban": 1,
        "petunjuk": "Semakin ke kiri pada garis bilangan, nilainya semakin kecil.",
    },
    "kp2": {
        "soal": "Hasil dari (−7) × (−6) adalah ...",
        "pilihan": ["−42", "42", "−13", "13"],
        "jawaban": 1,
        "petunjuk": "Dua bilangan bertanda sama (sama-sama negatif) menghasilkan bilangan positif.",
    },
    "kp3": {
        "soal": "FPB dari 12 dan 18 adalah ...",
        "pilihan": ["3", "6", "36", "2"],
        "jawaban": 1,
        "petunjuk": "12 = 2² × 3 dan 18 = 2 × 3². Ambil faktor yang sama dengan pangkat terkecil.",
    },
}

SOAL_LIST = [
    {
        "no": 1, "tipe": "PG", "kp": "KP 1",
        "soal": "Bilangan mana yang memiliki nilai lebih besar?",
        "konteks": "Suhu kota A = −8°C dan suhu kota B = −3°C.",
        "pilihan": ["A. −8 karena angkanya lebih besar", "B. −3 karena letaknya lebih ke kanan pada garis bilangan",
                    "C. Keduanya sama", "D. −8 karena berarti lebih dingin"],
        "jawaban": "B", "pembahasan": "Pada garis bilangan, −3 terletak lebih ke kanan daripada −8. Semakin ke kanan, nilainya semakin besar. Jadi −3 > −8."
    },
    {
        "no": 2, "tipe": "PG", "kp": "KP 1",
        "soal": "Invers penjumlahan dari −17 adalah ...",
        "konteks": "",
        "pilihan": ["A. 17", "B. −17", "C. 1/17", "D. 0"],
        "jawaban": "A", "pembahasan": "Invers penjumlahan dari −17 adalah +17, karena (−17) + 17 = 0."
    },
    {
        "no": 3, "tipe": "PG", "kp": "KP 2",
        "soal": "Hasil dari (−8) × (−5) + (−4) × 3 adalah ...",
        "konteks": "",
        "pilihan": ["A. −52", "B. 28", "C. 52", "D. −28"],
        "jawaban": "B", "pembahasan": "(−8) × (−5) = 40 karena tandanya sama. (−4) × 3 = −12 karena tandanya berbeda. Lalu 40 + (−12) = 28."
    },
    {
        "no": 4, "tipe": "PG", "kp": "KP 2",
        "soal": "Suhu awal gudang beku adalah −15°C. Suhu turun lagi 8°C, lalu naik 5°C. Suhu akhir gudang adalah ...",
        "konteks": "",
        "pilihan": ["A. −18°C", "B. −28°C", "C. 18°C", "D. 28°C"],
        "jawaban": "A", "pembahasan": "−15 + (−8) + 5 = −23 + 5 = −18°C."
    },
    {
        "no": 5, "tipe": "PG", "kp": "KP 3",
        "soal": "Faktorisasi prima dari 72 adalah ...",
        "konteks": "",
        "pilihan": ["A. 2² × 3²", "B. 2³ × 3²", "C. 2² × 3³", "D. 2⁴ × 3"],
        "jawaban": "B", "pembahasan": "72 = 2 × 2 × 2 × 3 × 3 = 2³ × 3²."
    },
    {
        "no": 6, "tipe": "PG", "kp": "KP 3",
        "soal": "FPB dari 48 dan 60 adalah ...",
        "konteks": "",
        "pilihan": ["A. 6", "B. 12", "C. 24", "D. 240"],
        "jawaban": "B", "pembahasan": "48 = 2⁴ × 3 dan 60 = 2² × 3 × 5. FPB diambil dari faktor prima yang sama dengan pangkat terkecil: 2² × 3 = 12."
    },
    {
        "no": 7, "tipe": "Isian", "kp": "KP 2",
        "soal": "Urutkan bilangan berikut dari yang terkecil ke terbesar:",
        "konteks": "Bilangan: −10, 5, −3, 0, 8, −7, 4",
        "pilihan": None,
        "jawaban": "−10, −7, −3, 0, 4, 5, 8",
        "pembahasan": "Dari kiri ke kanan pada garis bilangan: −10 < −7 < −3 < 0 < 4 < 5 < 8."
    },
    {
        "no": 8, "tipe": "Isian", "kp": "KP 3",
        "soal": "KPK dari 8, 12, dan 15 adalah ...",
        "konteks": "Petunjuk: pohon faktor di KP 3 bisa membantumu.",
        "pilihan": None,
        "jawaban": "120",
        "pembahasan": "8 = 2³, 12 = 2² × 3, 15 = 3 × 5. KPK = 2³ × 3 × 5 = 120."
    },
]

# ─────────────────────────────────────────
# CSS — sederhana, datar, satu warna utama
# ─────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

    html, body, [class*="css"], .stMarkdown, .stButton button, input, textarea, label {
        font-family: 'Nunito', sans-serif;
    }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .block-container { padding-top: 2rem; max-width: 1100px; }

    /* Banner judul */
    .judul-app {
        background: linear-gradient(135deg, #1A3C6E 0%, #2E75B6 60%, #70AD47 100%);
        color: white; padding: 1.4rem 2rem; border-radius: 16px;
        text-align: center; margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(26,60,110,0.3);
    }
    .judul-app .atas { font-size: .8rem; opacity: .85; letter-spacing: .08em; text-transform: uppercase; }
    .judul-app h1 { font-size: 2rem; font-weight: 800; margin: .1rem 0; padding: 0; color: white; }
    .judul-app p { margin: .2rem 0 0; opacity: .92; font-size: 1rem; color: white; }

    /* Langkah belajar (warna diatur per langkah) */
    .langkah { padding: .75rem 1rem; border-radius: 0 10px 10px 0; margin: .8rem 0; border-left: 5px solid; }
    .langkah-judul { font-weight: 800; font-size: .85rem; text-transform: uppercase; letter-spacing: .5px; }
    .langkah-judul .istilah { font-weight: 600; opacity: .7; font-size: .72rem; margin-left: .6rem;
                              text-transform: none; letter-spacing: 0; }
    .langkah-isi { color: #2C3E50; font-size: .95rem; margin-top: .3rem; line-height: 1.65; }

    /* Kotak informasi */
    .kotak {
        background: #F0F7FF; border: 1px solid #BDD7EE; border-radius: 12px;
        padding: 1rem 1.2rem; margin: .5rem 0; color: #2C3E50; font-size: .92rem; line-height: 1.6;
    }
    .kotak.catatan { background: #FFF8E6; border-color: #FFD966; }
    .kotak.benar   { background: #F0FBF0; border-color: #70AD47; }
    .kotak.salah   { background: #FEF0F0; border-color: #E74C3C; }
    .kotak.streak  { background: linear-gradient(135deg, #FFF3E0, #FFE0B2); border-color: #FFB74D; color: #5D4037; }

    /* Kartu angka / hasil */
    .angka {
        background: linear-gradient(135deg, #1A3C6E, #2E75B6); color: white;
        border-radius: 16px; padding: 1.1rem; text-align: center; margin: .5rem 0;
        box-shadow: 0 4px 15px rgba(26,60,110,0.3);
    }
    .angka.merah { background: linear-gradient(135deg, #C00000, #E74C3C); }
    .angka.hijau { background: linear-gradient(135deg, #70AD47, #27AE60); }
    .angka .label { font-size: .85rem; opacity: .85; }
    .angka .nilai { font-size: 2.8rem; font-weight: 800; color: white; line-height: 1.1; }
    .angka .rumus { font-size: 1.3rem; font-weight: 800; margin: .2rem 0 .4rem; }
    .angka .ket { font-size: .85rem; opacity: .9; margin-top: .2rem; }

    /* Tabel */
    .tabel { width: 100%; border-collapse: collapse; font-size: .88rem; margin: .4rem 0; }
    .tabel th { background: #1A3C6E; color: white; text-align: center; padding: 8px; border: 1px solid #ccc; font-weight: 700; }
    .tabel td { padding: 7px; border: 1px solid #ccc; text-align: center; color: #2C3E50; }
    .tabel tr:nth-child(even) td { background: #F8FAFF; }
    .pos { color: #4C9A2A; font-weight: 800; }
    .neg { color: #C00000; font-weight: 800; }

    /* Label status */
    .tag { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: .75rem; font-weight: 700; color: white; }
    .tag.selesai { background: #70AD47; }
    .tag.buka { background: #2E75B6; }
    .tag.kunci { background: #BDBDBD; }

    /* Streak & lencana */
    .lencana { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: .75rem; font-weight: 700;
               background: #EEEEEE; color: #9E9E9E; margin: 2px 4px 2px 0; }
    .lencana.aktif { background: #ED7D31; color: white; }
    .streak-angka { font-size: 2rem; font-weight: 800; color: #1A3C6E; line-height: 1; }
    .kotak.streak .streak-angka { color: #E65100; }
    .kecil { font-size: .8rem; color: #5F6B7A; }
    .kotak.streak .kecil { color: #795548; }

    /* Kartu soal */
    .soal { border: 1px solid #E0E0E0; border-left: 5px solid #2E75B6; border-radius: 12px;
            padding: .9rem 1.1rem; margin: 1rem 0 .3rem; background: #FFFFFF; }
    .soal .meta { font-size: .78rem; color: #5F6B7A; margin-bottom: .4rem; }
    .soal .tanya { font-size: .98rem; font-weight: 700; color: #2C3E50; }
    .soal .konteks { margin-top: .5rem; background: #FFF8E6; padding: .5rem .8rem; border-radius: 8px;
                     font-size: .88rem; color: #8B6914; }

    /* Sidebar */
    .sidebar-judul { background: #1A3C6E; color: white; padding: .6rem 1rem; border-radius: 10px;
                     font-weight: 800; text-align: center; margin-bottom: .5rem; }

    .stButton > button { border-radius: 10px; font-weight: 700; transition: all .2s; }
    .stButton > button:hover { transform: translateY(-2px); }
    [data-testid="metric-container"] { background: #F8FAFF; border: 1px solid #BDD7EE; border-radius: 12px; padding: .8rem; }
    hr { border: none; border-top: 2px solid #EBF3FB; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
# KOMPONEN TAMPILAN (dipakai berulang)
# ══════════════════════════════════════════
LANGKAH_WARNA = {
    1: ("#2E75B6", "#EBF3FB"),
    2: ("#ED7D31", "#FFF4EC"),
    3: ("#70AD47", "#F0FBF0"),
    4: ("#7030A0", "#F5EFFF"),
    5: ("#C00000", "#FEF0F0"),
    6: ("#1A3C6E", "#EBF3FB"),
}


def langkah(no, judul, isi, istilah=""):
    c, bg = LANGKAH_WARNA[no]
    ist = f'<span class="istilah">{istilah}</span>' if istilah else ""
    st.markdown(
        f'<div class="langkah" style="border-color:{c};background:{bg};">'
        f'<div class="langkah-judul" style="color:{c};">Langkah {no} · {judul}{ist}</div>'
        f'<div class="langkah-isi">{isi}</div></div>', unsafe_allow_html=True)


def kotak(isi, jenis=""):
    st.markdown(f'<div class="kotak {jenis}">{isi}</div>', unsafe_allow_html=True)


def tabel(header, baris):
    h = "".join(f"<th>{x}</th>" for x in header)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in baris)
    st.markdown(f'<table class="tabel"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>',
                unsafe_allow_html=True)


def tt(n):
    """Tulis bilangan dengan tanda: +5, −5, 0."""
    return "0" if n == 0 else f"{n:+d}".replace("-", "−")


# ══════════════════════════════════════════
# DATABASE (SQLite)
# ══════════════════════════════════════════
def q(sql, params=(), one=False, commit=False):
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
        nama TEXT NOT NULL, kelas TEXT NOT NULL,
        pin_hash TEXT NOT NULL, dibuat TEXT NOT NULL,
        UNIQUE(nama, kelas)
    );
    CREATE TABLE IF NOT EXISTS progres(
        siswa_id INTEGER NOT NULL, materi TEXT NOT NULL, selesai_pada TEXT NOT NULL,
        PRIMARY KEY(siswa_id, materi)
    );
    CREATE TABLE IF NOT EXISTS aktivitas(
        siswa_id INTEGER NOT NULL, tanggal TEXT NOT NULL, jumlah INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(siswa_id, tanggal)
    );
    CREATE TABLE IF NOT EXISTS latihan(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        siswa_id INTEGER NOT NULL, waktu TEXT NOT NULL,
        skor INTEGER NOT NULL, total INTEGER NOT NULL, detail TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS refleksi(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        siswa_id INTEGER NOT NULL, waktu TEXT NOT NULL, r1 TEXT, r2 TEXT, r3 TEXT
    );
    """)
    conn.commit()
    conn.close()
    return True


init_db()


# ══════════════════════════════════════════
# FUNGSI BANTU: WAKTU, AKUN, PROGRES, STREAK
# ══════════════════════════════════════════
def sekarang():
    return datetime.now(WIB)


def hari_ini():
    return sekarang().date()


def hash_pin(pin):
    return hashlib.sha256(("jbb-v1-" + pin).encode()).hexdigest()


def get_guru_password():
    """Password guru diambil dari st.secrets (GURU_PASSWORD). Bawaan: guru123 — segera ganti."""
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
            return None, "PIN-nya tidak cocok. Pakai PIN yang kamu buat saat pertama kali masuk."
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
    """Return (hari beruntun saat ini, rekor terpanjang)."""
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
# KOMPONEN: KEMAJUAN, STREAK, CEK PEMAHAMAN
# ══════════════════════════════════════════
def tampil_streak(sid):
    tgl = get_tanggal_aktif(sid)
    cur, best = hitung_streak(tgl)
    today = hari_ini()
    hari = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]

    titik = ""
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        aktif = d in tgl
        bg = "#FF9800" if aktif else "#E0E0E0"
        isi = "🔥" if aktif else ""
        tebal = f"outline:2px solid {C_UTAMA};outline-offset:2px;" if d == today else ""
        titik += (
            '<div style="text-align:center;">'
            f'<div style="width:28px;height:28px;border-radius:50%;background:{bg};color:#fff;{tebal}'
            f'display:flex;align-items:center;justify-content:center;font-size:.8rem;margin:auto;">{isi}</div>'
            f'<div class="kecil" style="margin-top:3px;">{hari[d.weekday()]}</div></div>'
        )

    if today in tgl:
        status = "Hari ini kamu sudah belajar."
    else:
        status = "Kamu belum belajar hari ini. Buka salah satu materi agar hari beruntunmu tidak putus."

    lencana = "".join(
        f'<span class="lencana {"aktif" if best >= t else ""}">{n}</span>' for t, n in LENCANA)
    berikut = next((t for t, _ in LENCANA if cur < t), None)
    target = f"{berikut - cur} hari lagi untuk lencana berikutnya." if berikut else "Semua lencana sudah kamu dapat."

    st.markdown(f"""
    <div class="kotak streak">
    <div class="kecil">🔥 Belajar berturut-turut</div>
    <div><span class="streak-angka">{cur}</span> hari</div>
    <div class="kecil">Rekor: {best} hari · Total hari belajar: {len(tgl)}</div>
    <div style="display:flex;gap:10px;justify-content:space-between;margin:.8rem 0 .4rem;">{titik}</div>
    <div style="font-size:.88rem;">{status}</div>
    <div style="margin-top:.5rem;">{lencana}</div>
    <div class="kecil">{target}</div>
    </div>
    """, unsafe_allow_html=True)


def tampil_ketercapaian(sid, selesai):
    jml = len([k for k in URUTAN if k in selesai])
    persen = int(jml / len(URUTAN) * 100)
    st.markdown(f'<div class="kecil">Kemajuan belajar</div>'
                f'<div><span class="streak-angka">{persen}%</span> '
                f'<span class="kecil">({jml} dari {len(URUTAN)} tahap selesai)</span></div>',
                unsafe_allow_html=True)
    st.progress(persen / 100)
    baris = []
    for k in URUTAN:
        if k in selesai:
            tg = '<span class="tag selesai">✅ Selesai</span>'
        elif akses_terbuka(k, selesai):
            tg = '<span class="tag buka">▶️ Bisa dibuka</span>'
        else:
            tg = '<span class="tag kunci">🔒 Terkunci</span>'
        baris.append([NAMA_HALAMAN[k], tg])
    tabel(["Tahap", "Status"], baris)

    best = q("SELECT MAX(CAST(skor AS REAL)/total*100) AS n, COUNT(*) AS c FROM latihan WHERE siswa_id=?",
             (sid,), one=True)
    if best and best["c"]:
        st.markdown(f'<div class="kecil">Nilai latihan terbaik: <b>{best["n"]:.0f}</b> '
                    f'(dikerjakan {best["c"]} kali)</div>', unsafe_allow_html=True)


def blok_selesai(kp):
    st.divider()
    st.markdown("### 🏁 Cek pemahaman")
    if is_guru():
        kotak("Mode guru: bagian ini hanya pratinjau dan tidak dicatat.", "netral")
        return

    sid = st.session_state.siswa["id"]
    selesai = get_selesai(sid)
    berikut = {"kp1": "kp2", "kp2": "kp3", "kp3": "latihan"}[kp]

    if kp in selesai:
        kotak(f"Kegiatan ini sudah selesai. Materi berikutnya sudah terbuka: <b>{NAMA_HALAMAN[berikut]}</b>.", "benar")
        st.button(f"Lanjut ke {NAMA_HALAMAN[berikut]}", on_click=pindah, args=(berikut,), type="primary")
        return

    cek = CEK[kp]
    st.write("Jawab satu pertanyaan ini untuk membuka materi berikutnya. "
             "Pastikan kamu sudah mencatat hasil percobaanmu di LKS.")
    st.markdown(cek["soal"])
    jawab = st.radio("Pilih jawaban:", cek["pilihan"], index=None, key=f"cek_{kp}")
    catat = st.checkbox("Aku sudah mencatat hasil percobaanku di LKS", key=f"lks_{kp}")

    if st.button("Periksa jawaban", key=f"btn_{kp}", type="primary"):
        if jawab is None:
            st.warning("Pilih satu jawaban dulu.")
        elif not catat:
            st.warning("Centang dulu kotak di atas setelah kamu selesai mencatat di LKS.")
        elif cek["pilihan"].index(jawab) != cek["jawaban"]:
            st.error(f"Jawabanmu belum tepat. Petunjuk: {cek['petunjuk']} Coba percobaan tadi sekali lagi, lalu jawab ulang.")
        else:
            tandai_selesai(sid, kp)
            st.rerun()


def tampil_terkunci(halaman, selesai):
    idx = URUTAN.index(halaman)
    syarat = URUTAN[idx - 1]
    st.markdown(f"## 🔒 {NAMA_HALAMAN[halaman].split(' ', 1)[1]}")
    kotak(f"Halaman ini belum bisa dibuka. Selesaikan dulu <b>{NAMA_HALAMAN[syarat]}</b>. "
          "Urutan belajarnya: KP 1, KP 2, KP 3, lalu Latihan Soal.", "catatan")
    target = next((k for k in URUTAN if k not in selesai), URUTAN[0])
    st.button(f"Buka {NAMA_HALAMAN[target]}", on_click=pindah, args=(target,), type="primary")


# ══════════════════════════════════════════
# HALAMAN MASUK
# ══════════════════════════════════════════
def halaman_login():
    st.markdown("## 🔐 Masuk")
    t1, t2 = st.tabs(["Siswa", "Guru"])

    with t1:
        st.write("Baru pertama kali? Isi nama dan kelas, lalu buat PIN 4 angka. "
                 "Berikutnya, masuk dengan data yang sama supaya kemajuan belajarmu tersimpan.")
        with st.form("form_siswa"):
            nama = st.text_input("Nama lengkap", placeholder="Contoh: Budi Santoso")
            kelas = st.text_input("Kelas", placeholder="Contoh: VII A")
            pin = st.text_input("PIN (4 angka)", type="password", max_chars=4)
            ok = st.form_submit_button("Masuk", type="primary")
        if ok:
            if len(nama.strip()) < 3:
                st.error("Nama minimal 3 huruf.")
            elif not kelas.strip():
                st.error("Kelas belum diisi.")
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
            ok2 = st.form_submit_button("Masuk sebagai guru", type="primary")
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
    st.markdown("## 📊 Dashboard Guru")
    today = hari_ini()

    siswa = baca_df("SELECT id,nama,kelas,dibuat FROM siswa ORDER BY kelas,nama")
    if siswa.empty:
        st.info("Belum ada siswa yang mendaftar. Bagikan link aplikasi ini kepada siswa.")
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
            status = "Tuntas"
        elif terakhir is None or persen == 0:
            status = "Belum mulai"
        elif tak_aktif is not None and tak_aktif >= 3:
            status = f"Tidak aktif {tak_aktif} hari"
        else:
            status = "Sedang belajar"

        rows.append({
            "ID": sid, "Nama": s["nama"], "Kelas": s["kelas"],
            "kp1": "kp1" in done, "kp2": "kp2" in done, "kp3": "kp3" in done, "latihan": "latihan" in done,
            "Nilai Terbaik": round(nilai.max()) if not nilai.empty else np.nan,
            "Nilai Terakhir": round(nilai.iloc[-1]) if not nilai.empty else np.nan,
            "Percobaan": len(l), "Progres": persen,
            "Hari Beruntun": cur, "Rekor": best, "Hari Belajar": len(tg),
            "Terakhir Aktif": str(terakhir) if terakhir else "-",
            "_terakhir": terakhir, "Status": status,
        })
    rekap = pd.DataFrame(rows)

    f1, f2 = st.columns(2)
    with f1:
        kelas_pilih = st.multiselect("Kelas", sorted(rekap["Kelas"].unique()),
                                     default=sorted(rekap["Kelas"].unique()))
    with f2:
        cari = st.text_input("Cari nama siswa", placeholder="Ketik nama...")
    rf = rekap[rekap["Kelas"].isin(kelas_pilih)]
    if cari.strip():
        rf = rf[rf["Nama"].str.contains(cari.strip(), case=False)]
    if rf.empty:
        st.warning("Tidak ada data yang sesuai.")
        return

    aktif_hari_ini = int((rf["_terakhir"] == today).sum())
    nilai_rata = rf["Nilai Terbaik"].mean()
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Jumlah siswa", len(rf))
    m2.metric("Aktif hari ini", aktif_hari_ini)
    m3.metric("Rata-rata progres", f"{rf['Progres'].mean():.0f}%")
    m4.metric("Rata-rata nilai terbaik", "-" if pd.isna(nilai_rata) else f"{nilai_rata:.0f}")
    m5.metric("Tuntas semua tahap", int((rf["Progres"] == 100).sum()))

    tab_a, tab_b, tab_c, tab_d, tab_e, tab_f = st.tabs(
        ["Rekap Siswa", "Ringkasan", "Detail Siswa", "Analisis Soal", "Refleksi", "Kelola Data"])

    with tab_a:
        tampil = rf.copy()
        for k, lbl in [("kp1", "KP 1"), ("kp2", "KP 2"), ("kp3", "KP 3"), ("latihan", "Latihan")]:
            tampil[lbl] = tampil[k].map({True: "Selesai", False: "-"})
        kolom = ["Nama", "Kelas", "KP 1", "KP 2", "KP 3", "Latihan", "Nilai Terbaik", "Nilai Terakhir",
                 "Percobaan", "Progres", "Hari Beruntun", "Rekor", "Hari Belajar", "Terakhir Aktif", "Status"]
        st.dataframe(
            tampil[kolom], use_container_width=True, hide_index=True,
            column_config={"Progres": st.column_config.ProgressColumn(
                "Progres", min_value=0, max_value=100, format="%d%%")})
        st.caption("Status \"Tidak aktif\" muncul jika siswa belum membuka materi selama 3 hari atau lebih dan belum tuntas.")

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

        st.markdown("**Siswa yang perlu diperhatikan**")
        perlu = rf[rf["Status"].str.startswith("Tidak aktif") | (rf["Status"] == "Belum mulai")]
        if perlu.empty:
            st.success("Semua siswa sudah berjalan dengan baik.")
        else:
            st.dataframe(perlu[["Nama", "Kelas", "Progres", "Terakhir Aktif", "Status"]],
                         use_container_width=True, hide_index=True)

        st.markdown("**Hari beruntun terbanyak**")
        top = rf.sort_values(["Hari Beruntun", "Rekor"], ascending=False).head(5)
        st.dataframe(top[["Nama", "Kelas", "Hari Beruntun", "Rekor", "Hari Belajar"]],
                     use_container_width=True, hide_index=True)

    with tab_c:
        opsi = {f"{r['Nama']} ({r['Kelas']})": r["ID"] for _, r in rf.iterrows()}
        pilih = st.selectbox("Pilih siswa", list(opsi.keys()))
        sid = int(opsi[pilih])
        d1, d2 = st.columns(2)
        with d1:
            tampil_streak(sid)
            tampil_ketercapaian(sid, get_selesai(sid))
        with d2:
            st.markdown("**Riwayat latihan**")
            lsi = lat[lat.siswa_id == sid].sort_values("id", ascending=False)
            if lsi.empty:
                st.info("Belum mengerjakan latihan.")
            else:
                lsi = lsi.assign(Nilai=(lsi.skor / lsi.total * 100).round(0).astype(int))
                st.dataframe(lsi[["waktu", "skor", "total", "Nilai"]].rename(
                    columns={"waktu": "Waktu", "skor": "Benar", "total": "Jumlah soal"}),
                    use_container_width=True, hide_index=True)
            st.markdown("**Tahap yang sudah selesai**")
            ps = prog[prog.siswa_id == sid]
            if ps.empty:
                st.info("Belum ada tahap yang selesai.")
            else:
                st.dataframe(ps[["materi", "selesai_pada"]].rename(
                    columns={"materi": "Tahap", "selesai_pada": "Selesai pada"}),
                    use_container_width=True, hide_index=True)

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
            st.caption(f"Dihitung dari percobaan terakhir {n} siswa.")
            st.dataframe(dfa, use_container_width=True, hide_index=True,
                         column_config={"% Benar": st.column_config.ProgressColumn(
                             "% Benar", min_value=0, max_value=100, format="%d%%")})
            st.bar_chart(dfa.set_index("No")["% Benar"])
            sulit = dfa[dfa["% Benar"] < 60]
            if sulit.empty:
                st.success("Tidak ada soal dengan tingkat benar di bawah 60%.")
            else:
                st.warning("Soal yang sebaiknya dibahas ulang di kelas (benar kurang dari 60%): " +
                           ", ".join(f"No. {x} ({k})" for x, k in zip(sulit["No"], sulit["KP"])))

    with tab_e:
        ref = baca_df("""SELECT s.nama AS Nama, s.kelas AS Kelas, r.waktu AS Waktu,
                                r.r1 AS 'Bagian paling membantu', r.r2 AS 'Temuan dari kalkulator',
                                r.r3 AS 'Perasaan belajar'
                         FROM refleksi r JOIN siswa s ON s.id=r.siswa_id ORDER BY r.id DESC""")
        ref = ref[ref["Kelas"].isin(kelas_pilih)] if not ref.empty else ref
        if ref.empty:
            st.info("Belum ada refleksi yang disimpan siswa.")
        else:
            st.dataframe(ref, use_container_width=True, hide_index=True)

    with tab_f:
        st.markdown("**Unduh data**")
        unduh = rf.drop(columns=["ID", "_terakhir", "kp1", "kp2", "kp3", "latihan"]).copy()
        st.download_button("Unduh rekap siswa (CSV)", unduh.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"rekap_siswa_{today}.csv", mime="text/csv")
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "rb") as f:
                st.download_button("Unduh cadangan database (.db)", f.read(),
                                   file_name=f"cadangan_data_belajar_{today}.db")
        st.caption("Unduh cadangan secara rutin. Di Streamlit Community Cloud, file database bisa hilang saat aplikasi dimulai ulang.")

        st.divider()
        st.markdown("**Hapus data satu siswa**")
        opsi_h = {f"{r['Nama']} ({r['Kelas']})": int(r["ID"]) for _, r in rekap.iterrows()}
        hapus = st.selectbox("Pilih siswa", list(opsi_h.keys()), key="hapus_pilih")
        yakin = st.checkbox("Saya yakin ingin menghapus siswa ini beserta seluruh datanya", key="hapus_yakin")
        if st.button("Hapus siswa", disabled=not yakin):
            hid = opsi_h[hapus]
            for tbl in ["progres", "aktivitas", "latihan", "refleksi"]:
                q(f"DELETE FROM {tbl} WHERE siswa_id=?", (hid,), commit=True)
            q("DELETE FROM siswa WHERE id=?", (hid,), commit=True)
            st.success("Data siswa dihapus.")
            st.rerun()

        st.divider()
        st.markdown("**Hapus semua data**")
        konfirmasi = st.text_input("Ketik HAPUS SEMUA untuk menghapus seluruh data", key="reset_all")
        if st.button("Hapus semua data", disabled=(konfirmasi != "HAPUS SEMUA")):
            for tbl in ["progres", "aktivitas", "latihan", "refleksi", "siswa"]:
                q(f"DELETE FROM {tbl}", commit=True)
            st.success("Seluruh data dihapus.")
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
# JUDUL APLIKASI
# ══════════════════════════════════════════
st.markdown("""
<div class="judul-app">
    <div class="atas">Matematika · SMP/MTs Kelas VII</div>
    <h1>🔢 Jelajah Bilangan Bulat</h1>
    <p>Coba sendiri dengan kalkulator, temukan polanya, lalu tulis kesimpulanmu.</p>
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
# SIDEBAR
# ══════════════════════════════════════════
with st.sidebar:
    if is_guru():
        st.markdown('<div class="sidebar-judul">Mode Guru</div>', unsafe_allow_html=True)
        st.caption("Semua materi terbuka sebagai pratinjau dan tidak dicatat.")
        opsi_menu = ["dashboard", "beranda", "kp1", "kp2", "kp3", "latihan", "video"]
    else:
        cur_s, _ = hitung_streak(get_tanggal_aktif(SID))
        persen_s = int(len([k for k in URUTAN if k in SELESAI]) / len(URUTAN) * 100)
        st.markdown(f'<div class="sidebar-judul">{SISWA["nama"]}</div>', unsafe_allow_html=True)
        st.caption(f"Kelas {SISWA['kelas']} · {cur_s} hari beruntun · kemajuan {persen_s}%")
        opsi_menu = ["beranda", "kp1", "kp2", "kp3", "latihan", "video"]

    if st.session_state.get("menu") not in opsi_menu:
        st.session_state.menu = opsi_menu[0]

    def label_menu(k):
        base = NAMA_HALAMAN[k]
        if is_guru() or k not in URUTAN:
            return base
        teks = base.split(" ", 1)[1]  # nama tanpa ikon di depan
        if k in SELESAI:
            return "✅ " + teks
        if akses_terbuka(k, SELESAI):
            return base
        return "🔒 " + teks + " (terkunci)"

    st.markdown('<div class="kecil" style="margin-top:.8rem;">Menu</div>', unsafe_allow_html=True)
    tab_choice = st.radio("Menu", options=opsi_menu, key="menu",
                          format_func=label_menu, label_visibility="collapsed")
    if not is_guru():
        st.caption("✅ selesai · 🔒 terkunci (selesaikan tahap sebelumnya dulu)")

    st.divider()
    st.markdown("""
    <div style="font-size:.82rem;color:#5F6B7A;line-height:1.6;">
    <b style="color:#1F2933;">Cara belajar</b><br>
    1. Kerjakan berurutan: KP 1, KP 2, KP 3, lalu Latihan.<br>
    2. Catat hasil percobaanmu di LKS.<br>
    3. Jawab cek pemahaman untuk membuka materi berikutnya.<br>
    4. Belajar sedikit setiap hari lebih baik daripada sekali banyak.
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    if st.button("Keluar", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.caption("Kurikulum Merdeka · Fase D\n\nPenulis: Efti Puji Lestari")

# ══════════════════════════════════════════
# GERBANG URUTAN BELAJAR
# ══════════════════════════════════════════
if tab_choice in URUTAN and not akses_terbuka(tab_choice, SELESAI):
    tampil_terkunci(tab_choice, SELESAI)
    st.stop()

# Catat hari belajar (sekali per hari per sesi) → dipakai untuk hitung hari beruntun
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
# BERANDA
# ══════════════════════════════════════════
elif tab_choice == "beranda":
    if SID:
        st.markdown(f"## 👋 Halo, {SISWA['nama'].split()[0]}")
        st.write("Di sini kamu belajar bilangan bulat dengan cara mencoba sendiri, bukan hanya membaca rumus. "
                 "Kerjakan kegiatan secara berurutan, dan catat hasilnya di LKS.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🎯 Kemajuan belajarmu")
            tampil_ketercapaian(SID, SELESAI)
        with c2:
            st.markdown("#### 🔥 Belajar harian")
            tampil_streak(SID)
        st.button("Lanjutkan belajar", type="primary", on_click=pindah,
                  args=(next((k for k in URUTAN if k not in SELESAI), "latihan"),))
    else:
        st.markdown("## 🏠 Beranda")
        st.write("Anda masuk sebagai guru. Dashboard pemantauan ada di menu paling atas.")

    st.divider()
    st.markdown("#### 📚 Yang akan kamu pelajari")
    tabel(["Kegiatan", "Isi", "Capaian"], [
        ["KP 1", "Bilangan bulat, garis bilangan, dan lawan (invers) suatu bilangan", "Memahami bilangan bulat"],
        ["KP 2", "Penjumlahan, pengurangan, perkalian, dan pembagian bilangan bulat", "TP 5 · Operasi hitung"],
        ["KP 3", "Faktorisasi prima, FPB, dan KPK", "TP 8 · FPB dan KPK"],
        ["Latihan", "Soal cerita sehari-hari, termasuk soal keuangan sederhana", "TP 9 · Masalah kontekstual"],
    ])

    st.markdown("#### 🔬 Cara kerja setiap kegiatan")
    cara = [
        ("1 · Coba pikirkan", "Baca situasi atau pertanyaan di awal kegiatan."),
        ("2 · Tulis dugaanmu", "Tulis dugaanmu di LKS sebelum mencoba."),
        ("3 · Ayo coba", "Pakai kalkulator, lalu catat hasilnya di LKS."),
        ("4 · Cari polanya", "Lihat hasil yang kamu catat. Apa yang selalu sama?"),
        ("5 · Cocokkan", "Bandingkan hasilmu dengan teman satu kelompok."),
        ("6 · Tarik kesimpulan", "Tulis kesimpulan dengan kata-katamu sendiri."),
    ]
    kolom_cara = st.columns(3)
    for i, (jdl, isi) in enumerate(cara):
        warna, latar = LANGKAH_WARNA[i + 1]
        with kolom_cara[i % 3]:
            st.markdown(
                f'<div style="border-left:5px solid {warna};background:{latar};padding:.8rem 1rem;'
                f'border-radius:0 10px 10px 0;margin-bottom:.8rem;">'
                f'<div style="font-weight:800;color:{warna};font-size:.9rem;">{jdl}</div>'
                f'<div style="font-size:.85rem;color:#444;margin-top:.3rem;">{isi}</div></div>',
                unsafe_allow_html=True)
    kotak("<b>Catatan:</b> jangan langsung menekan-nekan kalkulator. Tulis dugaanmu dulu, "
          "baru buktikan dengan kalkulator apakah dugaanmu benar.", "catatan")


# ══════════════════════════════════════════
# KP 1 — GARIS BILANGAN
# ══════════════════════════════════════════
elif tab_choice == "kp1":
    st.markdown("## 📍 KP 1 · Memahami Bilangan Bulat")

    langkah(1, "Coba pikirkan",
            "Puncak gunung berada di <b>+3.000 meter</b> di atas permukaan laut. "
            "Dasar Palung Jawa berada di <b>−7.000 meter</b> dari permukaan laut.<br>"
            "<b>Apa arti tanda minus (−) pada angka tersebut?</b>", "Stimulation")
    langkah(2, "Tulis dugaanmu",
            "Sebelum mencoba, tulis dugaanmu di LKS:<br>"
            "<i>\"Menurutku, bilangan bulat negatif adalah ... dan letaknya pada garis bilangan ada di ...\"</i>",
            "Problem Statement")
    st.divider()

    langkah(3, "Ayo coba",
            "Geser slider untuk memilih bilangan. Lihat letaknya pada garis bilangan, lalu catat di LKS.",
            "Data Collection")

    col1, col2 = st.columns([1, 2])
    with col1:
        bilangan = st.slider("Pilih bilangan", min_value=-20, max_value=20, value=0, step=1)
        inv = -bilangan
        st.markdown(f'<div class="angka"><div class="label">Bilangan yang dipilih</div>'
                    f'<div class="nilai">{tt(bilangan)}</div></div>', unsafe_allow_html=True)

        if bilangan > 0:
            kotak("<b>Bilangan positif.</b> Letaknya di sebelah <b>kanan</b> nol.", "benar")
        elif bilangan < 0:
            kotak("<b>Bilangan negatif.</b> Letaknya di sebelah <b>kiri</b> nol.", "salah")
        else:
            kotak("<b>Nol.</b> Bukan positif dan bukan negatif. Nol adalah titik tengah garis bilangan.", "netral")

        kotak(f"<b>Lawan (invers penjumlahan)</b><br>Lawan dari {tt(bilangan)} adalah {tt(inv)}.<br>"
              f"Buktinya: {tt(bilangan)} + ({tt(inv)}) = {bilangan + inv}", "catatan")

    with col2:
        fig, ax = plt.subplots(figsize=(10, 3.2))
        ax.set_xlim(-22, 22)
        ax.set_ylim(-1.6, 2)
        ax.axis("off")
        fig.patch.set_facecolor("white")

        ax.annotate("", xy=(21.5, 0), xytext=(-21.5, 0),
                    arrowprops=dict(arrowstyle="<->", color=C_TEKS, lw=2))
        for i in range(-20, 21):
            tick_h = 0.25 if i % 5 == 0 else 0.15
            ax.plot([i, i], [-tick_h, tick_h], color=C_TEKS if i % 5 == 0 else "#B8C0CA", lw=1.3)
            if i % 5 == 0:
                ax.text(i, -0.5, str(i).replace("-", "−"), ha="center", va="top", fontsize=10, color=C_TEKS)

        ax.text(-10, 1.5, "negatif", ha="center", fontsize=11, color=C_NEG)
        ax.text(10, 1.5, "positif", ha="center", fontsize=11, color=C_POS)

        dot = C_NEG if bilangan < 0 else (C_POS if bilangan > 0 else C_REDUP)
        ax.plot(bilangan, 0, "o", color=dot, markersize=16, zorder=5,
                markeredgecolor="white", markeredgewidth=2)
        ax.text(bilangan, 0.7, tt(bilangan), ha="center", fontsize=12, color=dot, fontweight="bold")

        if bilangan != 0:
            ax.annotate("", xy=(inv, 0), xytext=(bilangan, 0),
                        arrowprops=dict(arrowstyle="->", color=C_CATATAN, lw=1.5,
                                        connectionstyle="arc3,rad=-0.4"))
            ax.text((bilangan + inv) / 2, -1.2, f"lawannya: {tt(inv)}", ha="center",
                    fontsize=10, color=C_CATATAN)
        ax.set_title("Garis bilangan", fontsize=11, color=C_TEKS, loc="left")
        st.pyplot(fig)
        plt.close()

    st.divider()
    langkah(4, "Cari polanya",
            "Coba beberapa bilangan lain dengan slider, lalu lengkapi dua baris terakhir di LKS-mu.",
            "Data Processing")
    tabel(["Bilangan", "Letak pada garis bilangan", "Jenis", "Pembuktian lawan", "Lawan"], [
        ["+8", "Kanan nol", "Positif", "8 + (−8) = 0", "−8"],
        ["−5", "Kiri nol", "Negatif", "−5 + 5 = 0", "+5"],
        ["0", "Titik tengah", "Nol", "0 + 0 = 0", "0"],
        ["−12", "...", "...", "...", "..."],
        ["+17", "...", "...", "...", "..."],
    ])
    langkah(5, "Cocokkan", "Bandingkan tabelmu dengan teman satu kelompok. Samakah hasilnya?", "Verification")
    langkah(6, "Tarik kesimpulan",
            "Tulis kesimpulanmu di LKS dengan kata-katamu sendiri. Setelah itu, bandingkan dengan rangkuman di bawah.",
            "Generalization")

    with st.expander("Lihat rangkuman (tulis kesimpulanmu dulu, ya)"):
        kotak("""<b>Rangkuman bilangan bulat</b><br>
        • Bilangan bulat terdiri dari bilangan negatif (…, −3, −2, −1), nol (0), dan bilangan positif (1, 2, 3, …).<br>
        • Semakin ke <b>kanan</b> pada garis bilangan, nilainya semakin <b>besar</b>.<br>
        • Semakin ke <b>kiri</b>, nilainya semakin <b>kecil</b>.<br>
        • Lawan (invers penjumlahan) dari a adalah −a, karena a + (−a) = 0.""", "benar")

    blok_selesai("kp1")


# ══════════════════════════════════════════
# KP 2 — OPERASI HITUNG
# ══════════════════════════════════════════
elif tab_choice == "kp2":
    st.markdown("## 🔧 KP 2 · Operasi Hitung Bilangan Bulat")

    langkah(1, "Coba pikirkan",
            "Sebuah klub sepak bola melepas 3 pemain yang bermain buruk. Kalau ditulis sebagai perkalian, "
            "hasilnya: <b>(−3) × (−1) = ?</b> Apakah performa tim naik atau turun?<br>"
            "Mengapa (−3) × (−4) = +12, bukan −12?<br>"
            "<b>Apa yang menentukan tanda hasil perkalian dan pembagian bilangan bulat?</b>", "Stimulation")
    langkah(2, "Tulis dugaanmu",
            "Tulis di LKS:<br><i>\"Menurutku, hasil perkalian dua bilangan negatif adalah ... karena ...\"</i>",
            "Problem Statement")
    st.divider()

    langkah(3, "Ayo coba",
            "Masukkan dua bilangan dan pilih operasinya. Catat beberapa hasilnya di tabel LKS.",
            "Data Collection")

    col1, col2 = st.columns(2)
    with col1:
        a = st.number_input("Bilangan pertama (a)", value=-6, step=1, min_value=-999, max_value=999)
        op = st.selectbox("Operasi", ["+  (tambah)", "−  (kurang)", "×  (kali)", "÷  (bagi)"])
        b = st.number_input("Bilangan kedua (b)", value=-4, step=1, min_value=-999, max_value=999)

        op_sym = op[0]
        hasil = None
        if op_sym == "+":
            hasil = a + b
        elif op_sym == "−":
            hasil = a - b
        elif op_sym == "×":
            hasil = a * b
        else:
            if b == 0:
                st.error("Bilangan tidak bisa dibagi dengan nol.")
            else:
                hasil = a // b if a % b == 0 else a / b

    with col2:
        if hasil is not None:
            if isinstance(hasil, int):
                hasil_teks = str(hasil).replace("-", "−")
            else:
                hasil_teks = f"{hasil:.2f}".replace("-", "−")
            jenis = "positif" if hasil > 0 else ("negatif" if hasil < 0 else "nol")
            st.markdown(f"""
            <div class="angka">
                <div class="label">Kalimat matematika</div>
                <div class="rumus">({tt(a)}) {op_sym} ({tt(b)})</div>
                <div class="label">Hasil</div>
                <div class="nilai">{hasil_teks}</div>
                <div class="ket">Hasilnya {jenis}</div>
            </div>
            """, unsafe_allow_html=True)

            if not isinstance(hasil, int):
                st.caption("Hasilnya bukan bilangan bulat karena a tidak habis dibagi b.")

            if op_sym in ["×", "÷"] and a != 0 and b != 0:
                ta = "positif" if a > 0 else "negatif"
                tb = "positif" if b > 0 else "negatif"
                if (a > 0) == (b > 0):
                    simpul = "Tanda keduanya <b>sama</b>, jadi hasilnya <b>positif</b>."
                else:
                    simpul = "Tanda keduanya <b>berbeda</b>, jadi hasilnya <b>negatif</b>."
                kotak(f"<b>Cek tandanya</b><br>a = {tt(a)} ({ta}) · b = {tt(b)} ({tb})<br>{simpul}", "catatan")

    st.divider()
    langkah(4, "Cari polanya",
            "Coba semua kombinasi di bawah dengan kalkulator, lalu lihat: kapan hasilnya positif dan kapan negatif?",
            "Data Processing")

    def sel_hasil(r):
        kelas = "pos" if r > 0 else "neg"
        return f'<span class="{kelas}">{str(r).replace("-", "−")}</span>'

    c3a, c3b = st.columns(2)
    with c3a:
        st.markdown("**Perkalian**")
        tabel(["Operasi", "Hasil"], [
            ["(+6) × (+4)", sel_hasil(6 * 4)],
            ["(+6) × (−4)", sel_hasil(6 * -4)],
            ["(−6) × (+4)", sel_hasil(-6 * 4)],
            ["(−6) × (−4)", sel_hasil(-6 * -4)],
        ])
    with c3b:
        st.markdown("**Pembagian**")
        tabel(["Operasi", "Hasil"], [
            ["(+24) ÷ (+6)", sel_hasil(24 // 6)],
            ["(+24) ÷ (−6)", sel_hasil(24 // -6)],
            ["(−24) ÷ (+6)", sel_hasil(-24 // 6)],
            ["(−24) ÷ (−6)", sel_hasil(-24 // -6)],
        ])
    st.caption("Hijau = hasil positif, merah = hasil negatif.")

    langkah(5, "Cocokkan", "Bandingkan temuanmu dengan teman satu kelompok.", "Verification")
    langkah(6, "Tarik kesimpulan",
            "Tulis aturan tanda yang kamu temukan di LKS, lalu cocokkan dengan rangkuman di bawah.",
            "Generalization")

    with st.expander("Lihat rangkuman aturan tanda (tulis kesimpulanmu dulu, ya)"):
        tabel(["Tanda a", "Operasi", "Tanda b", "Tanda hasil"], [
            ["+", "× atau ÷", "+", '<span class="pos">Positif</span>'],
            ["−", "× atau ÷", "−", '<span class="pos">Positif</span>'],
            ["+", "× atau ÷", "−", '<span class="neg">Negatif</span>'],
            ["−", "× atau ÷", "+", '<span class="neg">Negatif</span>'],
        ])
        kotak("<b>Intinya</b><br>Tanda <b>sama</b> → hasil <b>positif</b>.<br>"
              "Tanda <b>berbeda</b> → hasil <b>negatif</b>.", "benar")

    blok_selesai("kp2")


# ══════════════════════════════════════════
# KP 3 — FAKTOR, FPB, KPK
# ══════════════════════════════════════════
elif tab_choice == "kp3":
    st.markdown("## 🌳 KP 3 · Faktor, FPB, dan KPK")

    langkah(1, "Coba pikirkan",
            "Ibu punya <b>24 kue nastar</b> dan <b>36 kue cokelat</b>. Ibu ingin membaginya ke beberapa piring "
            "dengan jumlah yang sama rata dan tidak ada sisa.<br>"
            "<b>Paling banyak berapa piring yang bisa dipakai? Berapa kue di setiap piring?</b>", "Stimulation")
    st.divider()

    tab3a, tab3b = st.tabs(["Pohon Faktor", "FPB dan KPK"])

    with tab3a:
        langkah(3, "Ayo coba",
                "Masukkan sebuah bilangan, perhatikan pohon faktor yang terbentuk, lalu catat di LKS.",
                "Data Collection")
        col1, col2 = st.columns([1, 2])
        with col1:
            n = st.number_input("Bilangan (2 sampai 200)", min_value=2, max_value=200, value=36, step=1)
            fp = faktorisasi_prima(n)
            fp_str = " × ".join([f"{p}" + (f"^{e}" if e > 1 else "") for p, e in fp.items()])
            semua_f = semua_faktor(n)
            is_prima = len(semua_f) == 2
            teks_prima = "Ya" if is_prima else "Bukan"
            daftar_faktor = ", ".join(map(str, semua_f))

            st.markdown(f"""
            <div class="angka">
                <div class="label">Faktorisasi prima</div>
                <div class="rumus">{n} = {fp_str}</div>
                <div class="ket">Bilangan prima? {teks_prima}</div>
            </div>
            """, unsafe_allow_html=True)
            kotak(f"<b>Semua faktor dari {n}:</b><br>{daftar_faktor}<br><b>Banyak faktor:</b> {len(semua_f)}")

        with col2:
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
                        cid1 = len(nodes)
                        nodes, edges = get_pohon_nodes(n, d, x - dx / (level + 1), y - 1.2,
                                                       dx * 0.6, level + 1, nodes, edges)
                        edges.append((node_id, cid1))
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
            fig2.patch.set_facecolor("white")

            for nid1, nid2 in edges_list:
                ax2.plot([nodes_list[nid1][1], nodes_list[nid2][1]],
                         [nodes_list[nid1][2], nodes_list[nid2][2]],
                         "-", color="#B8C0CA", lw=1.5, zorder=1)

            for nid, x, y, label, is_p, is_root in nodes_list:
                color = C_UTAMA if is_root else (C_POS if is_p else "#2E75B6")
                ax2.scatter([x], [y], s=620 if is_root else 440, c=color, zorder=3,
                            edgecolors="white", linewidths=2)
                ax2.text(x, y, label, ha="center", va="center", fontsize=10,
                         color="white", fontweight="bold", zorder=4)

            ax2.set_title(f"Pohon faktor dari {n}:  {fp_str}", fontsize=11, color=C_TEKS, loc="left")
            ax2.legend(handles=[
                mpatches.Patch(facecolor=C_UTAMA, label="Bilangan awal"),
                mpatches.Patch(facecolor=C_POS, label="Faktor prima"),
                mpatches.Patch(facecolor="#2E75B6", label="Faktor komposit (dipecah lagi)"),
            ], loc="lower right", fontsize=9, frameon=False)
            st.pyplot(fig2)
            plt.close()

    with tab3b:
        langkah(3, "Ayo coba",
                "Masukkan dua bilangan, lihat faktorisasi primanya, lalu catat pola FPB dan KPK di LKS.",
                "Data Collection")
        cola, colb = st.columns(2)
        with cola:
            bil1 = st.number_input("Bilangan pertama", min_value=2, max_value=200, value=24, step=1)
        with colb:
            bil2 = st.number_input("Bilangan kedua", min_value=2, max_value=200, value=36, step=1)

        fp1 = faktorisasi_prima(bil1)
        fp2 = faktorisasi_prima(bil2)
        semua_p = sorted(set(list(fp1.keys()) + list(fp2.keys())))

        fpb, kpk = 1, 1
        for p in semua_p:
            e1, e2 = fp1.get(p, 0), fp2.get(p, 0)
            fpb *= p ** min(e1, e2)
            kpk *= p ** max(e1, e2)

        col1, col2, col3 = st.columns([1.3, 1, 1])
        with col1:
            fp1_str = " × ".join([f"{p}" + (f"^{e}" if e > 1 else "") for p, e in fp1.items()])
            fp2_str = " × ".join([f"{p}" + (f"^{e}" if e > 1 else "") for p, e in fp2.items()])
            kotak(f"<b>Faktorisasi prima</b><br>{bil1} = {fp1_str}<br>{bil2} = {fp2_str}")
            baris = []
            for p in semua_p:
                e1, e2 = fp1.get(p, 0), fp2.get(p, 0)
                baris.append([p, e1 if e1 else "—", e2 if e2 else "—",
                              min(e1, e2) if min(e1, e2) else "—", max(e1, e2)])
            tabel(["Prima", f"Pangkat di {bil1}", f"Pangkat di {bil2}", "Terkecil (FPB)", "Terbesar (KPK)"], baris)

        with col2:
            fpb_str = " × ".join([f"{p}" + (f"^{min(fp1.get(p, 0), fp2.get(p, 0))}" if min(fp1.get(p, 0), fp2.get(p, 0)) > 1 else "")
                                  for p in semua_p if min(fp1.get(p, 0), fp2.get(p, 0)) > 0]) or "1"
            st.markdown(f"""
            <div class="angka merah">
                <div class="label">FPB({bil1}, {bil2})</div>
                <div class="ket">= {fpb_str}</div>
                <div class="nilai">{fpb}</div>
                <div class="ket">Faktor prima yang sama, pangkat terkecil</div>
            </div>
            """, unsafe_allow_html=True)
            kotak(f"Artinya {bil1} dan {bil2} sama-sama habis dibagi {fpb}. "
                  f"Pada soal kue, kuenya bisa dibagi ke <b>{fpb} piring</b>.", "netral")

        with col3:
            kpk_str = " × ".join([f"{p}" + (f"^{max(fp1.get(p, 0), fp2.get(p, 0))}" if max(fp1.get(p, 0), fp2.get(p, 0)) > 1 else "")
                                  for p in semua_p if max(fp1.get(p, 0), fp2.get(p, 0)) > 0])
            st.markdown(f"""
            <div class="angka hijau">
                <div class="label">KPK({bil1}, {bil2})</div>
                <div class="ket">= {kpk_str}</div>
                <div class="nilai">{kpk}</div>
                <div class="ket">Semua faktor prima, pangkat terbesar</div>
            </div>
            """, unsafe_allow_html=True)
            kotak(f"Artinya {kpk} adalah kelipatan terkecil yang habis dibagi {bil1} dan {bil2}. "
                  f"Misalnya dua lampu yang berkedip tiap {bil1} dan {bil2} detik akan berkedip bersamaan tiap <b>{kpk} detik</b>.", "netral")

        langkah(6, "Tarik kesimpulan",
                "Tulis cara mencari FPB dan KPK dengan kata-katamu sendiri, lalu cocokkan dengan rangkuman.",
                "Generalization")
        with st.expander("Lihat rangkuman FPB dan KPK (tulis kesimpulanmu dulu, ya)"):
            kotak("""<b>Mencari FPB dan KPK dengan faktorisasi prima</b><br>
            • <b>FPB</b>: kalikan faktor prima yang <b>sama-sama ada</b>, ambil pangkat yang <b>terkecil</b>.<br>
            • <b>KPK</b>: kalikan <b>semua</b> faktor prima yang muncul, ambil pangkat yang <b>terbesar</b>.<br><br>
            Cara mengingatnya: FPB itu irisan (yang sama saja), KPK itu gabungan (semuanya).""", "benar")

    blok_selesai("kp3")


# ══════════════════════════════════════════
# LATIHAN SOAL
# ══════════════════════════════════════════
elif tab_choice == "latihan":
    st.markdown("## 📝 Latihan Soal")
    kotak("<b>Sebelum mulai:</b> kerjakan sendiri dulu. Pakai kalkulator hanya untuk mengecek jawabanmu, "
          "bukan untuk mencari jawaban. Waktunya sekitar 45 menit.<br>"
          "Untuk soal isian yang jawabannya beberapa bilangan, pisahkan dengan koma.", "catatan")

    if is_guru():
        kotak("Mode guru: jawaban tidak dicatat. Kunci jawaban ditampilkan di bawah tiap soal.", "netral")

    hasil_latihan = st.session_state.get("hasil_latihan")
    sudah_submit = hasil_latihan is not None
    detail_map = {d["no"]: d for d in hasil_latihan["detail"]} if sudah_submit else {}

    for soal in SOAL_LIST:
        kp_color = {"KP 1": "#2E75B6", "KP 2": "#70AD47", "KP 3": "#ED7D31"}[soal["kp"]]
        konteks_html = f'<div class="konteks">{soal["konteks"]}</div>' if soal["konteks"] else ""
        tipe = "Pilihan ganda" if soal["tipe"] == "PG" else "Isian"
        st.markdown(f"""
        <div class="soal" style="border-left-color:{kp_color};">
            <div class="meta"><span style="background:{kp_color};color:white;padding:2px 10px;border-radius:20px;font-weight:700;">{soal['kp']}</span> &nbsp;Soal {soal['no']} · {tipe}</div>
            <div class="tanya">{soal['soal']}</div>
            {konteks_html}
        </div>
        """, unsafe_allow_html=True)

        key = f"soal_{soal['no']}"
        if soal["tipe"] == "PG":
            st.radio("Pilih jawaban", soal["pilihan"], index=None, key=key,
                     label_visibility="collapsed", disabled=sudah_submit)
        else:
            st.text_input("Jawabanmu", key=key, placeholder="Tulis jawabanmu di sini",
                          disabled=sudah_submit)

        if is_guru():
            st.caption(f"Kunci: {soal['jawaban']}. {soal['pembahasan']}")

        if sudah_submit:
            if detail_map[soal["no"]]["benar"]:
                kotak(f"<b>Benar.</b> {soal['pembahasan']}", "benar")
            else:
                kotak(f"<b>Belum tepat.</b> Jawaban yang benar: <b>{soal['jawaban']}</b>. {soal['pembahasan']}", "salah")

    st.write("")
    if not is_guru():
        b1, b2 = st.columns([1, 3])
        with b1:
            st.button("Kumpulkan jawaban", type="primary", use_container_width=True,
                      on_click=kirim_latihan, disabled=sudah_submit)
        with b2:
            st.button("Ulangi dari awal", on_click=ulangi_latihan)

    if sudah_submit:
        skor_total = hasil_latihan["skor"]
        persen = skor_total / len(SOAL_LIST) * 100
        if persen >= 80:
            pesan = "Hasilnya bagus. Kamu sudah memahami materi ini dengan baik."
        elif persen >= 60:
            pesan = "Cukup baik. Baca lagi pembahasan soal yang salah, lalu coba kerjakan ulang."
        else:
            pesan = "Belum maksimal. Pelajari lagi KP yang soalnya masih salah, lalu ulangi latihan ini."
        st.markdown(f"""
        <div class="angka" style="margin-top:1rem;">
            <div class="label">Nilaimu</div>
            <div class="nilai">{persen:.0f}</div>
            <div class="ket">{skor_total} dari {len(SOAL_LIST)} soal benar</div>
            <div class="ket" style="margin-top:.5rem;">{pesan}</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Nilaimu sudah tersimpan dan bisa dilihat guru. Kamu boleh mengulang untuk memperbaiki nilai.")

        st.divider()
        st.markdown("### 🔍 Refleksi")
        st.write("Jawab dengan jujur dan apa adanya. Tidak ada jawaban yang salah.")
        r1 = st.text_area("1. Bagian mana dari aplikasi ini yang paling membantumu memahami bilangan bulat? Kenapa?",
                          height=80, key="r1")
        r2 = st.text_area("2. Apa yang kamu temukan saat mencoba kalkulator, yang tidak kamu dapat dari buku?",
                          height=80, key="r2")
        r3 = st.text_area("3. Bagaimana perasaanmu belajar dengan cara ini?", height=80, key="r3")
        if st.button("Simpan refleksi", type="primary"):
            if r1.strip() or r2.strip() or r3.strip():
                q("INSERT INTO refleksi(siswa_id,waktu,r1,r2,r3) VALUES(?,?,?,?,?)",
                  (SID, sekarang().strftime("%Y-%m-%d %H:%M"), r1, r2, r3), commit=True)
                st.success("Refleksimu tersimpan. Jangan lupa salin juga ke LKS.")
            else:
                st.warning("Isi minimal satu pertanyaan dulu.")


# ══════════════════════════════════════════
# VIDEO MATERI
# ══════════════════════════════════════════
elif tab_choice == "video":
    st.markdown("## 🎬 Video Materi")
    st.write("Tonton video ini sebelum atau sesudah mencoba kalkulator. "
             "Catat hal penting yang kamu dapat di LKS.")
    st.video("https://youtu.be/cQAwIhfC6Dg")
    st.markdown("#### Setelah menonton, jawab di LKS")
    st.markdown("""
1. Apa gagasan utama yang dijelaskan di video?
2. Adakah cara atau trik baru yang kamu pelajari? Jelaskan.
3. Bagian mana yang paling sulit kamu pahami? Diskusikan dengan kelompokmu.
""")

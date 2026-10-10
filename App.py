import random

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Belajar Bilangan Bulat", layout="centered")

BIRU = "#1F4E9C"
MERAH = "#C8372D"
HIJAU = "#2E7D4F"
TINTA = "#1E2430"
ABU = "#5B6472"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600&display=swap');

html, body, .stApp, .stMarkdown, p, label, button, input, textarea {
    font-family: 'Lexend', sans-serif !important;
}
.block-container { padding-top: 2.2rem; max-width: 720px; }
h1 { font-size: 2rem !important; }
h1, h2, h3 { font-weight: 600; color: #1E2430; letter-spacing: -0.01em; }
p, li { line-height: 1.7; }

.catatan {
    background: #F3F6FB;
    border-left: 4px solid #1F4E9C;
    padding: 0.8rem 1rem;
    margin: 1rem 0;
    border-radius: 0 6px 6px 0;
    line-height: 1.7;
}
.awas {
    background: #FFF6F4;
    border-left: 4px solid #C8372D;
    padding: 0.8rem 1rem;
    margin: 1rem 0;
    border-radius: 0 6px 6px 0;
    line-height: 1.7;
}
footer { visibility: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------- fungsi bantu ----------

def fmt(n):
    """Tulis bilangan dengan tanda minus yang rapi."""
    return f"\u2212{abs(n)}" if n < 0 else str(n)


def kurung(n):
    """Bilangan negatif diberi kurung saat dipakai dalam operasi."""
    return f"({fmt(n)})" if n < 0 else str(n)


def garis_bilangan(lo, hi, titik=(), panah=()):
    """Gambar garis bilangan (SVG).
    titik : daftar (nilai, warna, label)
    panah : daftar (dari, ke, warna)
    """
    W, H, M, y = 700, 165, 30, 105

    def x(v):
        return M + (v - lo) * (W - 2 * M) / (hi - lo)

    label_tiap = 1 if hi - lo <= 22 else 5
    warna_panah = {w for _, _, w in panah}

    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" '
         f'font-family="Lexend, sans-serif">']
    s.append("<defs>")
    for w in warna_panah:
        s.append(
            f'<marker id="m{w[1:]}" markerWidth="8" markerHeight="8" refX="6" refY="4" '
            f'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="{w}"/></marker>'
        )
    s.append("</defs>")

    s.append(f'<line x1="{M - 12}" y1="{y}" x2="{W - M + 12}" y2="{y}" '
             f'stroke="{TINTA}" stroke-width="2"/>')

    for v in range(lo, hi + 1):
        tinggi = 10 if v == 0 else 6
        tebal = 2.5 if v == 0 else 1
        s.append(f'<line x1="{x(v):.1f}" y1="{y - tinggi}" x2="{x(v):.1f}" y2="{y + tinggi}" '
                 f'stroke="{TINTA}" stroke-width="{tebal}"/>')
        if v % label_tiap == 0:
            warna = MERAH if v < 0 else (BIRU if v > 0 else TINTA)
            s.append(f'<text x="{x(v):.1f}" y="{y + 28}" text-anchor="middle" '
                     f'font-size="13" fill="{warna}">{fmt(v)}</text>')

    for dari, ke, warna in panah:
        if dari == ke:
            continue
        tinggi = 26 + min(abs(ke - dari) * 3, 30)
        xa, xb = x(dari), x(ke)
        s.append(
            f'<path d="M {xa:.1f} {y - 10} Q {(xa + xb) / 2:.1f} {y - 10 - 2 * tinggi} '
            f'{xb:.1f} {y - 10}" fill="none" stroke="{warna}" stroke-width="2.5" '
            f'marker-end="url(#m{warna[1:]})"/>'
        )

    for v, warna, label in titik:
        s.append(f'<circle cx="{x(v):.1f}" cy="{y}" r="7" fill="{warna}"/>')
        s.append(f'<text x="{x(v):.1f}" y="{y + 50}" text-anchor="middle" font-size="13" '
                 f'font-weight="600" fill="{warna}">{label}</text>')

    s.append("</svg>")
    components.html("".join(s), height=H + 10)


def rentang(*nilai):
    """Tentukan batas garis bilangan supaya semua titik muat."""
    lo = min(min(nilai), 0) - 3
    hi = max(max(nilai), 0) + 3
    if hi - lo < 12:
        hi = lo + 12
    return lo, hi


def catatan(isi, jenis="catatan"):
    st.markdown(f'<div class="{jenis}">{isi}</div>', unsafe_allow_html=True)


# ---------- judul & menu ----------

st.title("Bilangan Bulat")
st.caption("Geser slider-nya, lalu perhatikan apa yang berubah di garis bilangan.")

menu = st.radio(
    "Pilih materi",
    ["Mulai dari sini", "Garis bilangan", "Membandingkan", "Menjumlah", "Mengurangi", "Latihan"],
    horizontal=True,
    label_visibility="collapsed",
)
st.divider()


# ---------- 1. Mulai dari sini ----------

if menu == "Mulai dari sini":
    st.header("Apa itu bilangan bulat?")
    st.write(
        "Pernah lihat angka dengan tanda minus di depannya? Misalnya suhu freezer "
        "yang tertulis \u221218 \u00b0C. Angka seperti itu disebut bilangan negatif. "
        "Kalau dikumpulkan bersama nol dan bilangan positif (1, 2, 3, dst.), "
        "hasilnya disebut bilangan bulat."
    )
    catatan(
        "\u2026, \u22123, \u22122, \u22121, <b>0</b>, 1, 2, 3, \u2026<br>"
        "Bilangan di sebelah kiri nol itu negatif, di sebelah kanan nol itu positif."
    )

    st.subheader("Di mana kita memakainya?")
    st.markdown(
        "- **Suhu.** Freezer bersuhu \u221218 \u00b0C, artinya 18 derajat di bawah nol.\n"
        "- **Lantai gedung.** Parkiran basemen biasanya ditulis lantai \u22121.\n"
        "- **Uang.** Kalau kamu berutang Rp20.000, saldomu bisa ditulis \u221220.000.\n"
        "- **Kedalaman.** Kapal selam di kedalaman 30 meter berada di posisi \u221230 m "
        "dari permukaan laut."
    )
    st.write("Pilih materi di bagian atas untuk mulai. Urutannya boleh dari kiri ke kanan.")


# ---------- 2. Garis bilangan ----------

elif menu == "Garis bilangan":
    st.header("Membaca garis bilangan")
    st.write(
        "Nol adalah titik tengah. Ke kanan bilangannya positif, ke kiri bilangannya negatif. "
        "Coba geser slider di bawah."
    )
    n = st.slider("Pilih bilangan", -10, 10, 4)

    titik = [(n, BIRU if n > 0 else MERAH if n < 0 else TINTA, fmt(n))]
    if n != 0:
        titik.append((-n, ABU, f"lawan: {fmt(-n)}"))
    garis_bilangan(-11, 11, titik)

    if n == 0:
        st.write("Nol tepat di tengah. Lawan dari nol adalah nol itu sendiri.")
    else:
        sisi = "kanan" if n > 0 else "kiri"
        sisi_lawan = "kiri" if n > 0 else "kanan"
        st.write(
            f"{fmt(n)} berjarak {abs(n)} langkah dari nol, di sebelah {sisi}. "
            f"Lawannya adalah {fmt(-n)}: jaraknya sama dari nol, tetapi di sebelah {sisi_lawan}."
        )
    catatan("Dua bilangan disebut <b>berlawanan</b> kalau jaraknya dari nol sama, "
            "tetapi letaknya di sisi yang berbeda.")


# ---------- 3. Membandingkan ----------

elif menu == "Membandingkan":
    st.header("Mana yang lebih besar?")
    st.write("Masukkan dua bilangan, lalu lihat letaknya di garis bilangan.")

    kol1, kol2 = st.columns(2)
    a = kol1.number_input("Bilangan a", min_value=-20, max_value=20, value=-3, step=1)
    b = kol2.number_input("Bilangan b", min_value=-20, max_value=20, value=2, step=1)

    lo, hi = rentang(a, b)
    garis_bilangan(lo, hi, [(a, TINTA, "a"), (b, HIJAU, "b")])

    if a == b:
        st.write(f"{fmt(a)} = {fmt(b)}. Letaknya di titik yang sama.")
    else:
        simbol = ">" if a > b else "<"
        sisi = "kanan" if a > b else "kiri"
        st.subheader(f"{fmt(a)} {simbol} {fmt(b)}")
        st.write(f"{fmt(a)} letaknya di sebelah {sisi} {fmt(b)}, jadi {fmt(a)} "
                 f"{'lebih besar' if a > b else 'lebih kecil'} dari {fmt(b)}.")

    catatan("Makin ke kanan, makin besar. Makin ke kiri, makin kecil.")
    catatan("Hati-hati dengan bilangan negatif. Meskipun 8 lebih besar dari 2, "
            "\u22128 justru lebih kecil dari \u22122, karena \u22128 letaknya lebih jauh di kiri.",
            "awas")


# ---------- 4. Menjumlah ----------

elif menu == "Menjumlah":
    st.header("Penjumlahan")
    st.write(
        "Bayangkan kamu berdiri di sebuah titik pada garis bilangan. Menambah berarti melangkah: "
        "ke kanan kalau yang ditambahkan positif, ke kiri kalau negatif."
    )
    a = st.slider("Mulai dari", -10, 10, 3)
    b = st.slider("Ditambah dengan", -10, 10, -5)
    hasil = a + b

    lo, hi = rentang(a, hasil)
    panah = [(0, a, ABU)]
    if b != 0:
        panah.append((a, hasil, BIRU if b > 0 else MERAH))
    garis_bilangan(lo, hi, [(a, TINTA, "mulai"), (hasil, HIJAU, "hasil")], panah)

    st.subheader(f"{fmt(a)} + {kurung(b)} = {fmt(hasil)}")
    if b > 0:
        st.write(f"Mulai dari {fmt(a)}, lalu melangkah {b} kali ke kanan karena yang ditambahkan positif.")
    elif b < 0:
        st.write(f"Mulai dari {fmt(a)}, lalu melangkah {abs(b)} kali ke kiri karena yang ditambahkan negatif.")
    else:
        st.write("Ditambah nol, posisinya tidak bergeser.")


# ---------- 5. Mengurangi ----------

elif menu == "Mengurangi":
    st.header("Pengurangan")
    catatan("Mengurangi sama dengan menambah <b>lawannya</b>.<br>"
            "Contoh: 5 \u2212 2 = 5 + (\u22122), dan 5 \u2212 (\u22122) = 5 + 2.")

    a = st.slider("Mulai dari", -10, 10, 2)
    b = st.slider("Dikurangi dengan", -10, 10, -4)
    lawan = -b
    hasil = a - b

    lo, hi = rentang(a, hasil)
    panah = [(0, a, ABU)]
    if lawan != 0:
        panah.append((a, hasil, BIRU if lawan > 0 else MERAH))
    garis_bilangan(lo, hi, [(a, TINTA, "mulai"), (hasil, HIJAU, "hasil")], panah)

    st.subheader(f"{fmt(a)} \u2212 {kurung(b)} = {fmt(hasil)}")
    st.write(f"Lawan dari {fmt(b)} adalah {fmt(lawan)}, jadi soalnya bisa ditulis ulang:")
    st.markdown(f"**{fmt(a)} \u2212 {kurung(b)} = {fmt(a)} + {kurung(lawan)} = {fmt(hasil)}**")
    if lawan > 0:
        st.write(f"Karena menambah {lawan}, langkahnya ke kanan.")
    elif lawan < 0:
        st.write(f"Karena menambah {fmt(lawan)}, langkahnya ke kiri.")
    else:
        st.write("Dikurangi nol, posisinya tidak bergeser.")


# ---------- 6. Latihan ----------

else:
    st.header("Latihan soal")

    def soal_baru():
        a = random.randint(-9, 9)
        b = random.randint(-9, 9)
        op = random.choice(["+", "\u2212"])
        st.session_state.soal = {
            "a": a, "b": b, "op": op,
            "jawaban": a + b if op == "+" else a - b,
            "id": random.random(),
        }
        st.session_state.sudah_dicek = False

    def pembahasan(a, b, op):
        if op == "+":
            if b == 0:
                return "Menambah nol tidak mengubah apa-apa."
            arah = "kanan" if b > 0 else "kiri"
            return (f"Mulai dari {fmt(a)}, lalu melangkah {abs(b)} kali ke {arah}. "
                    f"Hasilnya {fmt(a + b)}.")
        return (f"Mengurangi {fmt(b)} sama dengan menambah lawannya, yaitu {fmt(-b)}. "
                f"Jadi {fmt(a)} \u2212 {kurung(b)} = {fmt(a)} + {kurung(-b)} = {fmt(a - b)}.")

    if "soal" not in st.session_state:
        st.session_state.benar = 0
        st.session_state.total = 0
        st.session_state.benar_kini = False
        soal_baru()

    s = st.session_state.soal
    st.subheader(f"{fmt(s['a'])} {s['op']} {kurung(s['b'])} = ?")

    jawab = st.number_input(
        "Jawabanmu",
        value=0,
        step=1,
        key=f"jawab_{s['id']}",
        disabled=st.session_state.sudah_dicek,
    )

    if not st.session_state.sudah_dicek:
        if st.button("Periksa jawaban"):
            st.session_state.total += 1
            st.session_state.sudah_dicek = True
            st.session_state.benar_kini = (jawab == s["jawaban"])
            if st.session_state.benar_kini:
                st.session_state.benar += 1
            st.rerun()
    else:
        if st.session_state.benar_kini:
            st.success(f"Benar, jawabannya {fmt(s['jawaban'])}.")
        else:
            st.error(f"Belum tepat. Jawaban yang benar adalah {fmt(s['jawaban'])}.")
        st.write(pembahasan(s["a"], s["b"], s["op"]))
        if st.button("Soal berikutnya"):
            soal_baru()
            st.rerun()

    st.caption(f"Benar {st.session_state.benar} dari {st.session_state.total} soal.")

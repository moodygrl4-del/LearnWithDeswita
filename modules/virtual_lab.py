import streamlit as st
import sqlite3
from datetime import datetime

def show():
    st.markdown('<div class="header-style">🔬 Lab Virtual</div>', unsafe_allow_html=True)
    role = st.session_state.role

    if role in ["guru", "admin"]:
        st.markdown('<div class="subheader-style">Upload Lab Virtual Baru</div>', unsafe_allow_html=True)
        # Tombol dengan icon plus
        if st.button("➕ Tambah Lab Virtual", key="upload_lab_btn"):
            st.session_state.show_upload_form = True

        if st.session_state.get("show_upload_form", False):
            with st.form("upload_lab_form"):
                title = st.text_input("Judul Lab Virtual")
                description = st.text_area("Deskripsi Lab Virtual")
                url_or_embed = st.text_area("Link atau Embed Code (misalnya iframe)")
                lab_date = st.date_input("Tanggal Lab Virtual", value=datetime.today())
                submitted = st.form_submit_button("Upload")

                if submitted and title and url_or_embed:
                    # Simpan ke database virtual_labs
                    conn = sqlite3.connect("data/lms.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO virtual_labs (title, description, url_or_embed, date)
                        VALUES (?, ?, ?, ?)
                    """, (title, description or "Tidak ada deskripsi", url_or_embed, lab_date.strftime("%Y-%m-%d")))
                    # Tambahkan ke schedule juga agar muncul di kalender
                    cursor.execute("""
                        INSERT INTO schedule (title, description, date, type)
                        VALUES (?, ?, ?, ?)
                    """, (title, description or "Tidak ada deskripsi", lab_date.strftime("%Y-%m-%d"), "lab"))
                    conn.commit()
                    conn.close()
                    st.success(f"Lab Virtual '{title}' berhasil ditambahkan!")
                    st.session_state.show_upload_form = False
                    st.rerun()

    st.markdown('<div class="subheader-style">Daftar Lab Virtual</div>', unsafe_allow_html=True)
    # Ambil daftar lab virtual dari database
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, url_or_embed FROM virtual_labs ORDER BY date DESC")
    labs = cursor.fetchall()
    conn.close()

    if labs:
        for lab_id, title, desc, embed_code in labs:
            with st.container():
                st.write(f"🧪 **{title}**")
                st.caption(f"📝 Deskripsi: {desc}")

                # Tampilkan embed jika bukan link biasa
                if embed_code.startswith('<iframe'):
                    st.components.v1.html(embed_code, height=400)
                elif embed_code.startswith('http'):
                    # Jika link, tampilkan sebagai link dan embed
                    st.markdown(f"[🔗 Buka Lab Virtual]({embed_code})")
                    # Optional: Tampilkan embed link (bisa di disable jika tidak aman)
                    # st.components.v1.iframe(embed_code, height=400)
                else:
                    st.write("Konten tidak dikenali.")

            if role in ["guru", "admin"]:
                # Tombol hapus
                if st.button("🗑️ Hapus", key=f"delete_lab_{lab_id}", use_container_width=True):
                    # Hapus dari database virtual_labs dan schedule
                    conn = sqlite3.connect("data/lms.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM virtual_labs WHERE id = ?", (lab_id,))
                    cursor.execute("DELETE FROM schedule WHERE title = ?", (title,))
                    conn.commit()
                    conn.close()
                    st.success(f"Lab Virtual '{title}' berhasil dihapus.")
                    st.rerun()
            st.divider()
    else:
        st.info("Belum ada lab virtual yang diupload.")

    # Tombol kembali dan logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Kelas", key="back_to_class_lab", use_container_width=True):
            st.session_state.current_page = "kelas"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout_lab", use_container_width=True):
            # Hapus session login
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.name = None
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()


import streamlit as st
import os
import sqlite3
from datetime import datetime

# Pastikan folder materials ada
os.makedirs("data/materials", exist_ok=True)

def show():
    st.header("📚 Materi")
    role = st.session_state.role
    current_user = st.session_state.name

    if role in ["guru", "admin"]:
        st.subheader("Upload Materi Baru")
        # Tombol dengan icon plus
        if st.button("➕ Upload Materi Baru", key="upload_material_btn"):
            st.session_state.show_upload_form = True

        if st.session_state.get("show_upload_form", False):
            with st.form("upload_material_form"):
                uploaded_file = st.file_uploader("Pilih file", type=["pdf", "docx", "pptx", "mp4", "jpg", "jpeg", "png", "mp3", "wav"])
                material_date = st.date_input("Tanggal Materi", value=datetime.today())
                description = st.text_area("Deskripsi Materi")
                link_or_embed = st.text_area("Link atau Embed Code (misalnya iframe)")
                submitted = st.form_submit_button("Upload")

                if submitted and (uploaded_file or link_or_embed):
                    if uploaded_file:
                        save_path = f"data/materials/{uploaded_file.name}"
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        # Simpan ke database schedule
                        conn = sqlite3.connect("data/lms.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO schedule (title, description, date, type)
                            VALUES (?, ?, ?, ?)
                        """, (uploaded_file.name, description or "Tidak ada deskripsi", material_date.strftime("%Y-%m-%d"), "material"))
                        # Simpan juga ke tabel materials
                        cursor.execute("""
                            INSERT INTO materials (title, description, link_or_embed, date)
                            VALUES (?, ?, ?, ?)
                        """, (uploaded_file.name, description or "Tidak ada deskripsi", link_or_embed or "Tidak ada link/embed", material_date.strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success(f"File {uploaded_file.name} berhasil diupload!")
                        st.session_state.show_upload_form = False
                        st.rerun()
                    elif link_or_embed:
                        # Simpan link/embed ke database materials
                        conn = sqlite3.connect("data/lms.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO materials (title, description, link_or_embed, date)
                            VALUES (?, ?, ?, ?)
                        """, ("Materi Eksternal", description or "Tidak ada deskripsi", link_or_embed, material_date.strftime("%Y-%m-%d")))
                        # Simpan juga ke schedule
                        cursor.execute("""
                            INSERT INTO schedule (title, description, date, type)
                            VALUES (?, ?, ?, ?)
                        """, ("Materi Eksternal", description or "Tidak ada deskripsi", material_date.strftime("%Y-%m-%d"), "material"))
                        conn.commit()
                        conn.close()
                        st.success("Link/embed materi eksternal berhasil disimpan!")
                        st.session_state.show_upload_form = False
                        st.rerun()
                elif submitted:
                    st.error("Mohon upload file atau masukkan link/embed code.")

    st.subheader("Daftar Materi")
    files = os.listdir("data/materials/") if os.path.exists("data/materials/") else []
    if files:
        conn = sqlite3.connect("data/lms.db")
        cursor = conn.cursor()
        for f in files:
            # Ambil deskripsi dari database
            cursor.execute("SELECT description FROM schedule WHERE title = ? AND type = 'material'", (f,))
            result = cursor.fetchone()
            desc = result[0] if result else "Tidak ada deskripsi"

            # Tampilkan card modern
            st.markdown(f'''
                <div class="file-list-item-modern">
                    <div class="file-list-item-modern-title">📄 {f}</div>
                    <div class="file-list-item-modern-desc">📝 Deskripsi: {desc}</div>
                </div>
            ''', unsafe_allow_html=True)

            # Preview file jika format didukung
            file_path = f"data/materials/{f}"
            file_ext = f.split('.')[-1].lower()

            if file_ext in ['jpg', 'jpeg', 'png']:
                st.image(file_path, caption=f"Preview {f}", use_column_width=True)
            elif file_ext == 'pdf':
                # Untuk PDF, tampilkan link download karena streamlit tidak bisa embed PDF
                st.markdown(f"[📄 Lihat PDF]({file_path})")
            elif file_ext in ['mp4', 'mov', 'avi']:
                st.video(file_path)
            elif file_ext in ['mp3', 'wav']:
                st.audio(file_path)

            # Tombol download dan hapus
            col1, col2 = st.columns(2)
            with col1:
                # Tombol download
                with open(file_path, "rb") as file:
                    btn = st.download_button(
                        label="⬇️ Download",
                        data=file,
                        file_name=f,
                        mime="application/octet-stream",
                        key=f"download_{f}",
                        use_container_width=True
                    )
            if role in ["guru", "admin"]:
                with col2:
                    # Tombol hapus
                    if st.button("🗑️ Hapus", key=f"delete_{f}", use_container_width=True):
                        # Hapus file
                        os.remove(f"data/materials/{f}")
                        # Hapus dari database
                        cursor.execute("DELETE FROM schedule WHERE title = ? AND type = 'material'", (f,))
                        cursor.execute("DELETE FROM materials WHERE title = ?", (f,))
                        conn.commit()
                        st.success(f"Materi '{f}' berhasil dihapus.")
                        st.rerun()
        conn.close()
    else:
        st.info("Belum ada materi yang diupload.")

    # Tampilkan materi eksternal (YouTube, dll)
    st.subheader("Materi Eksternal")
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, description, link_or_embed FROM materials WHERE link_or_embed != 'Tidak ada link/embed' ORDER BY date DESC")
    external_materials = cursor.fetchall()
    conn.close()

    if external_materials:
        for title, desc, link_or_embed in external_materials:
            st.write(f"**{title}**")
            st.caption(f"📝 Deskripsi: {desc}")

            # Cek apakah link adalah YouTube
            if "youtube.com/watch" in link_or_embed or "youtu.be/" in link_or_embed:
                # Ekstrak ID video YouTube
                if "youtube.com/watch" in link_or_embed:
                    video_id = link_or_embed.split("v=")[1].split("&")[0]
                elif "youtu.be/" in link_or_embed:
                    video_id = link_or_embed.split("/")[-1].split("?")[0]
                else:
                    video_id = None

                if video_id:
                    # Embed video YouTube langsung di Streamlit
                    st.video(f"https://www.youtube.com/watch?v={video_id}")
                else:
                    st.error("❌ Link YouTube tidak valid.")
            elif link_or_embed.startswith('<iframe'):
                # Jika embed code, tampilkan dengan iframe
                st.components.v1.html(link_or_embed, height=400)
            else:
                # Jika link biasa, tampilkan sebagai link
                st.markdown(f"[🔗 Buka Link]({link_or_embed})")
    else:
        st.info("Belum ada materi eksternal yang diupload.")

    # Tombol kembali dan logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Kelas", key="back_to_class_materials", use_container_width=True):
            st.session_state.current_page = "kelas"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout_materials", use_container_width=True):
            # Hapus session login
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.name = None
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()

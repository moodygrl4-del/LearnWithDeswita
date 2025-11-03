import streamlit as st
import os
import sqlite3
from datetime import datetime

def show_kelas():
    st.header("🏫 Kelas Saya")
    role = st.session_state.role
    current_user = st.session_state.name

    st.write(f"Selamat datang di kelas, **{current_user}**!")
    st.info(f"Kamu masuk sebagai **{role}**.")

    # Cek apakah sudah ada kelas aktif
    if 'active_class' in st.session_state:
        # Tampilkan nama kelas
        conn = sqlite3.connect("data/lms.db")
        cursor = conn.cursor()
        cursor.execute("SELECT class_name FROM classes WHERE id = ?", (st.session_state.active_class,))
        class_result = cursor.fetchone()
        conn.close()
        
        if class_result:
            class_name = class_result[0]
            st.success(f"✅ Anda berada di kelas: **{class_name}**")
        else:
            # Kelas tidak ditemukan, hapus session
            del st.session_state['active_class']
            st.rerun()
    else:
        # Arahkan ke pemilihan kelas
        st.info("Silakan pilih atau buat kelas terlebih dahulu.")
        if st.button("↗️ Pilih Kelas", use_container_width=True):
            st.session_state.current_page = "class_selection"
            st.rerun()
        return

    if st.button("🏠 Buka Dashboard", use_container_width=True):
        st.session_state.current_page = "dashboard"
        st.rerun()

def show_dashboard():
    st.markdown('<h2 class="dashboard-header">🏠 Dashboard</h2>', unsafe_allow_html=True)
    role = st.session_state.role
    current_user = st.session_state.name

    # Cek apakah sudah ada kelas aktif
    if 'active_class' not in st.session_state:
        # Arahkan ke pemilihan kelas
        st.info("Silakan pilih kelas terlebih dahulu.")
        if st.button("↗️ Pilih Kelas", use_container_width=True):
            st.session_state.current_page = "class_selection"
            st.rerun()
        return

    # Tampilkan nama kelas aktif
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT class_name FROM classes WHERE id = ?", (st.session_state.active_class,))
    class_result = cursor.fetchone()
    conn.close()
    
    if class_result:
        class_name = class_result[0]
        st.subheader(f"Dashboard untuk **{class_name}**", divider=True)
    else:
        # Kelas tidak ditemukan, hapus session
        del st.session_state['active_class']
        st.rerun()
        return

    # Pastikan folder kelas ada
    class_id = st.session_state.active_class
    class_folder = f"data/classes/{class_id}"
    os.makedirs(f"{class_folder}/videos", exist_ok=True)
    os.makedirs(f"{class_folder}/banners", exist_ok=True)
    os.makedirs(f"{class_folder}/materials", exist_ok=True)
    os.makedirs(f"{class_folder}/tasks", exist_ok=True)
    os.makedirs(f"{class_folder}/submissions", exist_ok=True)
    os.makedirs(f"{class_folder}/quizzes", exist_ok=True)

    # Inisialisasi database untuk deskripsi video
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            video_name TEXT NOT NULL,
            learning_outcomes TEXT,
            learning_objectives TEXT,
            greeting TEXT,
            FOREIGN KEY (class_id) REFERENCES classes(id)
        )
    """)
    conn.commit()
    conn.close()

    # Upload banner (hanya untuk guru/admin)
    if role in ["guru", "admin"]:
        with st.expander("🎨 Upload/Edit Banner LMS", expanded=False):
            st.markdown('<div class="banner-upload-form">', unsafe_allow_html=True)
            
            # Upload banner baru
            uploaded_banner = st.file_uploader("Pilih gambar banner (rekomendasi: 1200x300 px)", type=["jpg", "jpeg", "png"], key="banner_uploader")
            if uploaded_banner:
                banner_path = f"{class_folder}/banners/banner.jpg"
                with open(banner_path, "wb") as f:
                    f.write(uploaded_banner.getbuffer())
                st.success(f"Banner {uploaded_banner.name} berhasil diupload!")
                st.rerun()

            # Tombol hapus banner
            banner_files = os.listdir(f"{class_folder}/banners/") if os.path.exists(f"{class_folder}/banners/") else []
            if banner_files:
                if st.button("🗑️ Hapus Banner", key="delete_banner_btn", use_container_width=True):
                    os.remove(f"{class_folder}/banners/{banner_files[0]}")
                    st.success("Banner berhasil dihapus.")
                    st.rerun()
                    
            st.markdown('</div>', unsafe_allow_html=True)

    # Tampilkan banner jika ada
    banner_files = os.listdir(f"{class_folder}/banners/") if os.path.exists(f"{class_folder}/banners/") else []
    if banner_files:
        banner_filename = banner_files[0]
        banner_path = f"{class_folder}/banners/{banner_filename}"
        
        # Periksa apakah file banner benar-benar ada
        if os.path.exists(banner_path):
            # Gunakan st.image untuk menampilkan banner (dengan parameter yang benar)
            st.image(banner_path, caption="Banner LMS", use_container_width=True)
        else:
            st.error(f"❌ File banner '{banner_filename}' tidak ditemukan. Silakan upload ulang.")
            # Tombol hapus file yang rusak
            if role in ["guru", "admin"]:
                if st.button("🗑️ Hapus Entri Rusak", key="delete_broken_banner", use_container_width=True):
                    # Hapus file (jika ada) dan abaikan error
                    try:
                        os.remove(banner_path)
                    except:
                        pass
                    st.success("Entri banner rusak berhasil dihapus.")
                    st.rerun()
    else:
        st.info("Belum ada banner yang diupload.")

    # Upload video apersepsi (hanya untuk guru/admin)
    if role in ["guru", "admin"]:
        with st.expander("🎥 Upload/Edit Video Apersepsi", expanded=False):
            uploaded_video = st.file_uploader("Pilih video", type=["mp4", "mov", "avi"], key="video_apresiasi")
            if uploaded_video:
                video_path = f"{class_folder}/videos/{uploaded_video.name}"
                with open(video_path, "wb") as f:
                    f.write(uploaded_video.getbuffer())
                st.success(f"Video {uploaded_video.name} berhasil diupload!")
                st.rerun()

    # Tampilkan video apersepsi dan deskripsi
    video_files = os.listdir(f"{class_folder}/videos/") if os.path.exists(f"{class_folder}/videos/") else []
    if video_files:
        video_filename = video_files[0]
        video_path = f"{class_folder}/videos/{video_filename}"
        
        # Periksa apakah file video benar-benar ada
        if os.path.exists(video_path):
            # Tampilkan video apersepsi dulu
            st.markdown('<div class="video-apresiasi-container">', unsafe_allow_html=True)
            
            # Tombol edit dan hapus video (hanya untuk guru/admin)
            if role in ["guru", "admin"]:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit Video", key="edit_video_btn", use_container_width=True):
                        st.session_state.show_edit_video_form = True
                with col2:
                    if st.button("🗑️ Hapus Video", key="delete_video_btn", use_container_width=True):
                        os.remove(video_path)
                        # Hapus juga deskripsi video
                        conn = sqlite3.connect("data/lms.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM video_descriptions WHERE class_id = ? AND video_name = ?", (class_id, video_filename))
                        conn.commit()
                        conn.close()
                        st.success("Video apersepsi berhasil dihapus.")
                        st.rerun()
            
            st.markdown('<div class="video-apresiasi-title">📺 Video Apersepsi</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="video-apresiasi-player">', unsafe_allow_html=True)
            st.video(video_path)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Ambil atau buat deskripsi video
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            cursor.execute("SELECT learning_outcomes, learning_objectives, greeting FROM video_descriptions WHERE class_id = ? AND video_name = ?", (class_id, video_filename))
            result = cursor.fetchone()
            conn.close()

            # Default values
            default_outcomes = "Mahasiswa dapat memahami konsep dasar materi yang dipelajari.\nMahasiswa mampu menganalisis informasi dan menerapkannya dalam konteks nyata.\nMahasiswa dapat berpikir kritis dan kreatif dalam menyelesaikan masalah."
            default_objectives = "Memahami prinsip-prinsip dasar materi.\nMengembangkan keterampilan analitis dan pemecahan masalah.\nMeningkatkan kemampuan berpikir kritis dan kolaborasi."
            default_greeting = "Selamat datang di pembelajaran hari ini! Video apersepsi ini akan memberimu gambaran awal tentang materi yang akan kita pelajari. Harapannya, kamu bisa lebih siap dan antusias dalam mengikuti kegiatan pembelajaran. Mari kita mulai perjalanan belajar yang menyenangkan ini bersama-sama!"

            if result:
                outcomes, objectives, greeting = result
            else:
                outcomes, objectives, greeting = default_outcomes, default_objectives, default_greeting

            # Form edit deskripsi (hanya untuk guru/admin)
            if role in ["guru", "admin"]:
                with st.expander("✏️ Edit Deskripsi Pembelajaran", expanded=False):
                    with st.form("edit_video_description"):
                        st.subheader("👋 Kata Sambutan")
                        new_greeting = st.text_area("Kata Sambutan", value=greeting, height=150)
                        st.subheader("🎯 Capaian Pembelajaran")
                        new_outcomes = st.text_area("Capaian Pembelajaran", value=outcomes, height=150)
                        st.subheader("🎯 Tujuan Pembelajaran")
                        new_objectives = st.text_area("Tujuan Pembelajaran", value=objectives, height=150)
                        
                        submitted = st.form_submit_button("💾 Simpan Deskripsi")
                        if submitted:
                            conn = sqlite3.connect("data/lms.db")
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM video_descriptions WHERE class_id = ? AND video_name = ?", (class_id, video_filename))
                            cursor.execute("""
                                INSERT INTO video_descriptions (class_id, video_name, learning_outcomes, learning_objectives, greeting)
                                VALUES (?, ?, ?, ?, ?)
                            """, (class_id, video_filename, new_outcomes, new_objectives, new_greeting))
                            conn.commit()
                            conn.close()
                            st.success("Deskripsi pembelajaran berhasil disimpan.")
                            st.rerun()

            # Tampilkan deskripsi pembelajaran dalam satu kolom besar (mirip gambar)
            st.markdown('<div class="learning-description-full">', unsafe_allow_html=True)

            # 1. Kata Sambutan
            st.markdown(f'''
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin-bottom: 20px; border-radius: 8px;">
                    <h3>👋 Kata Sambutan</h3>
                    <p>{greeting}</p>
                </div>
            ''', unsafe_allow_html=True)

            # 2. Capaian Pembelajaran
            st.markdown(f'''
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #ffc107; margin-bottom: 20px; border-radius: 8px;">
                    <h3>🎯 Capaian Pembelajaran</h3>
                    <ul>
            ''', unsafe_allow_html=True)
            for outcome in outcomes.split('\n'):
                if outcome.strip():
                    st.markdown(f'<li>{outcome.strip()}</li>', unsafe_allow_html=True)
            st.markdown('''
                    </ul>
                </div>
            ''', unsafe_allow_html=True)

            # 3. Tujuan Pembelajaran
            st.markdown(f'''
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #17a2b8; margin-bottom: 20px; border-radius: 8px;">
                    <h3>🎯 Tujuan Pembelajaran</h3>
                    <ul>
            ''', unsafe_allow_html=True)
            for objective in objectives.split('\n'):
                if objective.strip():
                    st.markdown(f'<li>{objective.strip()}</li>', unsafe_allow_html=True)
            st.markdown('''
                    </ul>
                </div>
            ''', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error(f"❌ File video '{video_filename}' tidak ditemukan. Silakan upload ulang.")
            # Tombol hapus file yang rusak
            if role in ["guru", "admin"]:
                if st.button("🗑️ Hapus Entri Rusak", key="delete_broken_video", use_container_width=True):
                    # Hapus dari database
                    conn = sqlite3.connect("data/lms.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM video_descriptions WHERE class_id = ? AND video_name = ?", (class_id, video_filename))
                    conn.commit()
                    conn.close()
                    st.success("Entri video rusak berhasil dihapus.")
                    st.rerun()
    else:
        st.info("Belum ada video apersepsi yang diupload.")

    # Mapping tombol ke halaman, sesuaikan dengan role
    menu = {
        "admin": [
            ("📅 Kalender", "calendar"),
            ("📋 Absensi", "attendance"),
            ("👥 Manajemen Pengguna", "users"),
            ("📚 Materi", "materials"),
            ("📝 Tugas", "tasks"),
            ("❓ Kuis", "quiz"),
            ("💬 Chat", "chat"),
            ("🔬 Lab Virtual", "virtual_lab"),
            ("📈 Progres Siswa", "progress")
        ],
        "guru": [
            ("📅 Kalender", "calendar"),
            ("📋 Absensi", "attendance"),
            ("📚 Materi", "materials"),
            ("📝 Tugas", "tasks"),
            ("❓ Kuis", "quiz"),
            ("💬 Chat", "chat"),
            ("🔬 Lab Virtual", "virtual_lab"),
            ("📈 Progres Siswa", "progress")
        ],
        "siswa": [
            ("📅 Kalender", "calendar"),
            ("📋 Absensi", "attendance"),
            ("📚 Materi", "materials"),
            ("📝 Tugas", "tasks"),
            ("❓ Kuis", "quiz"),
            ("💬 Chat", "chat"),
            ("🔬 Lab Virtual", "virtual_lab"),
            ("📈 Progres Saya", "progress")
        ]
    }

    # Tampilkan tombol-tombol besar dan modis dalam 2 kolom
    buttons = menu[role]
    cols = st.columns(2)

    for i, (label, page_key) in enumerate(buttons):
        col = cols[i % 2]
        if col.button(label, key=page_key, use_container_width=True):
            st.session_state.current_page = page_key
            st.rerun()

    # Tambahkan navigasi kembali ke kelas
    if st.button("🔙 Kembali ke Kelas", use_container_width=True):
        st.session_state.current_page = "kelas"
        st.rerun()

    # Tombol Logout di dashboard
    if st.button("🚪 Logout", use_container_width=True):
        # Hapus session login
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.name = None
        if 'current_page' in st.session_state:
            del st.session_state['current_page']
        if 'active_class' in st.session_state:
            del st.session_state['active_class']
        st.rerun()

    # Tampilkan halaman yang dipilih
    if 'current_page' in st.session_state:
        page = st.session_state.current_page
        if page == "calendar":
            from modules import calendar
            calendar.show()
        elif page == "materials":
            from modules import materials
            materials.show()
        elif page == "tasks":
            from modules import tasks
            tasks.show()
        elif page == "quiz":
            from modules import quiz
            quiz.show()
        elif page == "chat":
            from modules import chat
            chat.show()
        elif page == "virtual_lab":
            from modules import virtual_lab
            virtual_lab.show()
        elif page == "progress":
            from modules import progress
            progress.show()
        elif page == "users" and role == "admin":
            st.write("Fitur manajemen pengguna (akan ditambahkan nanti).")
        elif page == "attendance":
            from modules import attendance
            attendance.show()

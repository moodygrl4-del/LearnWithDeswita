import streamlit as st
import os
import sqlite3
from datetime import datetime, timedelta
import json

# Pastikan folder materials ada
os.makedirs("data/materials", exist_ok=True)

def show():
    st.header("📚 Materi")
    role = st.session_state.role
    current_user = st.session_state.name

    # Cek status alur pembelajaran siswa
    if role == "siswa":
        learning_status = get_learning_status(current_user)
        
        # Status:
        # 0: Belum mengerjakan pretest
        # 1: Sudah pretest, belum baca materi
        # 2: Sudah baca materi, belum posttest
        # 3: Sudah posttest
        
        if learning_status == 0:
            # Arahkan ke pretest
            show_pretest(current_user)
        elif learning_status == 1:
            # Arahkan ke materi
            show_material(current_user)
        elif learning_status == 2:
            # Arahkan ke posttest
            show_posttest(current_user)
        else:
            # Semua selesai
            st.success("🎉 Selamat! Kamu telah menyelesaikan semua tahap pembelajaran.")
            show_material_results(current_user)
    else:
        # Tampilan untuk guru/admin
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

                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"📄 [{f}](data/materials/{f})")
                    st.caption(f"📝 Deskripsi: {desc}")

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

                if role in ["guru", "admin"]:
                    with col2:
                        # Tombol download
                        with open(file_path, "rb") as file:
                            btn = st.download_button(
                                label="⬇️",
                                data=file,
                                file_name=f,
                                mime="application/octet-stream",
                                key=f"download_{f}",
                                use_container_width=True
                            )
                        # Tombol hapus
                        if st.button("🗑️", key=f"delete_{f}", use_container_width=True):
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

def get_learning_status(user):
    """
    Cek status pembelajaran siswa:
    0: Belum mengerjakan pretest
    1: Sudah pretest, belum baca materi
    2: Sudah baca materi, belum posttest
    3: Sudah posttest
    """
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    
    # Cek apakah sudah mengerjakan pretest
    cursor.execute("""
        SELECT COUNT(*) FROM quiz_submissions
        WHERE student_name = ? AND quiz_type = 'pretest'
    """, (user,))
    pretest_done = cursor.fetchone()[0] > 0
    
    # Cek apakah sudah mengerjakan posttest
    cursor.execute("""
        SELECT COUNT(*) FROM quiz_submissions
        WHERE student_name = ? AND quiz_type = 'posttest'
    """, (user,))
    posttest_done = cursor.fetchone()[0] > 0
    
    conn.close()
    
    if not pretest_done:
        return 0  # Belum pretest
    elif pretest_done and not posttest_done:
        # Cek apakah sudah membaca materi (simulasi dengan flag)
        if st.session_state.get(f"material_read_{user}", False):
            return 2  # Sudah baca materi, belum posttest
        else:
            return 1  # Sudah pretest, belum baca materi
    elif posttest_done:
        return 3  # Sudah posttest
    else:
        return 1  # Default ke tahap 1

def show_pretest(user):
    st.subheader("📋 Pretest")
    # Cek apakah sudah mengerjakan
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM quiz_submissions
        WHERE student_name = ? AND quiz_type = 'pretest'
    """, (user,))
    already_submitted = cursor.fetchone()[0] > 0
    conn.close()
    
    if already_submitted:
        st.success("✅ Kamu sudah mengerjakan pretest.")
        # Arahkan ke materi
        st.session_state[f"material_read_{user}"] = True
        st.rerun()
        return
    
    # Ambil soal pretest
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, question, options, question_type FROM quizzes
        WHERE quiz_type = 'pretest'
    """)
    questions = cursor.fetchall()
    conn.close()
    
    if not questions:
        st.info("Belum ada soal pretest.")
        return
    
    # Timer 5 menit
    if 'pretest_start_time' not in st.session_state:
        st.session_state.pretest_start_time = datetime.now()
    
    start_time = st.session_state.pretest_start_time
    elapsed = datetime.now() - start_time
    time_limit = timedelta(minutes=5)
    
    if elapsed > time_limit:
        st.warning("Waktu pretest habis!")
        # Submit jawaban kosong
        submit_empty_answers(user, "pretest", questions)
        st.session_state[f"material_read_{user}"] = True
        st.rerun()
        return
    
    time_left = time_limit - elapsed
    st.info(f"⏰ Waktu tersisa: {time_left.seconds // 60} menit {time_left.seconds % 60} detik")
    st.progress(1 - (elapsed / time_limit))
    
    # Form pretest
    with st.form("pretest_form"):
        answers = {}
        for q_id, question, options_str, q_type in questions:
            options = json.loads(options_str) if options_str else None
            st.subheader(f"Soal: {question}")
            if q_type == "mcq":
                answer = st.radio("Pilih jawaban", options, key=f"pretest_{q_id}")
            else:
                answer = st.text_area("Jawaban Essay", key=f"pretest_{q_id}")
            answers[q_id] = answer
        
        submitted = st.form_submit_button("Kirim Jawaban")
        if submitted:
            # Simpan jawaban
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            for q_id, _, _, _ in questions:
                answer = answers.get(q_id, "")
                # Ambil jawaban benar untuk scoring
                cursor.execute("SELECT correct_answer FROM quizzes WHERE id = ?", (q_id,))
                correct_answer = cursor.fetchone()[0]
                score = 1 if answer == correct_answer else 0
                cursor.execute("""
                    INSERT INTO quiz_submissions (student_name, quiz_type, question_id, answer, score)
                    VALUES (?, ?, ?, ?, ?)
                """, (user, "pretest", q_id, answer, score))
            conn.commit()
            conn.close()
            st.success("Jawaban pretest berhasil dikirim!")
            # Arahkan ke materi
            st.session_state[f"material_read_{user}"] = True
            st.rerun()

def show_material(user):
    st.subheader("📚 Materi")
    # Tampilkan link/embed materi
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, description, link_or_embed FROM materials ORDER BY date DESC LIMIT 1")
    material = cursor.fetchone()
    conn.close()
    
    if material:
        title, desc, link_or_embed = material
        st.write(f"**{title}**")
        st.caption(f"📝 Deskripsi: {desc}")
        
        # Tampilkan link/embed
        if link_or_embed and link_or_embed != "Tidak ada link/embed":
            # Cek apakah link Google Drive
            if "drive.google.com/file/d/" in link_or_embed:
                # Ubah link Google Drive menjadi link embed
                try:
                    file_id = link_or_embed.split("/d/")[1].split("/")[0]
                    embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
                    st.components.v1.iframe(embed_url, height=600)
                except:
                    st.error("❌ Link Google Drive tidak valid.")
            elif link_or_embed.startswith('<iframe'):
                # Tampilkan embed code
                st.components.v1.html(link_or_embed, height=600)
            elif link_or_embed.startswith('http'):
                # Tampilkan link
                st.markdown(f"[🔗 Buka Materi]({link_or_embed})")
            else:
                st.info("Konten tidak dikenali.")
        else:
            st.info("Belum ada link/embed materi.")
        
        # Tombol sudah baca
        if st.button("✅ Sudah Baca", use_container_width=True):
            st.session_state.current_page = "materials"
            st.session_state.material_read = True
            st.rerun()
    else:
        st.info("Belum ada materi yang diupload.")

def show_posttest(user):
    st.subheader("📝 Posttest")
    # Cek apakah sudah mengerjakan
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM quiz_submissions
        WHERE student_name = ? AND quiz_type = 'posttest'
    """, (user,))
    already_submitted = cursor.fetchone()[0] > 0
    conn.close()
    
    if already_submitted:
        st.success("✅ Kamu sudah mengerjakan posttest.")
        st.rerun()
        return
    
    # Ambil soal posttest
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, question, options, question_type FROM quizzes
        WHERE quiz_type = 'posttest'
    """)
    questions = cursor.fetchall()
    conn.close()
    
    if not questions:
        st.info("Belum ada soal posttest.")
        return
    
    # Timer 5 menit
    if 'posttest_start_time' not in st.session_state:
        st.session_state.posttest_start_time = datetime.now()
    
    start_time = st.session_state.posttest_start_time
    elapsed = datetime.now() - start_time
    time_limit = timedelta(minutes=5)
    
    if elapsed > time_limit:
        st.warning("Waktu posttest habis!")
        # Submit jawaban kosong
        submit_empty_answers(user, "posttest", questions)
        st.rerun()
        return
    
    time_left = time_limit - elapsed
    st.info(f"⏰ Waktu tersisa: {time_left.seconds // 60} menit {time_left.seconds % 60} detik")
    st.progress(1 - (elapsed / time_limit))
    
    # Form posttest
    with st.form("posttest_form"):
        answers = {}
        for q_id, question, options_str, q_type in questions:
            options = json.loads(options_str) if options_str else None
            st.subheader(f"Soal: {question}")
            if q_type == "mcq":
                answer = st.radio("Pilih jawaban", options, key=f"posttest_{q_id}")
            else:
                answer = st.text_area("Jawaban Essay", key=f"posttest_{q_id}")
            answers[q_id] = answer
        
        submitted = st.form_submit_button("Kirim Jawaban")
        if submitted:
            # Simpan jawaban
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            for q_id, _, _, _ in questions:
                answer = answers.get(q_id, "")
                # Ambil jawaban benar untuk scoring
                cursor.execute("SELECT correct_answer FROM quizzes WHERE id = ?", (q_id,))
                correct_answer = cursor.fetchone()[0]
                score = 1 if answer == correct_answer else 0
                cursor.execute("""
                    INSERT INTO quiz_submissions (student_name, quiz_type, question_id, answer, score)
                    VALUES (?, ?, ?, ?, ?)
                """, (user, "posttest", q_id, answer, score))
            conn.commit()
            conn.close()
            st.success("Jawaban posttest berhasil dikirim!")
            st.rerun()

def submit_empty_answers(user, quiz_type, questions):
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    for q_id, _, _, _ in questions:
        answer = ""
        score = 0
        cursor.execute("""
            INSERT INTO quiz_submissions (student_name, quiz_type, question_id, answer, score)
            VALUES (?, ?, ?, ?, ?)
        """, (user, quiz_type, q_id, answer, score))
    conn.commit()
    conn.close()

def show_material_results(user):
    st.subheader("📊 Hasil Pembelajaran")
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    
    # Ambil skor pretest
    cursor.execute("""
        SELECT SUM(score) FROM quiz_submissions
        WHERE student_name = ? AND quiz_type = 'pretest'
    """, (user,))
    pretest_score = cursor.fetchone()[0]
    
    # Ambil skor posttest
    cursor.execute("""
        SELECT SUM(score) FROM quiz_submissions
        WHERE student_name = ? AND quiz_type = 'posttest'
    """, (user,))
    posttest_score = cursor.fetchone()[0]
    
    conn.close()
    
    if pretest_score is not None and posttest_score is not None:
        st.write(f"**Pretest**: {pretest_score}/100")
        st.write(f"**Posttest**: {posttest_score}/100")
        improvement = posttest_score - pretest_score
        st.write(f"**Peningkatan**: {improvement}/100")
        if improvement > 0:
            st.success(f"🎉 Kamu mengalami peningkatan sebesar {improvement} poin!")
        elif improvement < 0:
            st.warning(f"📉 Kamu mengalami penurunan sebesar {abs(improvement)} poin.")
        else:
            st.info("🔄 Tidak ada perubahan skor.")
    else:
        st.info("Belum ada hasil pembelajaran.")



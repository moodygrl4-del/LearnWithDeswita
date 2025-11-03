import streamlit as st
import os
import sqlite3
import json

def show():
    st.markdown(f'<div class="header-style">📈 Progres {"Siswa" if st.session_state.role == "guru" else "Saya"}</div>', unsafe_allow_html=True)
    role = st.session_state.role
    current_user = st.session_state.name

    if role == "guru":
        # Tampilkan progres semua siswa
        st.markdown('<div class="subheader-style">Daftar Siswa dan Progres Kuis</div>', unsafe_allow_html=True)
        conn = sqlite3.connect("data/lms.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE role = 'siswa'")
        students = cursor.fetchall()
        conn.close()

        if not students:
            st.info("Belum ada siswa.")
            # Tombol kembali dan logout
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔙 Kembali ke Kelas", key="back_to_class_progress_guru", use_container_width=True):
                    st.session_state.current_page = "kelas"
                    st.rerun()
            with col2:
                if st.button("🚪 Logout", key="logout_progress_guru", use_container_width=True):
                    # Hapus session login
                    st.session_state.logged_in = False
                    st.session_state.role = None
                    st.session_state.name = None
                    if 'current_page' in st.session_state:
                        del st.session_state['current_page']
                    st.rerun()
            return

        for (student_name,) in students:
            st.write(f"**Siswa: {student_name}**")
            # Tampilkan hasil kuis
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            quiz_types = ["pretest", "test", "posttest"]
            scores = []
            for q_type in quiz_types:
                cursor.execute("""
                    SELECT SUM(score) FROM quiz_submissions
                    WHERE student_name = ? AND quiz_type = ?
                """, (student_name, q_type))
                total_score = cursor.fetchone()[0]
                if total_score is not None:
                    cursor.execute("""
                        SELECT COUNT(*) FROM quizzes WHERE quiz_type = ?
                    """, (q_type,))
                    total_questions = cursor.fetchone()[0]
                    # Hitung skor dalam skala 1-100
                    score_scaled = round((total_score / total_questions) * 100) if total_questions > 0 else 0
                    st.write(f"- {q_type.upper()}: {score_scaled}/100")
                    scores.append(score_scaled)
                else:
                    st.write(f"- {q_type.upper()}: Belum dikerjakan")
                    scores.append(0)
            conn.close()
            # Tampilkan grafik
            if any(scores):
                st.bar_chart(
                    data={
                        "Pretest": scores[0],
                        "Test": scores[1],
                        "Posttest": scores[2]
                    }
                )
            # Tampilkan riwayat absen
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            cursor.execute("SELECT title, date, status FROM attendance WHERE student_name = ?", (student_name,))
            attendance_records = cursor.fetchall()
            conn.close()
            if attendance_records:
                st.write(f"**Riwayat Absen {student_name}:**")
                for title, date, status in attendance_records:
                    if status == "hadir":
                        st.success(f"✅ {title} ({date}) - {status}")
                    elif status == "tidak hadir":
                        st.error(f"❌ {title} ({date}) - {status}")
                    else:
                        st.info(f"ℹ️ {title} ({date}) - {status}")
            else:
                st.info(f"Belum ada riwayat absen untuk {student_name}.")
            st.divider()

    else:  # role == "siswa"
        # Tampilkan progres siswa saat ini
        st.markdown(f'<div class="subheader-style">Progres untuk {current_user}</div>', unsafe_allow_html=True)
        task_files = os.listdir("data/tasks/") if os.path.exists("data/tasks/") else []
        if not task_files:
            st.info("Belum ada tugas yang diupload.")
        else:
            total_tasks = len(task_files)
            completed_tasks = 0
            for task in task_files:
                submissions = [f for f in os.listdir("data/submissions/") if task in f and current_user in f] if os.path.exists("data/submissions/") else []
                if submissions:
                    completed_tasks += 1

            progress_percent = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            st.progress(progress_percent / 100)
            st.write(f"Kamu telah menyelesaikan **{completed_tasks} dari {total_tasks}** tugas.")

        # Tampilkan hasil kuis
        st.markdown('<div class="subheader-style">📊 Hasil Kuis</div>', unsafe_allow_html=True)
        conn = sqlite3.connect("data/lms.db")
        cursor = conn.cursor()
        quiz_types = ["pretest", "test", "posttest"]
        scores = []
        for q_type in quiz_types:
            cursor.execute("""
                SELECT SUM(score) FROM quiz_submissions
                WHERE student_name = ? AND quiz_type = ?
            """, (current_user, q_type))
            total_score = cursor.fetchone()[0]
            if total_score is not None:
                cursor.execute("""
                    SELECT COUNT(*) FROM quizzes WHERE quiz_type = ?
                """, (q_type,))
                total_questions = cursor.fetchone()[0]
                # Hitung skor dalam skala 1-100
                score_scaled = round((total_score / total_questions) * 100) if total_questions > 0 else 0
                st.write(f"**{q_type.upper()}**: {score_scaled}/100")
                scores.append(score_scaled)
            else:
                st.write(f"**{q_type.upper()}**: Belum dikerjakan")
                scores.append(0)
        conn.close()
        # Tampilkan grafik
        if any(scores):
            st.bar_chart(
                data={
                    "Pretest": scores[0],
                    "Test": scores[1],
                    "Posttest": scores[2]
                }
            )
        # Tampilkan riwayat absen
        st.markdown('<div class="subheader-style">📋 Riwayat Absen</div>', unsafe_allow_html=True)
        conn = sqlite3.connect("data/lms.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, date, status FROM attendance WHERE student_name = ?", (current_user,))
        attendance_records = cursor.fetchall()
        conn.close()
        if attendance_records:
            for title, date, status in attendance_records:
                if status == "hadir":
                    st.success(f"✅ {title} ({date}) - {status}")
                elif status == "tidak hadir":
                    st.error(f"❌ {title} ({date}) - {status}")
                else:
                    st.info(f"ℹ️ {title} ({date}) - {status}")
        else:
            st.info("Belum ada riwayat absen.")

    # Tombol kembali dan logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Kelas", key="back_to_class_progress", use_container_width=True):
            st.session_state.current_page = "kelas"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout_progress", use_container_width=True):
            # Hapus session login
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.name = None
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()

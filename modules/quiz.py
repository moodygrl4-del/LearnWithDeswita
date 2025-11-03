import streamlit as st
import sqlite3
import json
import time
from datetime import datetime, timedelta

def show():
    st.header("📝 Kuis")
    role = st.session_state.role
    current_user = st.session_state.name

    if role in ["guru", "admin"]:
        st.subheader("Buat Kuis Baru")
        quiz_type = st.selectbox("Pilih Jenis Kuis", ["pretest", "test", "posttest"])
        question_count = st.number_input("Jumlah Soal (maks 10)", min_value=1, max_value=10, value=1)

        if st.button(f"➕ Buat Kuis {quiz_type.upper()}", key="create_quiz_btn"):
            st.session_state.current_quiz_type = quiz_type
            st.session_state.question_count = question_count
            st.session_state.questions_created = 0
            st.session_state.quiz_form_active = True

        if st.session_state.get("quiz_form_active", False):
            current_q_count = st.session_state.question_count
            current_q_num = st.session_state.questions_created
            if current_q_num < current_q_count:
                st.subheader(f"Soal {current_q_num + 1}")
                with st.form(f"quiz_q{current_q_num}_form"):
                    question = st.text_area("Pertanyaan")
                    q_type = st.radio("Jenis Soal", ["Pilihan Ganda (MCQ)", "Essay"])
                    if q_type == "Pilihan Ganda (MCQ)":
                        opt1 = st.text_input("Pilihan A")
                        opt2 = st.text_input("Pilihan B")
                        opt3 = st.text_input("Pilihan C")
                        opt4 = st.text_input("Pilihan D")
                        correct = st.selectbox("Jawaban Benar", ["A", "B", "C", "D"])
                        options = [opt1, opt2, opt3, opt4]
                        correct_answer = options[["A", "B", "C", "D"].index(correct)]
                    else:
                        correct_answer = st.text_input("Jawaban Benar (untuk koreksi manual)")
                        options = None

                    submitted = st.form_submit_button("Simpan Soal")
                    if submitted and question and correct_answer:
                        # Simpan ke database
                        conn = sqlite3.connect("data/lms.db")
                        cursor = conn.cursor()
                        opt_json = json.dumps(options) if options else None
                        cursor.execute("""
                            INSERT INTO quizzes (quiz_type, question, options, correct_answer, question_type, time_limit)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (st.session_state.current_quiz_type, question, opt_json, correct_answer, "mcq" if q_type == "Pilihan Ganda (MCQ)" else "essay", 15))
                        conn.commit()
                        conn.close()
                        st.success(f"Soal {current_q_num + 1} berhasil disimpan.")
                        st.session_state.questions_created += 1
                        if st.session_state.questions_created >= current_q_count:
                            st.session_state.quiz_form_active = False
                            st.rerun()
                        else:
                            st.rerun()
            else:
                st.success(f"Kuis {st.session_state.current_quiz_type.upper()} berhasil dibuat!")
                st.session_state.quiz_form_active = False
                st.rerun()

        # Tampilkan daftar soal dan tombol edit/hapus untuk guru
        st.subheader("Daftar Soal")
        conn = sqlite3.connect("data/lms.db")
        cursor = conn.cursor()
        for q_type in ["pretest", "test", "posttest"]:
            st.write(f"**{q_type.upper()}**")
            cursor.execute("""
                SELECT id, question, options, correct_answer, question_type FROM quizzes
                WHERE quiz_type = ?
            """, (q_type,))
            questions = cursor.fetchall()
            if questions:
                for q_id, question, options_str, correct_answer, q_type_db in questions:
                    options = json.loads(options_str) if options_str else None
                    with st.expander(f"Soal: {question}"):
                        st.write(f"**Jenis:** {q_type_db}")
                        st.write(f"**Pertanyaan:** {question}")
                        if q_type_db == "mcq":
                            st.write(f"**Pilihan:** {options}")
                            st.write(f"**Jawaban Benar:** {correct_answer}")
                        else:
                            st.write(f"**Jawaban Benar:** {correct_answer}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✏️ Edit", key=f"edit_{q_id}"):
                                st.session_state.editing_q_id = q_id
                                st.session_state.edit_question = question
                                st.session_state.edit_options = options
                                st.session_state.edit_correct = correct_answer
                                st.session_state.edit_q_type = q_type_db
                        with col2:
                            if st.button("🗑️ Hapus", key=f"delete_{q_id}"):
                                cursor.execute("DELETE FROM quizzes WHERE id = ?", (q_id,))
                                # Hapus juga jawaban terkait
                                cursor.execute("DELETE FROM quiz_submissions WHERE question_id = ?", (q_id,))
                                conn.commit()
                                st.success("Soal dihapus.")
                                st.rerun()
            else:
                st.info(f"Belum ada soal untuk {q_type.upper()}.")
        conn.close()

        # Form edit soal
        if st.session_state.get("editing_q_id"):
            st.subheader("Edit Soal")
            with st.form("edit_quiz_form"):
                edited_question = st.text_area("Pertanyaan", value=st.session_state.edit_question)
                edited_q_type = st.radio("Jenis Soal", ["Pilihan Ganda (MCQ)", "Essay"], index=0 if st.session_state.edit_q_type == "mcq" else 1)
                if edited_q_type == "Pilihan Ganda (MCQ)":
                    opt1 = st.text_input("Pilihan A", value=st.session_state.edit_options[0] if st.session_state.edit_options else "")
                    opt2 = st.text_input("Pilihan B", value=st.session_state.edit_options[1] if st.session_state.edit_options else "")
                    opt3 = st.text_input("Pilihan C", value=st.session_state.edit_options[2] if st.session_state.edit_options else "")
                    opt4 = st.text_input("Pilihan D", value=st.session_state.edit_options[3] if st.session_state.edit_options else "")
                    correct = st.selectbox("Jawaban Benar", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(st.session_state.edit_correct[0]) if st.session_state.edit_correct in ["A", "B", "C", "D"] else 0)
                    options = [opt1, opt2, opt3, opt4]
                    edited_correct_answer = options[["A", "B", "C", "D"].index(correct)]
                else:
                    edited_correct_answer = st.text_input("Jawaban Benar (untuk koreksi manual)", value=st.session_state.edit_correct)

                submitted = st.form_submit_button("Simpan Perubahan")
                if submitted:
                    conn = sqlite3.connect("data/lms.db")
                    cursor = conn.cursor()
                    opt_json = json.dumps(options) if edited_q_type == "Pilihan Ganda (MCQ)" else None
                    cursor.execute("""
                        UPDATE quizzes SET question = ?, options = ?, correct_answer = ?, question_type = ?
                        WHERE id = ?
                    """, (edited_question, opt_json, edited_correct_answer, "mcq" if edited_q_type == "Pilihan Ganda (MCQ)" else "essay", st.session_state.editing_q_id))
                    conn.commit()
                    conn.close()
                    st.success("Soal berhasil diupdate.")
                    del st.session_state["editing_q_id"]
                    del st.session_state["edit_question"]
                    del st.session_state["edit_options"]
                    del st.session_state["edit_correct"]
                    del st.session_state["edit_q_type"]
                    st.rerun()

    # Tampilan untuk siswa
    elif role == "siswa":
        # Cek status alur pembelajaran
        learning_status = get_learning_status(current_user)
        
        if learning_status == 0:
            # Tahap 1: Pretest
            show_pretest(current_user)
        elif learning_status == 1:
            # Tahap 2: Materi
            st.info("✅ Pretest selesai! Silakan baca materi terlebih dahulu.")
            if st.button("📖 Buka Materi", use_container_width=True):
                st.session_state.current_page = "materials"
                st.rerun()
        elif learning_status == 2:
            # Tahap 3: Posttest
            st.info("✅ Materi sudah dibaca! Silakan kerjakan posttest.")
            if st.button("❓ Kerjakan Posttest", use_container_width=True):
                st.session_state.current_page = "quiz"
                st.session_state.quiz_type_override = "posttest"
                st.rerun()
        else:
            # Semua selesai
            st.success("🎉 Selamat! Kamu telah menyelesaikan semua tahap pembelajaran.")
            show_quiz_results(current_user)

    # Tombol kembali dan logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Kelas", key="back_to_class_quiz"):
            st.session_state.current_page = "kelas"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout_quiz", use_container_width=True):
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
        # Cek apakah sudah membaca materi (dengan flag)
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
            for q_id, answer in answers.items():
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
            st.rerun()

def take_quiz():
    current_user = st.session_state.name
    quiz_type = st.session_state.current_quiz_type
    all_questions = st.session_state[f"quiz_question_list_{quiz_type}"]
    answers = st.session_state[f"quiz_answers_{quiz_type}"]
    current_q_index = st.session_state[f"current_question_index_{quiz_type}"]

    # Cek waktu
    start_time = st.session_state.get(f"quiz_start_time_{quiz_type}")
    if not start_time:
        st.error("Waktu kuis tidak valid.")
        st.session_state.quiz_active = False
        st.rerun()
        return

    elapsed = datetime.now() - start_time
    time_limit = timedelta(minutes=15)
    if elapsed > time_limit:
        st.warning("Waktu pengerjaan habis!")
        # Submit jawaban sebelum keluar
        submit_answers(quiz_type, current_user, all_questions, answers)
        st.session_state.quiz_active = False
        st.rerun()
        return

    time_left = time_limit - elapsed
    st.info(f"⏰ Waktu tersisa: {time_left.seconds // 60} menit {time_left.seconds % 60} detik")
    st.progress(1 - (elapsed / time_limit))

    # Tampilkan soal saat ini
    if current_q_index < len(all_questions):
        q_id, question, options_str, q_type_db = all_questions[current_q_index]
        options = json.loads(options_str) if options_str else None

        st.subheader(f"Soal {current_q_index + 1}: {question}")

        if q_type_db == "mcq":
            default = answers[q_id]
            answer = st.radio("Pilih jawaban", options, index=options.index(default) if default in options else 0, key=f"q_{q_id}")
        else:
            default = answers[q_id] or ""
            answer = st.text_area("Jawaban Essay", value=default, key=f"q_{q_id}")

        # Simpan jawaban ke session_state
        answers[q_id] = answer
        st.session_state[f"quiz_answers_{quiz_type}"] = answers

        # Tombol navigasi
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if current_q_index > 0:
                if st.button("Sebelumnya", key=f"prev_{q_id}"):
                    st.session_state[f"current_question_index_{quiz_type}"] -= 1
                    st.rerun()
        with col2:
            # Tombol untuk skip (langsung ke soal berikutnya)
            if current_q_index < len(all_questions) - 1:
                if st.button("Lanjut", key=f"next_{q_id}"):
                    st.session_state[f"current_question_index_{quiz_type}"] += 1
                    st.rerun()
            else:
                # Tombol selesai
                if st.button("Selesai", key="finish_quiz"):
                    submit_answers(quiz_type, current_user, all_questions, answers)
                    st.session_state.quiz_active = False
                    st.rerun()
        with col3:
            # Tombol untuk kembali ke daftar kuis (tanpa submit)
            if st.button("Kembali ke Daftar", key="back_to_list"):
                st.session_state.quiz_active = False
                st.rerun()

def submit_answers(quiz_type, user, questions, answers):
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    for q_id, _, _, _ in questions:
        answer = answers.get(q_id, "")
        # Ambil jawaban benar dari database untuk scoring
        cursor.execute("SELECT correct_answer FROM quizzes WHERE id = ?", (q_id,))
        correct_answer = cursor.fetchone()[0]
        score = 1 if answer == correct_answer else 0
        cursor.execute("""
            INSERT INTO quiz_submissions (student_name, quiz_type, question_id, answer, score)
            VALUES (?, ?, ?, ?, ?)
        """, (user, quiz_type, q_id, answer, score))
    conn.commit()
    conn.close()
    # Tambahkan ke kalender
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO schedule (title, description, date, type)
        VALUES (?, ?, ?, ?)
    """, (f"Kuis {quiz_type.upper()}", f"Siswa {user} telah mengerjakan kuis {quiz_type.upper()}", datetime.now().strftime("%Y-%m-%d"), "quiz"))
    conn.commit()
    conn.close()

def show_quiz_results(user):
    st.subheader("📊 Hasil Kuis")
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    quiz_types = ["pretest", "test", "posttest"]
    scores = []
    for q_type in quiz_types:
        cursor.execute("""
            SELECT SUM(score) FROM quiz_submissions
            WHERE student_name = ? AND quiz_type = ?
        """, (user, q_type))
        total_score = cursor.fetchone()[0]
        if total_score is not None:
            cursor.execute("""
                SELECT COUNT(*) FROM quizzes WHERE quiz_type = ?
            """, (q_type,))
            total_questions = cursor.fetchone()[0]
            # Hitung skor dalam skala 0-100
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
    # Tampilkan tabel hasil kuis
    st.subheader("📋 Detail Hasil Kuis")
    for q_type in quiz_types:
        st.write(f"**{q_type.upper()}**")
        conn = sqlite3.connect("data/lms.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.question, qs.answer, q.correct_answer
            FROM quizzes q
            JOIN quiz_submissions qs ON q.id = qs.question_id
            WHERE qs.student_name = ? AND qs.quiz_type = ?
        """, (user, q_type))
        results = cursor.fetchall()
        if results:
            # Buat tabel hasil kuis
            table_data = []
            for question, user_answer, correct_answer in results:
                if user_answer == correct_answer:
                    table_data.append([question, user_answer, correct_answer, "✅"])
                else:
                    table_data.append([question, user_answer, correct_answer, "❌"])
            # Tampilkan tabel hasil kuis
            st.table(table_data)
        else:
            st.info(f"Belum ada jawaban untuk {q_type.upper()}.")
        conn.close()


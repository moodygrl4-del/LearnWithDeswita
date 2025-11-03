import streamlit as st
import sqlite3
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta
import os

# Buat folder data jika belum ada
os.makedirs("data", exist_ok=True)

def init_db():
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()

    # Tabel users
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    table_exists = cursor.fetchone()

    if table_exists:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'name' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN name TEXT NOT NULL DEFAULT ''")
            st.warning("Kolom 'name' ditambahkan ke tabel users.")
    else:
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

    # Tabel schedule
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            type TEXT NOT NULL
        )
    """)

    # Tabel quizzes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quizzes';")
    quiz_table_exists = cursor.fetchone()
    if quiz_table_exists:
        # Cek apakah kolom time_limit sudah ada
        cursor.execute("PRAGMA table_info(quizzes)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'time_limit' not in columns:
            cursor.execute("ALTER TABLE quizzes ADD COLUMN time_limit INTEGER DEFAULT 15")
    else:
        cursor.execute("""
            CREATE TABLE quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_type TEXT NOT NULL, -- 'pretest', 'test', 'posttest'
                question TEXT NOT NULL,
                options TEXT, -- JSON string for MCQ options
                correct_answer TEXT NOT NULL,
                question_type TEXT NOT NULL, -- 'mcq', 'essay'
                time_limit INTEGER DEFAULT 15
            )
        """)

    # Tabel quiz_submissions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            quiz_type TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            FOREIGN KEY (question_id) REFERENCES quizzes(id)
        )
    """)

    # Tabel virtual_labs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS virtual_labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url_or_embed TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    # Tabel chat
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # Tabel attendance
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            student_name TEXT NOT NULL,
            status TEXT NOT NULL, -- 'hadir', 'tidak hadir', 'izin'
            FOREIGN KEY (student_name) REFERENCES users(username)
        )
    """)

    # === PERUBAHAN DI SINI ===
    # Tabel video_descriptions (dengan class_id)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_descriptions';")
    video_desc_table_exists = cursor.fetchone()
    if video_desc_table_exists:
        # Cek apakah kolom class_id sudah ada
        cursor.execute("PRAGMA table_info(video_descriptions)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'class_id' not in columns:
            # Hapus tabel lama dan buat baru dengan class_id
            cursor.execute("DROP TABLE video_descriptions")
            cursor.execute("""
                CREATE TABLE video_descriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER NOT NULL,
                    video_name TEXT NOT NULL,
                    learning_outcomes TEXT,
                    learning_objectives TEXT,
                    greeting TEXT,
                    FOREIGN KEY (class_id) REFERENCES classes(id)
                )
            """)
            st.warning("Tabel 'video_descriptions' diperbarui dengan kolom 'class_id'.")
    else:
        cursor.execute("""
            CREATE TABLE video_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                video_name TEXT NOT NULL,
                learning_outcomes TEXT,
                learning_objectives TEXT,
                greeting TEXT,
                FOREIGN KEY (class_id) REFERENCES classes(id)
            )
        """)

    # Tabel classes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            class_pin TEXT NOT NULL UNIQUE,
            teacher_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Tabel class_members
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            joined_at TEXT NOT NULL,
            FOREIGN KEY (class_id) REFERENCES classes(id)
        )
    """)

    # === TAMBAHKAN INI ===
    # Tabel materials
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            link_or_embed TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    # Hapus pesan lama (> 1 bulan) di chat
    one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM chat WHERE timestamp < ?", (one_month_ago,))

    # === PERUBAHAN DI SINI ===
    # Buat akun default (tambahkan akun guru baru dan semua akun lama)
    users_to_add = [
        # Admin
        ("Admin Utama", "admin@example.com", "admin", "admin123", "admin"),
        
        # Guru
        ("Guru Satu", "guru@example.com", "guru1", "guru123", "guru"),
        ("Deswita Ananda", "deswita@example.com", "deswita", "Deswita123", "guru"),  # Akun guru baru
        
        # Siswa (lama)
        ("Siswa Satu", "siswa@example.com", "siswa1", "siswa123", "siswa"),
        
        # Siswa (baru)
        ("Carissa Oktariani", "carissa@example.com", "carissa", "Carissa123", "siswa"),
        ("Kayyisah Putri", "kayyisah@example.com", "kayyisah", "Kayyisah123", "siswa"),
        ("Muhammad Fahri", "fahri@example.com", "fahri", "Fahri123", "siswa"),
        ("Dirgahayu Indah Kurnia", "dirgahayu@example.com", "dirgahayu", "Dirgahayu123", "siswa"),
        ("Muhammad Afrizal", "afrizal@example.com", "afrizal", "Afrizal123", "siswa"),
        ("Chayara Nuraulia", "chayara@example.com", "chayara", "Chayara123", "siswa"),
        ("Meyriska", "meyriska@example.com", "meyriska", "Meyriska123", "siswa"),
        ("Keyla Putri Kirana", "keyla@example.com", "keyla", "Keyla123", "siswa"),
        ("Anggie Niken Ramadhani", "niken@example.com", "niken", "Niken123", "siswa"),
        ("Deania Triwahyuni", "deani@example.com", "deani", "Deani123", "siswa"),
        ("Fahrani Mutia Khanza", "fahrani@example.com", "fahrani", "Fahrani123", "siswa"),
        ("Desita Putri Saimona", "desita@example.com", "desita", "Desita123", "siswa")
    ]

    for name, email, username, plain_password, role in users_to_add:
        try:
            hashed = pbkdf2_sha256.hash(plain_password)
            cursor.execute("""
                INSERT INTO users (name, email, username, password, role)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, username, hashed, role))
        except sqlite3.IntegrityError:
            pass  # Akun sudah ada

    conn.commit()
    conn.close()

def show_login():
    st.title("🔐 Login Sistem")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name, password, role FROM users WHERE username=?", (username,))
            user = cursor.fetchone()
            conn.close()

            if user and pbkdf2_sha256.verify(password, user[1]):
                st.session_state.logged_in = True
                st.session_state.name = user[0]
                st.session_state.role = user[2]
                st.success(f"Login berhasil sebagai {user[2]}!")
                if 'current_page' in st.session_state:
                    del st.session_state['current_page']
                st.rerun()
            else:
                st.error("Username atau password salah!")

init_db()
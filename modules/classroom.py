import streamlit as st
import sqlite3
import random
import string
from datetime import datetime
import os
import shutil

def show_create_class():
    st.header("➕ Buat Kelas Baru")
    with st.form("create_class_form"):
        class_name = st.text_input("Nama Kelas")
        # Input PIN manual
        class_pin = st.text_input("PIN Kelas (minimal 4 karakter, hanya angka/huruf)", max_chars=10)
        submitted = st.form_submit_button("Buat Kelas")
        
        if submitted and class_name and class_pin:
            # Validasi PIN
            if len(class_pin) < 4:
                st.error("PIN harus minimal 4 karakter.")
                return
            if not class_pin.isalnum():
                st.error("PIN hanya boleh mengandung angka dan huruf.")
                return
                
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO classes (class_name, class_pin, teacher_name, created_at)
                    VALUES (?, ?, ?, ?)
                """, (class_name, class_pin, st.session_state.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                class_id = cursor.lastrowid
                conn.commit()
                
                # Buat folder kelas
                class_folder = f"data/classes/{class_id}"
                os.makedirs(f"{class_folder}/videos", exist_ok=True)
                os.makedirs(f"{class_folder}/banners", exist_ok=True)
                os.makedirs(f"{class_folder}/materials", exist_ok=True)
                os.makedirs(f"{class_folder}/tasks", exist_ok=True)
                os.makedirs(f"{class_folder}/submissions", exist_ok=True)
                os.makedirs(f"{class_folder}/quizzes", exist_ok=True)
                
                st.success(f"Kelas '{class_name}' berhasil dibuat dengan PIN: `{class_pin}`")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("PIN sudah digunakan. Coba PIN lain.")
            conn.close()
        elif submitted:
            st.error("Mohon isi nama kelas dan PIN.")

def show_join_class():
    st.header("🔑 Gabung ke Kelas")
    with st.form("join_class_form"):
        class_pin = st.text_input("Masukkan PIN Kelas")
        submitted = st.form_submit_button("Gabung")
        
        if submitted and class_pin:
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, class_name FROM classes WHERE class_pin = ?", (class_pin,))
            result = cursor.fetchone()
            if result:
                class_id, class_name = result
                # Cek apakah sudah join
                cursor.execute("SELECT id FROM class_members WHERE class_id = ? AND student_name = ?", (class_id, st.session_state.name))
                if cursor.fetchone():
                    st.info(f"Kamu sudah bergabung ke kelas '{class_name}'.")
                else:
                    cursor.execute("""
                        INSERT INTO class_members (class_id, student_name, joined_at)
                        VALUES (?, ?, ?)
                    """, (class_id, st.session_state.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success(f"Berhasil bergabung ke kelas '{class_name}'!")
                    # Set kelas aktif
                    st.session_state.active_class = class_id
                    st.session_state.current_page = "dashboard"
                    st.rerun()
            else:
                st.error("PIN kelas tidak valid.")
            conn.close()

# ✅ Fungsi yang dipanggil di app.py
def show_class_selection():
    st.header("🏫 Pilih Kelas")
    role = st.session_state.role
    current_user = st.session_state.name
    
    if role == "guru":
        # Tampilkan kelas yang dibuat guru
        conn = sqlite3.connect("data/lms.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, class_name, class_pin FROM classes WHERE teacher_name = ?", (current_user,))
        classes = cursor.fetchall()
        conn.close()
        
        if classes:
            st.subheader("Kelas yang Anda Buat")
            for class_id, class_name, class_pin in classes:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                with col1:
                    st.write(f"**{class_name}**")
                with col2:
                    st.write(f"PIN: `{class_pin}`")
                with col3:
                    if st.button("↗️ Masuk", key=f"enter_{class_id}", use_container_width=True):
                        st.session_state.active_class = class_id
                        st.session_state.current_page = "dashboard"
                        st.rerun()
                with col4:
                    # Tombol hapus kelas
                    if st.button("🗑️ Hapus", key=f"delete_{class_id}", use_container_width=True):
                        # Konfirmasi hapus
                        st.session_state.confirm_delete_class = class_id
                        st.session_state.confirm_delete_class_name = class_name
                        st.rerun()
            
            # Konfirmasi hapus kelas
            if st.session_state.get("confirm_delete_class"):
                class_id_to_delete = st.session_state.confirm_delete_class
                class_name_to_delete = st.session_state.confirm_delete_class_name
                st.warning(f"⚠️ Anda yakin ingin menghapus kelas **{class_name_to_delete}**?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Ya, Hapus", key="confirm_delete_yes", use_container_width=True):
                        # Hapus kelas dan semua data terkait
                        conn = sqlite3.connect("data/lms.db")
                        cursor = conn.cursor()
                        # Hapus anggota kelas
                        cursor.execute("DELETE FROM class_members WHERE class_id = ?", (class_id_to_delete,))
                        # Hapus kelas
                        cursor.execute("DELETE FROM classes WHERE id = ?", (class_id_to_delete,))
                        conn.commit()
                        conn.close()
                        # Hapus folder kelas
                        class_folder = f"data/classes/{class_id_to_delete}"
                        if os.path.exists(class_folder):
                            shutil.rmtree(class_folder)
                        # Hapus session kelas aktif jika sedang aktif
                        if st.session_state.get("active_class") == class_id_to_delete:
                            del st.session_state["active_class"]
                        st.success(f"Kelas '{class_name_to_delete}' berhasil dihapus.")
                        del st.session_state["confirm_delete_class"]
                        del st.session_state["confirm_delete_class_name"]
                        st.rerun()
                with col2:
                    if st.button("❌ Batal", key="confirm_delete_no", use_container_width=True):
                        del st.session_state["confirm_delete_class"]
                        del st.session_state["confirm_delete_class_name"]
                        st.rerun()
        else:
            st.info("Anda belum membuat kelas.")
        
        # Tombol buat kelas baru
        if st.button("➕ Buat Kelas Baru", use_container_width=True):
            st.session_state.show_create_class = True
            
        if st.session_state.get("show_create_class", False):
            show_create_class()
    
    elif role == "siswa":
        # Tampilkan kelas yang sudah dijoin
        conn = sqlite3.connect("data/lms.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.class_name, c.class_pin
            FROM classes c
            JOIN class_members cm ON c.id = cm.class_id
            WHERE cm.student_name = ?
        """, (current_user,))
        joined_classes = cursor.fetchall()
        conn.close()
        
        if joined_classes:
            st.subheader("Kelas yang Anda Ikuti")
            for class_id, class_name, class_pin in joined_classes:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{class_name}**")
                with col2:
                    st.write(f"PIN: `{class_pin}`")
                with col3:
                    if st.button("↗️ Masuk", key=f"enter_{class_id}", use_container_width=True):
                        st.session_state.active_class = class_id
                        st.session_state.current_page = "dashboard"
                        st.rerun()
        else:
            st.info("Anda belum mengikuti kelas.")
        
        # Tombol gabung kelas
        if st.button("🔑 Gabung ke Kelas", use_container_width=True):
            st.session_state.show_join_class = True
            
        if st.session_state.get("show_join_class", False):
            show_join_class()

    # Tombol kembali dan logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Menu Utama", use_container_width=True):
            st.session_state.current_page = "main_menu"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            # Hapus session login
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.name = None
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()

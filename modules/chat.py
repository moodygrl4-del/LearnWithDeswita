import streamlit as st
import sqlite3
from datetime import datetime

def show():
    st.markdown('<div class="header-style">💬 Chat</div>', unsafe_allow_html=True)
    current_user = st.session_state.name
    current_role = st.session_state.role

    # Ambil daftar user berdasarkan role
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, role FROM users WHERE name != ?", (current_user,))
    users = cursor.fetchall()
    conn.close()

    # Filter user berdasarkan role
    if current_role == "admin":
        # Admin bisa chat dengan guru
        available_users = [u[0] for u in users if u[1] == "guru"]
    elif current_role == "guru":
        # Guru bisa chat dengan siswa
        available_users = [u[0] for u in users if u[1] == "siswa"]
    elif current_role == "siswa":
        # Siswa bisa chat dengan guru
        available_users = [u[0] for u in users if u[1] == "guru"]
    else:
        available_users = []

    if not available_users:
        st.info("Tidak ada pengguna yang bisa diajak chat.")
        # Tombol kembali dan logout
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔙 Kembali ke Kelas", key="back_to_class_chat", use_container_width=True):
                st.session_state.current_page = "kelas"
                st.rerun()
        with col2:
            if st.button("🚪 Logout", key="logout_chat", use_container_width=True):
                # Hapus session login
                st.session_state.logged_in = False
                st.session_state.role = None
                st.session_state.name = None
                if 'current_page' in st.session_state:
                    del st.session_state['current_page']
                st.rerun()
        return

    selected_user = st.selectbox("Pilih pengguna untuk diajak chat", available_users)

    # Ambil pesan antara dua user
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sender, message, timestamp FROM chat
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
        ORDER BY timestamp ASC
    """, (current_user, selected_user, selected_user, current_user))
    messages = cursor.fetchall()
    conn.close()

    # Tampilkan pesan dengan st.chat_message
    st.subheader(f"Obrolan dengan {selected_user}")
    if messages:
        for msg_id, sender, msg, time in messages:
            if sender == current_user:
                with st.chat_message("user"):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(msg)
                        st.caption(time)
                    with col2:
                        if st.button("🗑️", key=f"delete_msg_{msg_id}"):
                            # Hapus pesan dari database
                            conn = sqlite3.connect("data/lms.db")
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM chat WHERE id = ?", (msg_id,))
                            conn.commit()
                            conn.close()
                            st.success("Pesan dihapus.")
                            st.rerun()
            else:
                with st.chat_message("assistant"):
                    st.write(msg)
                    st.caption(time)
    else:
        st.info("Belum ada pesan.")

    # Input pesan di bawah
    with st.form("send_message_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            new_message = st.text_input("Ketik pesan kamu...", key="input_message")
        with col2:
            send_button = st.form_submit_button("Kirim")

        if send_button and new_message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat (sender, receiver, message, timestamp)
                VALUES (?, ?, ?, ?)
            """, (current_user, selected_user, new_message, timestamp))
            conn.commit()
            conn.close()
            st.rerun()

    # Tombol kembali dan logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Kelas", key="back_to_class_chat_main", use_container_width=True):
            st.session_state.current_page = "kelas"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout_chat_main", use_container_width=True):
            # Hapus session login
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.name = None
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()

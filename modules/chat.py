import streamlit as st
import sqlite3
from datetime import datetime

def show():
    st.markdown('<div class="header-style">💬 Chat Kelas</div>', unsafe_allow_html=True)
    current_user = st.session_state.name
    current_role = st.session_state.role

    # Cek apakah sudah ada kelas aktif
    if 'active_class' not in st.session_state:
        st.info("Silakan pilih atau buat kelas terlebih dahulu.")
        if st.button("↗️ Pilih Kelas", key="back_to_class_selection_chat", use_container_width=True):
            st.session_state.current_page = "class_selection"
            st.rerun()
        return

    # Ambil nama kelas aktif
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT class_name FROM classes WHERE id = ?", (st.session_state.active_class,))
    class_result = cursor.fetchone()
    conn.close()

    if class_result:
        class_name = class_result[0]
        st.info(f"Obrolan untuk kelas: **{class_name}**")
    else:
        st.error("❌ Kelas tidak ditemukan.")
        del st.session_state['active_class']
        st.rerun()
        return

    # Ambil semua pesan grup dari database
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    # Ambil pesan dengan receiver = "Kelas" (pesan grup)
    cursor.execute("""
        SELECT sender, message, timestamp, id
        FROM chat
        WHERE receiver = 'Kelas'
        ORDER BY timestamp ASC
    """)
    messages = cursor.fetchall()
    conn.close()

    # Tampilkan pesan grup
    st.subheader("Obrolan Grup")
    if messages:
        for sender, msg, time, msg_id in messages:
            if sender == current_user:
                with st.chat_message("user"):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{sender}**: {msg}")
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
                    st.write(f"**{sender}**: {msg}")
                    st.caption(time)
    else:
        st.info("Belum ada pesan di obrolan grup.")

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
            """, (current_user, "Kelas", new_message, timestamp))
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

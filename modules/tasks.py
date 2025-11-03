import streamlit as st
import os
import sqlite3
from datetime import datetime

# Pastikan folder tasks dan submissions ada
os.makedirs("data/tasks", exist_ok=True)
os.makedirs("data/submissions", exist_ok=True)

def show():
    st.header("📝 Tugas")
    role = st.session_state.role
    current_user = st.session_state.name

    # Cek status alur pembelajaran siswa untuk tugas
    if role == "siswa":
        task_status = get_task_status(current_user)
        
        # Status:
        # 0: Belum membaca tugas
        # 1: Sudah membaca tugas, belum lab virtual
        # 2: Sudah lab virtual
        
        if task_status == 0:
            # Arahkan ke tugas (LKPD)
            show_task(current_user)
        elif task_status == 1:
            # Arahkan ke lab virtual
            show_lab_virtual(current_user)
        else:
            # Semua selesai
            st.success("🎉 Selamat! Kamu telah menyelesaikan tugas dan lab virtual.")
            show_task_results(current_user)
    else:
        # Tampilan untuk guru/admin
        if role in ["guru", "admin"]:
            st.subheader("Upload Tugas Baru")
            # Tombol dengan icon plus
            if st.button("➕ Upload Tugas Baru", key="upload_task_btn"):
                st.session_state.show_upload_form = True

            if st.session_state.get("show_upload_form", False):
                with st.form("upload_task_form"):
                    uploaded_file = st.file_uploader("Upload tugas", type=["pdf", "docx"])
                    task_date = st.date_input("Tanggal Tugas", value=datetime.today())
                    description = st.text_area("Deskripsi Tugas")
                    submitted = st.form_submit_button("Upload")

                    if submitted and uploaded_file:
                        save_path = f"data/tasks/{uploaded_file.name}"
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        # Simpan ke database schedule
                        conn = sqlite3.connect("data/lms.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO schedule (title, description, date, type)
                            VALUES (?, ?, ?, ?)
                        """, (uploaded_file.name, description or "Tidak ada deskripsi", task_date.strftime("%Y-%m-%d"), "task"))
                        conn.commit()
                        conn.close()
                        st.success(f"Tugas {uploaded_file.name} berhasil diupload!")
                        st.session_state.show_upload_form = False
                        st.rerun()

        st.subheader("Daftar Tugas")
        files = os.listdir("data/tasks/")
        if files:
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            for f in files:
                # Ambil deskripsi dari database
                cursor.execute("SELECT description FROM schedule WHERE title = ? AND type = 'task'", (f,))
                result = cursor.fetchone()
                desc = result[0] if result else "Tidak ada deskripsi"

                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"📄 [{f}](data/tasks/{f})")
                    st.caption(f"📝 Deskripsi: {desc}")

                    # Preview file jika format didukung
                    file_path = f"data/tasks/{f}"
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
                            os.remove(f"data/tasks/{f}")
                            # Hapus dari database
                            cursor.execute("DELETE FROM schedule WHERE title = ? AND type = 'task'", (f,))
                            conn.commit()
                            st.success(f"Tugas '{f}' berhasil dihapus.")
                            st.rerun()
            conn.close()
        else:
            st.info("Belum ada tugas yang diupload.")

    # Tombol kembali dan logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Kelas", key="back_to_class_tasks", use_container_width=True):
            st.session_state.current_page = "kelas"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout_tasks", use_container_width=True):
            # Hapus session login
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.name = None
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()

def get_task_status(user):
    """
    Cek status pembelajaran siswa untuk tugas:
    0: Belum membaca tugas
    1: Sudah membaca tugas, belum lab virtual
    2: Sudah lab virtual
    """
    # Cek apakah sudah membaca tugas (simulasi dengan flag)
    if st.session_state.get(f"task_read_{user}", False):
        # Cek apakah sudah lab virtual
        if st.session_state.get(f"lab_virtual_done_{user}", False):
            return 2  # Sudah lab virtual
        else:
            return 1  # Sudah baca tugas, belum lab virtual
    else:
        return 0  # Belum baca tugas

def show_task(user):
    st.subheader("📚 Tugas (LKPD)")
    # Tampilkan tugas pertama
    files = os.listdir("data/tasks/") if os.path.exists("data/tasks/") else []
    if files:
        task_filename = files[0]
        task_path = f"data/tasks/{task_filename}"
        
        # Periksa apakah file tugas benar-benar ada
        if os.path.exists(task_path):
            st.write(f"📄 **{task_filename}**")
            
            # Preview file jika format didukung
            file_ext = task_filename.split('.')[-1].lower()

            if file_ext in ['jpg', 'jpeg', 'png']:
                st.image(task_path, caption=f"Preview {task_filename}", use_column_width=True)
            elif file_ext == 'pdf':
                # Untuk PDF, tampilkan link download karena streamlit tidak bisa embed PDF
                st.markdown(f"[📄 Lihat PDF]({task_path})")
            elif file_ext in ['mp4', 'mov', 'avi']:
                st.video(task_path)
            elif file_ext in ['mp3', 'wav']:
                st.audio(task_path)

            # Tombol sudah baca tugas
            if st.button("✅ Sudah Baca Tugas", use_container_width=True):
                st.session_state[f"task_read_{user}"] = True
                st.rerun()
        else:
            st.error(f"❌ File tugas '{task_filename}' tidak ditemukan. Silakan hubungi guru.")
    else:
        st.info("Belum ada tugas yang diupload.")

def show_lab_virtual(user):
    st.subheader("🔬 Lab Virtual")
    # Tampilkan lab virtual pertama
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, url_or_embed FROM virtual_labs ORDER BY date DESC LIMIT 1")
    lab = cursor.fetchone()
    conn.close()
    
    if lab:
        lab_id, title, desc, url_or_embed = lab
        st.write(f"🧪 **{title}**")
        st.caption(f"📝 Deskripsi: {desc}")
        
        # Tampilkan embed jika bukan link biasa
        if url_or_embed.startswith('<iframe'):
            st.components.v1.html(url_or_embed, height=400)
        elif url_or_embed.startswith('http'):
            # Jika link, tampilkan sebagai link dan embed
            st.markdown(f"[🔗 Buka Lab Virtual]({url_or_embed})")
            # Optional: Tampilkan embed link (bisa di disable jika tidak aman)
            # st.components.v1.iframe(url_or_embed, height=400)
        else:
            st.write("Konten tidak dikenali.")
        
        # Tombol sudah lab virtual
        if st.button("✅ Sudah Lab Virtual", use_container_width=True):
            st.session_state[f"lab_virtual_done_{user}"] = True
            st.rerun()
    else:
        st.info("Belum ada lab virtual yang diupload.")

def show_task_results(user):
    st.subheader("📊 Hasil Tugas dan Lab Virtual")
    st.success("🎉 Kamu telah menyelesaikan tugas dan lab virtual.")
    # Tampilkan hasil tugas dan lab virtual (jika ada)

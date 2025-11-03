import streamlit as st
import sqlite3
from datetime import datetime

def show():
    st.header("📋 Absensi")
    role = st.session_state.role
    current_user = st.session_state.name

    if role in ["guru", "admin"]:
        st.subheader("Buat Jadwal Absen Baru")
        # Tombol dengan icon plus
        if st.button("➕ Buat Jadwal Absen", key="create_attendance_btn"):
            st.session_state.show_attendance_form = True

        if st.session_state.get("show_attendance_form", False):
            with st.form("attendance_form"):
                title = st.text_input("Judul Jadwal Absen", value=f"Absensi {datetime.now().strftime('%d %B %Y')}")
                attendance_date = st.date_input("Tanggal Absen", value=datetime.today())
                submitted = st.form_submit_button("Simpan")

                if submitted and title:
                    # Simpan ke database schedule
                    conn = sqlite3.connect("data/lms.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO schedule (title, description, date, type)
                        VALUES (?, ?, ?, ?)
                    """, (title, "Jadwal absensi", attendance_date.strftime("%Y-%m-%d"), "attendance"))
                    conn.commit()
                    conn.close()
                    st.success(f"Jadwal absen '{title}' berhasil dibuat!")
                    st.session_state.show_attendance_form = False
                    st.rerun()

    st.subheader("Daftar Jadwal Absen")
    # Ambil daftar jadwal absen dari database
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, date FROM schedule WHERE type = 'attendance' ORDER BY date DESC")
    schedules = cursor.fetchall()
    conn.close()

    if schedules:
        for sch_id, title, date_str in schedules:
            st.write(f"**{title}** ({date_str})")
            # Cek apakah siswa sudah absen
            conn = sqlite3.connect("data/lms.db")
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM attendance WHERE student_name = ? AND title = ?", (current_user, title))
            result = cursor.fetchone()
            conn.close()

            if result:
                status = result[0]
                if status == "hadir":
                    st.success(f"✅ Anda telah mengisi absensi (Status: {status})")
                elif status == "tidak hadir":
                    st.error(f"❌ Anda telah mengisi absensi (Status: {status})")
                else:
                    st.info(f"ℹ️ Anda telah mengisi absensi (Status: {status})")
            else:
                if role == "siswa":
                    # Tombol untuk absen
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Hadir", key=f"hadir_{sch_id}"):
                            conn = sqlite3.connect("data/lms.db")
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO attendance (title, date, student_name, status)
                                VALUES (?, ?, ?, ?)
                            """, (title, date_str, current_user, "hadir"))
                            conn.commit()
                            conn.close()
                            st.success("Absen berhasil!")
                            st.rerun()
                    with col2:
                        if st.button("❌ Tidak Hadir", key=f"tidak_hadir_{sch_id}"):
                            conn = sqlite3.connect("data/lms.db")
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO attendance (title, date, student_name, status)
                                VALUES (?, ?, ?, ?)
                            """, (title, date_str, current_user, "tidak hadir"))
                            conn.commit()
                            conn.close()
                            st.success("Absen berhasil!")
                            st.rerun()
                    with col3:
                        if st.button("ℹ️ Izin", key=f"izin_{sch_id}"):
                            conn = sqlite3.connect("data/lms.db")
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO attendance (title, date, student_name, status)
                                VALUES (?, ?, ?, ?)
                            """, (title, date_str, current_user, "izin"))
                            conn.commit()
                            conn.close()
                            st.success("Absen berhasil!")
                            st.rerun()
                elif role in ["guru", "admin"]:
                    # Tampilkan tabel absensi siswa
                    conn = sqlite3.connect("data/lms.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM users WHERE role = 'siswa'")
                    students = cursor.fetchall()
                    conn.close()

                    if students:
                        st.write("**Tabel Absensi Siswa:**")
                        table_data = []
                        for i, (student_name,) in enumerate(students):
                            conn = sqlite3.connect("data/lms.db")
                            cursor = conn.cursor()
                            cursor.execute("SELECT status FROM attendance WHERE student_name = ? AND title = ?", (student_name, title))
                            result = cursor.fetchone()
                            conn.close()
                            status = result[0] if result else "Belum Absen"
                            table_data.append([i+1, student_name, status])
                        
                        # Tampilkan tabel
                        st.table(table_data)
                    else:
                        st.info("Belum ada siswa.")
    else:
        st.info("Belum ada jadwal absen.")

    # Tombol kembali dan logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Kelas", key="back_to_class_attendance"):
            st.session_state.current_page = "kelas"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout_attendance", use_container_width=True):
            # Hapus session login
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.name = None
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()


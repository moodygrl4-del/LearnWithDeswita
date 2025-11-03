import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import calendar
import os

def show():
    st.header("📅 Kalender Kegiatan")
    
    # Ambil jadwal dari database
    conn = sqlite3.connect("data/lms.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, description, date, type FROM schedule ORDER BY date ASC")
    schedules = cursor.fetchall()
    conn.close()

    # Buat dict untuk tanggal: [daftar kegiatan]
    schedule_dict = {}
    for title, desc, date_str, type_ in schedules:
        if date_str not in schedule_dict:
            schedule_dict[date_str] = []
        schedule_dict[date_str].append((title, desc, type_))

    # Input bulan dan tahun
    today = datetime.today()
    year = st.selectbox("Pilih Tahun", list(range(2020, 2031)), index=5)
    month = st.selectbox("Pilih Bulan", list(range(1, 13)), index=today.month - 1)

    # Buat kalender
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    st.subheader(f"{month_name} {year}")

    # Header hari
    cols = st.columns(7)
    days = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    for i, day in enumerate(days):
        cols[i].write(f"**{day}**")

    # Tampilkan tanggal
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                # Cek apakah ada jadwal di tanggal ini
                events = schedule_dict.get(date_str, [])
                if events:
                    event_titles = []
                    for title, desc, type_ in events:
                        # Jika tipe task, tambahkan info progres
                        if type_ == "task":
                            # Cek berapa banyak siswa yang sudah submit
                            if os.path.exists("data/submissions/"):
                                submissions = [f for f in os.listdir("data/submissions/") if title in f]
                                submitted_count = len(submissions)
                                event_titles.append(f"• {title} ({submitted_count} siswa submit)")
                            else:
                                event_titles.append(f"• {title} (0 siswa submit)")
                        # Tambahkan info lab virtual
                        elif type_ == "lab":
                            event_titles.append(f"• {title} (Lab Virtual)")
                        # Tambahkan info absen
                        elif type_ == "attendance":
                            event_titles.append(f"• {title} (Absensi)")
                        else:
                            event_titles.append(f"• {title}")
                    event_list = "\n".join(event_titles)
                    cols[i].write(f"**{day}**\n\n{event_list}")
                else:
                    cols[i].write(day)

    # Tampilkan daftar lengkap jadwal
    st.subheader("Daftar Kegiatan Lengkap")
    if schedules:
        for title, desc, date_str, type_ in schedules:
            # Tambahkan info progres ke tugas
            if type_ == "task":
                if os.path.exists("data/submissions/"):
                    submissions = [f for f in os.listdir("data/submissions/") if title in f]
                    submitted_count = len(submissions)
                    st.write(f"📅 **{date_str}** — **{type_.capitalize()}**: {title} — {desc} — **{submitted_count} siswa submit**")
                else:
                    st.write(f"📅 **{date_str}** — **{type_.capitalize()}**: {title} — {desc} — **0 siswa submit**")
            # Tambahkan info lab virtual
            elif type_ == "lab":
                st.write(f"📅 **{date_str}** — **{type_.capitalize()}**: {title} — {desc}")
            # Tambahkan info absen
            elif type_ == "attendance":
                st.write(f"📅 **{date_str}** — **{type_.capitalize()}**: {title} — {desc}")
            else:
                st.write(f"📅 **{date_str}** — **{type_.capitalize()}**: {title} — {desc}")
    else:
        st.info("Belum ada jadwal kegiatan.")

    # Tombol kembali dan logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Kelas", key="back_to_class_calendar"):
            st.session_state.current_page = "kelas"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout_calendar", use_container_width=True):
            # Hapus session login
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.name = None
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()


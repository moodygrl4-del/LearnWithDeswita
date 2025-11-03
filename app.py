import streamlit as st
from modules import auth, dashboard

# Konfigurasi halaman
st.set_page_config(
    page_title="LearnWithDeswita",
    page_icon="📚",
    layout="wide"
)

# Tambahkan CSS
with open("assets/css/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'role' not in st.session_state:
        st.session_state.role = None

    if not st.session_state.logged_in:
        auth.show_login()
    else:
        # Jika belum ada halaman yang dipilih, arahkan ke kelas
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "kelas"

        # Sidebar
        role = st.session_state.role
        menu = {
            "admin": [
                ("🏫 Kelas", "kelas"),
                ("🏠 Dashboard", "dashboard"),
                ("📅 Kalender", "calendar"),
                ("📋 Absensi", "attendance"),
                ("👥 Manajemen Pengguna", "users"),
                ("📚 Materi", "materials"),
                ("📝 Tugas", "tasks"),
                ("❓ Kuis", "quiz"),
                ("💬 Chat", "chat"),
                ("🔬 Lab Virtual", "virtual_lab"),
                ("📈 Progres Siswa", "progress")
            ],
            "guru": [
                ("🏫 Kelas", "kelas"),
                ("🏠 Dashboard", "dashboard"),
                ("📅 Kalender", "calendar"),
                ("📋 Absensi", "attendance"),
                ("📚 Materi", "materials"),
                ("📝 Tugas", "tasks"),
                ("❓ Kuis", "quiz"),
                ("💬 Chat", "chat"),
                ("🔬 Lab Virtual", "virtual_lab"),
                ("📈 Progres Siswa", "progress")
            ],
            "siswa": [
                ("🏫 Kelas", "kelas"),
                ("🏠 Dashboard", "dashboard"),
                ("📅 Kalender", "calendar"),
                ("📋 Absensi", "attendance"),
                ("📚 Materi", "materials"),
                ("📝 Tugas", "tasks"),
                ("❓ Kuis", "quiz"),
                ("💬 Chat", "chat"),
                ("🔬 Lab Virtual", "virtual_lab"),
                ("📈 Progres Saya", "progress")
            ]
        }

        # Sidebar
        with st.sidebar:
            st.markdown(f'<div class="sidebar-title">📚 LMS - {role.capitalize()}</div>', unsafe_allow_html=True)
            st.write(f"Selamat datang, **{st.session_state.name}**")

            # Tombol sidebar
            for label, page_key in menu[role]:
                if st.button(label, key=f"sidebar_{page_key}", use_container_width=True):
                    st.session_state.current_page = page_key
                    st.rerun()

        # Tampilkan halaman berdasarkan current_page
        page = st.session_state.current_page

        # Routing halaman
        if page == "kelas":
            dashboard.show_kelas()
        elif page == "dashboard":
            dashboard.show_dashboard()
        elif page == "calendar":
            from modules import calendar
            calendar.show()
        elif page == "materials":
            from modules import materials
            materials.show()
        elif page == "tasks":
            from modules import tasks
            tasks.show()
        elif page == "quiz":
            from modules import quiz
            quiz.show()
        elif page == "chat":
            from modules import chat
            chat.show()
        elif page == "virtual_lab":
            from modules import virtual_lab
            virtual_lab.show()
        elif page == "progress":
            from modules import progress
            progress.show()
        elif page == "users" and role == "admin":
            st.write("Fitur manajemen pengguna (akan ditambahkan nanti).")
        elif page == "attendance":
            from modules import attendance
            attendance.show()
        # Tambahkan routing untuk classroom
        elif page == "class_selection":
            from modules import classroom
            classroom.show_class_selection()

if __name__ == "__main__":
    main()
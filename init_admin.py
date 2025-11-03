from modules.auth import add_user, create_user_table

# Pastikan tabel 'users' sudah dibuat
create_user_table()

# Buat akun admin default
success = add_user("admin", "admin123", "admin")

if success:
    print("✅ Akun admin berhasil dibuat!")
    print("Username: admin")
    print("Password: admin123")
else:
    print("❌ Gagal membuat akun (mungkin username sudah ada).")
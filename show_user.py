#!/usr/bin/env python3
"""
show_users.py
Scan `data/` untuk menemukan penyimpanan akun (SQLite .db atau .json)
dan cetak daftar akun (username, role). Aman dipakai; tidak merubah data.
"""

import os
import json
import sqlite3
from typing import List, Dict

DATA_DIR = "data"

def check_json_files() -> List[str]:
    if not os.path.isdir(DATA_DIR):
        return []
    return [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.lower().endswith(".json")]

def try_read_users_json(path: str) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [!] Gagal membaca JSON '{path}': {e}")
        return []

    # If it's a dict with usernames under a key, try to find them
    if isinstance(data, dict):
        # common patterns: {"users": [...]} or file is quizzes etc. Try to find list values containing dicts with 'username'
        # first check top-level 'users'
        if "users" in data and isinstance(data["users"], list):
            return [u for u in data["users"] if isinstance(u, dict) and "username" in u]
        # otherwise scan nested lists
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "username" in v[0]:
                return [u for u in v if isinstance(u, dict) and "username" in u]
        # Not found
        return []
    elif isinstance(data, list):
        # list of objects? filter those with username
        return [u for u in data if isinstance(u, dict) and "username" in u]
    else:
        return []

def scan_jsons_and_print():
    json_files = check_json_files()
    found = False
    for jf in json_files:
        users = try_read_users_json(jf)
        if users:
            found = True
            print(f"\n[JSON] Ditemukan akun di: {jf}")
            for u in users:
                uname = u.get("username") or u.get("user") or u.get("name") or "(unknown)"
                role = u.get("role") or u.get("role_name") or "(no role)"
                pw = "(hidden)" if "password" in u else "(no password field)"
                print(f"  - Username: {uname}, Role: {role}, PasswordField: {pw}")
    return found

def find_db_files():
    if not os.path.isdir(DATA_DIR):
        return []
    return [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.lower().endswith(".db")]

def try_read_sqlite_users(path: str) -> List[tuple]:
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
    except Exception as e:
        print(f"  [!] Gagal buka DB '{path}': {e}")
        return []

    rows = []
    try:
        # Check if table 'users' exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        if "users" in tables:
            c.execute("PRAGMA table_info(users)")
            cols = [r[1] for r in c.fetchall()]  # column names
            # Try to select common columns
            c.execute("SELECT * FROM users")
            rows = c.fetchall()
            conn.close()
            return [(cols, row) for row in rows]
        else:
            # attempt to find table with username-like column
            for t in tables:
                try:
                    c.execute(f"PRAGMA table_info({t})")
                    cols = [r[1] for r in c.fetchall()]
                    if any(col.lower() in ("username","user","name","email") for col in cols):
                        c.execute(f"SELECT * FROM {t} LIMIT 100")
                        rows = c.fetchall()
                        conn.close()
                        return [(cols, row) for row in rows]
                except Exception:
                    continue
    except Exception as e:
        print(f"  [!] Gagal query DB '{path}': {e}")
    finally:
        conn.close()
    return []

def scan_dbs_and_print():
    db_files = find_db_files()
    found = False
    for db in db_files:
        results = try_read_sqlite_users(db)
        if results:
            found = True
            print(f"\n[SQLite DB] Ditemukan data user di: {db}")
            # results is list of (cols, row)
            for cols, row in results:
                # print friendly mapping
                mapping = {cols[i]: row[i] for i in range(len(cols))}
                uname = mapping.get("username") or mapping.get("user") or mapping.get("name") or "(unknown)"
                role = mapping.get("role") or mapping.get("role_name") or "(no role)"
                pw = mapping.get("password", "(no password field)")
                print(f"  - Username: {uname}, Role: {role}, PasswordStored: {pw}")
    return found

def main():
    print("Mengecek folder 'data/' untuk penyimpanan akun...")
    if not os.path.isdir(DATA_DIR):
        print("  Folder 'data/' tidak ditemukan. Pastikan kamu menjalankan script ini dari folder proyek.")
        return

    any_found = False
    # JSON
    any_found = scan_jsons_and_print() or any_found
    # SQLite
    any_found = scan_dbs_and_print() or any_found

    if not any_found:
        print("\nTidak ditemukan akun di data/.")
        print("Kemungkinan penyimpanan akun belum dibuat (belum ada registrasi) atau disimpan di lokasi lain.")
        print("Jika kamu menggunakan modul auth.py, periksa file modules/auth.py untuk path DB/JSON yang dipakai.")
    else:
        print("\nSelesai. Jika ingin menampilkan lebih rinci, jalankan script ini lagi atau beri tahu file yang ingin diperiksa.")

if __name__ == "__main__":
    main()

import sqlite3

conn = sqlite3.connect('data/app.db')
cur = conn.cursor()
cur.execute("SELECT username, password_temporanea, totp_enabled, totp_secret FROM utenti WHERE username='admin'")
result = cur.fetchone()
print(f"Admin record: {result}")
if result:
    username, pwd_temp, totp_enabled, totp_secret = result
    print(f"  Username: {username}")
    print(f"  Password temporanea: {pwd_temp}")
    print(f"  TOTP Enabled: {totp_enabled}")
    print(f"  TOTP Secret: {totp_secret}")
conn.close()

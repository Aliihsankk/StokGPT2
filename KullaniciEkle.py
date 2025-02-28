import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('StokDB.db')
cursor = conn.cursor()

# Varsayılan yönetici hesabı ekleyelim
hashed_password = generate_password_hash("admin123")  # Şifre: admin123
cursor.execute("INSERT INTO Kullanici (kullanici_adi, sifre,yetki) VALUES (?, ?,?)", ("admin", hashed_password,"admin"))

conn.commit()
conn.close()
print("Admin kullanıcı başarıyla eklendi!")

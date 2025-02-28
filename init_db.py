import sqlite3

def init_db():
    conn = sqlite3.connect('StokDB.db')
    c = conn.cursor()
    
    # Isyeri tablosunu oluştur
    c.execute('''
        CREATE TABLE IF NOT EXISTS Isyeri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isyeri_adi TEXT NOT NULL,
            isyeri_servisi TEXT,
            konum TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Veritabanı ve tablolar başarıyla oluşturuldu.")

def update_table():
    conn = sqlite3.connect('StokDB.db')
    c = conn.cursor()
    
    try:
        # Miktar sütununu ekle
        c.execute('ALTER TABLE Malzemeler ADD COLUMN miktar INTEGER')
        print("Miktar sütunu başarıyla eklendi")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Miktar sütunu zaten mevcut")
        else:
            print(f"Hata: {e}")
    
    try:
        # Birim sütununu ekle
        c.execute('ALTER TABLE Malzemeler ADD COLUMN birim TEXT')
        print("Birim sütunu başarıyla eklendi")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Birim sütunu zaten mevcut")
        else:
            print(f"Hata: {e}")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    update_table() 
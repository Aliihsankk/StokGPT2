from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template
app = Flask(__name__)
app.secret_key = 'stok_yonetim_sistemi'

def get_db_connection():
    conn = sqlite3.connect('StokDB.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Kullanici (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kullanici_adi TEXT UNIQUE NOT NULL,
                        sifre TEXT NOT NULL,
                        yetki TEXT NOT NULL,
                        aciklama TEXT,
                        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Isyeri (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        isyeri_adi TEXT NOT NULL,
                        adres TEXT,
                        telefon TEXT,
                        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        kullanici_id INTEGER
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Firma (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        firma_adi TEXT NOT NULL,
                        firma_adresi TEXT,
                        aciklama TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Birim (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        birim_adi TEXT NOT NULL,
                        aciklama TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Malzemeler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stok_kodu TEXT UNIQUE NOT NULL,
                        malzeme_adi TEXT NOT NULL,
                        aciklama TEXT,
                        kullanici_id INTEGER,
                        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Stok (
                        stok_kodu TEXT PRIMARY KEY,
                        malzeme_adi TEXT NOT NULL,
                        miktar INTEGER NOT NULL,
                        birim_adi TEXT NOT NULL,
                        minimum_miktar INTEGER,
                        son_miktar INTEGER,
                        son_islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        son_islem_tipi TEXT,
                        kullanici_id INTEGER
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Stok_Giris (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stok_kodu TEXT NOT NULL,
                        malzeme_adi TEXT NOT NULL,
                        miktar INTEGER NOT NULL,
                        birim_adi TEXT NOT NULL,
                        islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        gelis_nedeni TEXT,
                        firma_isyeri_adi TEXT,
                        aciklama TEXT,
                        kullanici_id INTEGER
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Stok_Cikis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stok_kodu TEXT NOT NULL,
                        malzeme_adi TEXT NOT NULL,
                        miktar INTEGER NOT NULL,
                        birim_adi TEXT NOT NULL,
                        isyeri_adi TEXT NOT NULL,
                        teslim_alan TEXT,
                        islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        aciklama TEXT,
                        kullanici_id INTEGER
                    )''')
    conn.commit()
    conn.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Kullanici WHERE kullanici_adi = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['sifre'], password):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            return "Hatalı kullanıcı adı veya şifre!", 403

    return render_template('login.html')


@app.route('/isyeri_kayit', methods=['GET', 'POST'])
def isyeri_kayit():
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            isyerleri = conn.execute('SELECT * FROM Isyeri ORDER BY id DESC').fetchall()
            conn.close()
            return render_template('isyeri_kayit.html', isyerleri=isyerleri)
        except Exception as e:
            print("Error:", e)
            return f"Hata oluştu: {e}"
    
    elif request.method == 'POST':
        isyeri_adi = request.form.get('isyeri_adi')
        isyeri_servisi = request.form.get('isyeri_servisi')
        konum = request.form.get('konum')
        
        if not isyeri_adi:
            return jsonify(success=False, message="İşyeri adı boş olamaz."), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = "INSERT INTO Isyeri (isyeri_adi, isyeri_servisi, konum) VALUES (?, ?, ?)"
            cursor.execute(sql, (isyeri_adi, isyeri_servisi, konum))
            
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            return jsonify(success=True, id=new_id)
            
        except Exception as e:
            print("Database Error:", str(e))
            return jsonify(success=False, message=str(e)), 500

@app.route('/isyeri_duzenle/<int:id>', methods=['POST'])
def isyeri_duzenle(id):
    isyeri_adi = request.form.get('isyeri_adi')
    isyeri_servisi = request.form.get('isyeri_servisi')
    konum = request.form.get('konum')
    
    if not isyeri_adi:
        return jsonify(success=False, message="İşyeri adı boş olamaz."), 400
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE Isyeri SET isyeri_adi = ?, isyeri_servisi = ?, konum = ? WHERE id = ?",
            (isyeri_adi, isyeri_servisi, konum, id)
        )
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        print("Update Error:", str(e))
        return jsonify(success=False, message=str(e)), 500

@app.route('/isyeri_sil/<int:id>', methods=['POST'])
def isyeri_sil(id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM Isyeri WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        print("Delete Error:", str(e))
        return jsonify(success=False, message=str(e)), 500

@app.route('/')
def index():
    return render_template('ana_ekran.html')

@app.route('/firma_kayit', methods=['GET', 'POST'])
def firma_kayit():
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            firmalar = conn.execute('SELECT * FROM Firma ORDER BY id DESC').fetchall()
            conn.close()
            return render_template('firma_kayit.html', firmalar=firmalar)
        except Exception as e:
            print("Error:", e)
            return f"Hata oluştu: {e}"
    
    elif request.method == 'POST':
        firma_adi = request.form.get('firma_adi')
        firma_adresi = request.form.get('firma_adresi')
        aciklama = request.form.get('aciklama')
        
        if not firma_adi:
            return jsonify(success=False, message="Firma adı boş olamaz."), 400
        try:
            conn = get_db_connection()
            cursor = conn.execute(
                "INSERT INTO Firma (firma_adi, firma_adresi, aciklama) VALUES (?, ?, ?)",
                (firma_adi, firma_adresi, aciklama)
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return jsonify(success=True, id=new_id)
        except Exception as e:
            return jsonify(success=False, message=str(e)), 500

@app.route('/firma_duzenle/<int:id>', methods=['POST'])
def firma_duzenle(id):
    firma_adi = request.form.get('firma_adi')
    firma_adresi = request.form.get('firma_adresi')
    aciklama = request.form.get('aciklama')
    
    if not firma_adi:
        return jsonify(success=False, message="Firma adı boş olamaz."), 400
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE Firma SET firma_adi = ?, firma_adresi = ?, aciklama = ? WHERE id = ?",
            (firma_adi, firma_adresi, aciklama, id)
        )
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/firma_sil/<int:id>', methods=['POST'])
def firma_sil(id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM Firma WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/malzeme_kayit', methods=['GET', 'POST'])
def malzeme_kayit():
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            malzemeler = conn.execute('SELECT * FROM Malzemeler ORDER BY id DESC').fetchall()
            conn.close()
            return render_template('malzeme_kayit.html', malzemeler=malzemeler)
        except Exception as e:
            print("Error:", e)
            return f"Hata oluştu: {e}"
    
    elif request.method == 'POST':
        stok_kodu = request.form.get('stok_kodu')
        malzeme_adi = request.form.get('malzeme_adi')
        aciklama = request.form.get('aciklama')
        
        if not stok_kodu or not malzeme_adi:
            return jsonify(success=False, message="Stok kodu ve malzeme adı zorunludur."), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.execute(
                "INSERT INTO Malzemeler (stok_kodu, malzeme_adi, aciklama) VALUES (?, ?, ?)",
                (stok_kodu, malzeme_adi, aciklama)
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return jsonify(success=True, id=new_id)
        except sqlite3.IntegrityError as e:
            return jsonify(success=False, message="Bu stok kodu zaten kullanılıyor."), 400
        except Exception as e:
            print("Database Error:", str(e))
            return jsonify(success=False, message=str(e)), 500

@app.route('/stok_giris', endpoint='stok_giris_view')
def stok_giris_view():
    return render_template('stok_giris.html')

@app.route('/stok_cikis')
def stok_cikis():
    return render_template('stok_cikis.html')

@app.route('/kullanici_kayit')
def kullanici_kayit():
    return render_template('kullanici_kayit.html')

@app.route('/malzeme_ekle', methods=['POST'])
def malzeme_ekle():
    try:
        malzeme_adi = request.form.get('malzeme_adi')
        miktar = request.form.get('miktar', 0)  # Varsayılan değer 0
        birim = request.form.get('birim', '')   # Varsayılan değer boş string
        aciklama = request.form.get('aciklama', '')
        
        if not malzeme_adi:
            return jsonify(success=False, message="Malzeme adı boş olamaz"), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO Malzemeler (malzeme_adi, miktar, birim, aciklama) VALUES (?, ?, ?, ?)",
            (malzeme_adi, miktar, birim, aciklama)
        )
        
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        return jsonify(success=True, id=new_id)
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify(success=False, message=str(e)), 500

@app.route('/malzeme_sil/<int:id>', methods=['POST'])
def malzeme_sil(id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM Malzemeler WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/malzeme_duzenle/<int:id>', methods=['POST'])
def malzeme_duzenle(id):
    stok_kodu = request.form.get('stok_kodu')
    malzeme_adi = request.form.get('malzeme_adi')
    aciklama = request.form.get('aciklama')
    
    if not stok_kodu or not malzeme_adi:
        return jsonify(success=False, message="Stok kodu ve malzeme adı zorunludur."), 400
    
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE Malzemeler SET stok_kodu = ?, malzeme_adi = ?, aciklama = ? WHERE id = ?",
            (stok_kodu, malzeme_adi, aciklama, id)
        )
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except sqlite3.IntegrityError as e:
        return jsonify(success=False, message="Bu stok kodu zaten kullanılıyor."), 400
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/stok_ekrani')
def stok_ekrani():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                stok_kodu,
                malzeme_adi,
                miktar,
                birim_adi,
                minimum_miktar,
                son_miktar,
                son_islem_tarihi,
                CASE 
                    WHEN son_islem_tipi = 'giris' THEN 'Giriş'
                    WHEN son_islem_tipi = 'cikis' THEN 'Çıkış'
                    ELSE '-'
                END as son_islem_tipi
            FROM Stok 
            ORDER BY malzeme_adi
        """)
        stoklar = cursor.fetchall()
        return render_template('stok_ekrani.html', stoklar=stoklar)
    except Exception as e:
        print("Hata:", str(e))
        return str(e)
    finally:
        conn.close()

@app.route('/stok_listele')
def stok_listele():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                stok_kodu,
                malzeme_adi,
                miktar,
                birim_adi,
                minimum_miktar,
                son_miktar,
                son_islem_tarihi,
                CASE 
                    WHEN son_islem_tipi = 'giris' THEN 'Giriş'
                    WHEN son_islem_tipi = 'cikis' THEN 'Çıkış'
                    ELSE '-'
                END as son_islem_tipi
            FROM Stok 
            ORDER BY malzeme_adi
        """)
        columns = [column[0] for column in cursor.description]
        stoklar = []
        for row in cursor.fetchall():
            stok = dict(zip(columns, row))
            stoklar.append(stok)
        return jsonify({"success": True, "stoklar": stoklar})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/malzemeler_listele')
def malzemeler_listele():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, s.birim_adi 
            FROM Malzemeler m 
            LEFT JOIN Stok s ON m.stok_kodu = s.stok_kodu 
            ORDER BY m.malzeme_adi
        """)
        columns = [column[0] for column in cursor.description]
        malzemeler = []
        for row in cursor.fetchall():
            malzeme = dict(zip(columns, row))
            malzemeler.append(malzeme)
        return jsonify({"success": True, "malzemeler": malzemeler})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/stok_giris_kaydet', methods=['POST'])
def stok_giris_kaydet():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stok_kodu = request.form.get('stok_kodu')
        malzeme_adi = request.form.get('malzeme_adi')
        miktar = request.form.get('miktar')
        birim_adi = request.form.get('birim_adi')
        gelis_nedeni = request.form.get('gelis_nedeni')
        firma_isyeri_adi = request.form.get('firma_isyeri_adi')
        aciklama = request.form.get('aciklama')
        
        cursor.execute("""
            INSERT INTO Stok_Giris (
                stok_kodu, malzeme_adi, miktar, birim_adi,
                gelis_nedeni, firma_isyeri_adi, aciklama
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (stok_kodu, malzeme_adi, miktar, birim_adi,
              gelis_nedeni, firma_isyeri_adi, aciklama))
        
        cursor.execute("""
            INSERT OR REPLACE INTO Stok (
                stok_kodu, malzeme_adi, miktar, birim_adi,
                son_miktar, son_islem_tarihi, son_islem_tipi
            ) VALUES (
                ?, ?, 
                COALESCE((SELECT miktar FROM Stok WHERE stok_kodu = ?) + ?, ?),
                ?, 
                ?, 
                CURRENT_TIMESTAMP,
                'giris'
            )
        """, (stok_kodu, malzeme_adi, stok_kodu, miktar, miktar,
              birim_adi, miktar))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print("Hata:", str(e))  # Hatayı konsola yazdır
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/stok_giris_listele')
def stok_giris_listele():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Stok_Giris ORDER BY id DESC")
        columns = [column[0] for column in cursor.description]
        kayitlar = []
        for row in cursor.fetchall():
            kayit = dict(zip(columns, row))
            kayitlar.append(kayit)
        return jsonify({"success": True, "kayitlar": kayitlar})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/stok_giris_sil/<int:id>', methods=['POST'])
def stok_giris_sil(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Önce silinecek kaydın bilgilerini al
        cursor.execute("SELECT stok_kodu, miktar FROM Stok_Giris WHERE id = ?", (id,))
        kayit = cursor.fetchone()
        
        if kayit:
            stok_kodu = kayit['stok_kodu']
            miktar = kayit['miktar']
            
            # Stok tablosundan miktarı düş
            cursor.execute("""
                UPDATE Stok 
                SET miktar = miktar - ?,
                    son_miktar = son_miktar - ?,
                    son_islem_tarihi = CURRENT_TIMESTAMP
                WHERE stok_kodu = ?
            """, (miktar, miktar, stok_kodu))
            
            # Stok giriş kaydını sil
            cursor.execute("DELETE FROM Stok_Giris WHERE id = ?", (id,))
            
            conn.commit()
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Kayıt bulunamadı"})
    except Exception as e:
        print("Hata:", str(e))
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/stok_minimum_guncelle', methods=['POST'])
def stok_minimum_guncelle():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stok_kodu = request.form.get('stok_kodu')
        minimum_miktar = request.form.get('minimum_miktar', 0)
        
        cursor.execute("""
            UPDATE Stok 
            SET minimum_miktar = ? 
            WHERE stok_kodu = ?
        """, (minimum_miktar, stok_kodu))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print("Hata:", str(e))
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/isyerleri_listele')
def isyerleri_listele():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Isyeri ORDER BY id DESC')
        
        # Sütun isimlerini al
        columns = [column[0] for column in cursor.description]
        
        # Kayıtları sözlük listesine dönüştür
        isyerleri = []
        for row in cursor.fetchall():
            isyeri = dict(zip(columns, row))
            isyerleri.append(isyeri)
            
        return jsonify({"success": True, "isyerleri": isyerleri})
    except Exception as e:
        print("Hata:", str(e))
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/firmalar_listele')
def firmalar_listele():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Firma ORDER BY id DESC')
        
        # Sütun isimlerini al
        columns = [column[0] for column in cursor.description]
        
        # Kayıtları sözlük listesine dönüştür
        firmalar = []
        for row in cursor.fetchall():
            firma = dict(zip(columns, row))
            firmalar.append(firma)
            
        return jsonify({"success": True, "firmalar": firmalar})
    except Exception as e:
        print("Hata:", str(e))
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/stok_cikis_kaydet', methods=['POST'])
def stok_cikis_kaydet():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stok_kodu = request.form.get('stok_kodu')
        malzeme_adi = request.form.get('malzeme_adi')
        miktar = int(request.form.get('miktar'))
        birim_adi = request.form.get('birim_adi')
        isyeri_adi = request.form.get('isyeri_adi')
        teslim_alan = request.form.get('teslim_alan')
        aciklama = request.form.get('aciklama')
        
        cursor.execute("SELECT miktar FROM Stok WHERE stok_kodu = ?", (stok_kodu,))
        mevcut_stok = cursor.fetchone()
        
        if not mevcut_stok:
            return jsonify({"success": False, "message": "Stok bulunamadı!"})
            
        mevcut_miktar = mevcut_stok[0]
        
        if miktar > mevcut_miktar:
            return jsonify({"success": False, "message": f"Yetersiz stok! Mevcut stok: {mevcut_miktar}"})
        
        cursor.execute("""
            INSERT INTO Stok_Cikis (
                stok_kodu, malzeme_adi, miktar, birim_adi, 
                isyeri_adi, teslim_alan, aciklama
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (stok_kodu, malzeme_adi, miktar, birim_adi, isyeri_adi, teslim_alan, aciklama))
        
        yeni_miktar = mevcut_miktar - miktar
        cursor.execute("""
            UPDATE Stok 
            SET miktar = ?, 
                son_miktar = ?,
                son_islem_tarihi = CURRENT_TIMESTAMP,
                son_islem_tipi = 'cikis'
            WHERE stok_kodu = ?
        """, (yeni_miktar, miktar, stok_kodu))
        
        conn.commit()
        return jsonify({"success": True, "message": "Stok çıkışı başarıyla kaydedildi."})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/stok_cikis_listele')
def stok_cikis_listele():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id, stok_kodu, malzeme_adi, miktar, birim_adi,
                isyeri_adi, teslim_alan, islem_tarihi, aciklama
            FROM Stok_Cikis 
            ORDER BY islem_tarihi DESC
        """)
        columns = [column[0] for column in cursor.description]
        kayitlar = []
        for row in cursor.fetchall():
            kayit = dict(zip(columns, row))
            kayitlar.append(kayit)
        return jsonify({"success": True, "kayitlar": kayitlar})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/stok_cikis_sil/<int:id>', methods=['POST'])
def stok_cikis_sil(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Silinecek kaydın bilgilerini al
        cursor.execute("SELECT stok_kodu, miktar FROM Stok_Cikis WHERE id = ?", (id,))
        kayit = cursor.fetchone()
        
        if not kayit:
            return jsonify({"success": False, "message": "Kayıt bulunamadı!"})
            
        stok_kodu = kayit[0]
        miktar = kayit[1]
        
        # Stok miktarını geri ekle
        cursor.execute("""
            UPDATE Stok 
            SET miktar = miktar + ?,
                son_islem_tarihi = CURRENT_TIMESTAMP 
            WHERE stok_kodu = ?
        """, (miktar, stok_kodu))
        
        # Kaydı sil
        cursor.execute("DELETE FROM Stok_Cikis WHERE id = ?", (id,))
        
        conn.commit()
        return jsonify({"success": True, "message": "Kayıt başarıyla silindi."})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/birim_kayit', methods=['GET', 'POST'])
def birim_kayit():
    if request.method == 'GET':
        return render_template('birim_kayit.html')
    
    elif request.method == 'POST':
        birim_adi = request.form.get('birim_adi')
        aciklama = request.form.get('aciklama')
        
        if not birim_adi:
            return jsonify(success=False, message="Birim adı boş olamaz."), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO Birim (birim_adi, aciklama) VALUES (?, ?)",
                (birim_adi, aciklama)
            )
            
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            return jsonify(success=True, id=new_id)
            
        except Exception as e:
            print("Database Error:", str(e))
            return jsonify(success=False, message=str(e)), 500

@app.route('/birim_duzenle/<int:id>', methods=['POST'])
def birim_duzenle(id):
    birim_adi = request.form.get('birim_adi')
    aciklama = request.form.get('aciklama')
    
    if not birim_adi:
        return jsonify(success=False, message="Birim adı boş olamaz."), 400
    
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE Birim SET birim_adi = ?, aciklama = ? WHERE id = ?",
            (birim_adi, aciklama, id)
        )
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/birim_sil/<int:id>', methods=['POST'])
def birim_sil(id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM Birim WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/birimler_listele')
def birimler_listele():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Birim ORDER BY birim_adi')
        
        columns = [column[0] for column in cursor.description]
        birimler = []
        for row in cursor.fetchall():
            birim = dict(zip(columns, row))
            birimler.append(birim)
            
        return jsonify({"success": True, "birimler": birimler})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

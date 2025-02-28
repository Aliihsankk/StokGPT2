from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template
from anthropic import Anthropic
import os

app = Flask(__name__)
app.secret_key = 'stok_yonetim_sistemi'

# Claude istemcisi
anthropic = Anthropic(
    api_key="Claude_API_KEY"
)

def get_db_connection():
    try:
        conn = sqlite3.connect('StokDB.db', timeout=20)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        return None

def init_db():
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        # Birimler tablosunu oluştur
        cursor.execute('''CREATE TABLE IF NOT EXISTS Birimler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            birim_adi TEXT NOT NULL,
            aciklama TEXT
        )''')
        
        # Isyerleri tablosunu oluştur
        cursor.execute('''CREATE TABLE IF NOT EXISTS Isyerleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isyeri_adi TEXT NOT NULL,
            isyeri_servisi TEXT,
            konum TEXT,
            kullanici_id INTEGER,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Veritabanı başlatma hatası: {e}")
    finally:
        if conn:
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
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            if conn is None:
                return jsonify({'success': False, 'message': 'Veritabanı bağlantı hatası'})
                
            cursor = conn.cursor()
            
            isyeri_adi = request.form.get('isyeri_adi')
            isyeri_servisi = request.form.get('isyeri_servisi')
            konum = request.form.get('konum')
            
            cursor.execute("""
                INSERT INTO Isyerleri (isyeri_adi, isyeri_servisi, konum)
                VALUES (?, ?, ?)
            """, (isyeri_adi, isyeri_servisi, konum))
            
            conn.commit()
            return jsonify({'success': True})
        except sqlite3.Error as e:
            return jsonify({'success': False, 'message': str(e)})
        finally:
            if conn:
                conn.close()
    
    return render_template('isyeri_kayit.html')

@app.route('/isyerleri_listele')
def isyerleri_listele():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'Veritabanı bağlantı hatası'})
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, isyeri_adi, isyeri_servisi, konum, 
                   datetime(tarih, 'localtime') as tarih 
            FROM Isyerleri 
            ORDER BY isyeri_adi
        """)
        
        columns = [column[0] for column in cursor.description]
        isyerleri = []
        for row in cursor.fetchall():
            isyeri = dict(zip(columns, row))
            isyerleri.append(isyeri)
            
        return jsonify({'success': True, 'isyerleri': isyerleri})
    except sqlite3.Error as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/isyeri_duzenle/<int:id>', methods=['POST'])
def isyeri_duzenle(id):
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'Veritabanı bağlantı hatası'})
            
        cursor = conn.cursor()
        
        isyeri_adi = request.form.get('isyeri_adi')
        isyeri_servisi = request.form.get('isyeri_servisi')
        konum = request.form.get('konum')
        
        cursor.execute("""
            UPDATE Isyerleri 
            SET isyeri_adi = ?,
                isyeri_servisi = ?,
                konum = ?
            WHERE id = ?
        """, (isyeri_adi, isyeri_servisi, konum, id))
        
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.Error as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/isyeri_sil/<int:id>', methods=['POST'])
def isyeri_sil(id):
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'Veritabanı bağlantı hatası'})
            
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Isyerleri WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.Error as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/')
def index():
    return render_template('index.html')

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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Birimleri getir
        cursor.execute("SELECT id, birim_adi FROM Birimler ORDER BY birim_adi")
        birimler = [{'id': row[0], 'birim_adi': row[1]} for row in cursor.fetchall()]
        
        # Firmaları getir
        cursor.execute("SELECT id, firma_adi FROM Firma ORDER BY firma_adi")
        firmalar = [{'id': row[0], 'firma_adi': row[1]} for row in cursor.fetchall()]
        
        # Geliş nedenlerini getir
        cursor.execute("SELECT id, neden_adi FROM Gelis_Nedeni ORDER BY neden_adi")
        gelis_nedenleri = [{'id': row[0], 'neden_adi': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return render_template('stok_giris.html', 
                             birimler=birimler,
                             firmalar=firmalar,
                             gelis_nedenleri=gelis_nedenleri)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/stok_cikis')
def stok_cikis():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Birimleri getir
        cursor.execute("SELECT id, birim_adi FROM Birimler ORDER BY birim_adi")
        birimler = [{'id': row[0], 'birim_adi': row[1]} for row in cursor.fetchall()]
        
        # İşyerlerini getir
        cursor.execute("SELECT id, isyeri_adi FROM Isyerleri ORDER BY isyeri_adi")
        isyerleri = [{'id': row[0], 'isyeri_adi': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        return render_template('stok_cikis.html', birimler=birimler, isyerleri=isyerleri)
    except Exception as e:
        print(f"Hata: {str(e)}")
        return str(e)

@app.route('/kullanici_kayit')
def kullanici_kayit():
    return render_template('kullanici_kayit.html')

@app.route('/malzeme_ekle', methods=['POST'])
def malzeme_ekle():
    try:
        stok_kodu = request.form.get('stok_kodu')
        malzeme_adi = request.form.get('malzeme_adi')
        aciklama = request.form.get('aciklama')
        
        if not stok_kodu or not malzeme_adi:
            return jsonify({'success': False, 'message': 'Stok kodu ve malzeme adı zorunludur!'})
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Stok kodu benzersiz olmalı
        cursor.execute('SELECT id FROM Malzemeler WHERE stok_kodu = ?', (stok_kodu,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Bu stok kodu zaten kullanımda!'})
        
        cursor.execute('''
            INSERT INTO Malzemeler (stok_kodu, malzeme_adi, aciklama, kullanici_id)
            VALUES (?, ?, ?, ?)
        ''', (stok_kodu, malzeme_adi, aciklama, 1))  # kullanici_id şimdilik sabit 1
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Malzeme başarıyla eklendi.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

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
    try:
        stok_kodu = request.form.get('stok_kodu')
        malzeme_adi = request.form.get('malzeme_adi')
        aciklama = request.form.get('aciklama')
        
        if not stok_kodu or not malzeme_adi:
            return jsonify({'success': False, 'message': 'Stok kodu ve malzeme adı zorunludur!'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Stok kodu benzersizlik kontrolü (kendi ID'si hariç)
        cursor.execute('SELECT id FROM Malzemeler WHERE stok_kodu = ? AND id != ?', (stok_kodu, id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Bu stok kodu başka bir malzeme için kullanımda!'})
        
        cursor.execute('''
            UPDATE Malzemeler 
            SET stok_kodu = ?, malzeme_adi = ?, aciklama = ?
            WHERE id = ?
        ''', (stok_kodu, malzeme_adi, aciklama, id))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Malzeme başarıyla güncellendi.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

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
        cursor.execute('''
            SELECT id, stok_kodu, malzeme_adi, aciklama, tarih
            FROM Malzemeler
            ORDER BY id DESC
        ''')
        malzemeler = []
        for row in cursor.fetchall():
            malzemeler.append({
                'id': row[0],
                'stok_kodu': row[1],
                'malzeme_adi': row[2],
                'aciklama': row[3],
                'tarih': row[4]
            })
        return jsonify({'success': True, 'malzemeler': malzemeler})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/stok_giris_listele')
def stok_giris_listele():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Stok giriş kayıtlarını getir
        cursor.execute("""
            SELECT 
                sg.id,
                sg.stok_kodu,
                sg.malzeme_adi,
                sg.miktar,
                sg.birim_adi,
                sg.firma_isyeri_adi,
                gn.neden_adi as gelis_nedeni,
                sg.islem_tarihi,
                sg.aciklama
            FROM Stok_Giris sg
            LEFT JOIN Gelis_Nedeni gn ON sg.gelis_nedeni_id = gn.id
            ORDER BY sg.id DESC
        """)
        
        columns = [column[0] for column in cursor.description]
        kayitlar = []
        for row in cursor.fetchall():
            kayit = dict(zip(columns, row))
            kayitlar.append(kayit)
            
        # Bugünkü giriş sayısını hesapla
        cursor.execute("""
            SELECT COUNT(*) FROM Stok_Giris 
            WHERE date(islem_tarihi) = date('now')
        """)
        today_count = cursor.fetchone()[0]
        
        conn.close()
        return jsonify({
            'success': True,
            'kayitlar': kayitlar,
            'todayCount': today_count
        })
        
    except Exception as e:
        print(f"Hata: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Kayıtlar getirilirken bir hata oluştu!'
        })

@app.route('/stok_giris_kaydet', methods=['POST'])
def stok_giris_kaydet():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stok_kodu = request.form.get('stok_kodu')
        malzeme_adi = request.form.get('malzeme_adi')
        miktar = request.form.get('miktar')
        birim_adi = request.form.get('birim_adi')
        gelis_nedeni_id = request.form.get('gelis_nedeni_id')
        firma_isyeri_adi = request.form.get('firma_isyeri_adi')
        aciklama = request.form.get('aciklama')
        
        cursor.execute("""
            INSERT INTO Stok_Giris (
                stok_kodu, malzeme_adi, miktar, birim_adi,
                gelis_nedeni_id, firma_isyeri_adi, aciklama
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (stok_kodu, malzeme_adi, miktar, birim_adi,
              gelis_nedeni_id, firma_isyeri_adi, aciklama))
        
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
        print("Hata:", str(e))
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
        
        # Stok çıkış kayıtlarını getir
        cursor.execute("""
            SELECT 
                id,
                stok_kodu,
                malzeme_adi,
                miktar,
                birim_adi,
                isyeri_adi,
                teslim_alan,
                islem_tarihi,
                aciklama
            FROM Stok_Cikis
            ORDER BY id DESC
        """)
        
        columns = [column[0] for column in cursor.description]
        kayitlar = []
        for row in cursor.fetchall():
            kayit = dict(zip(columns, row))
            kayitlar.append(kayit)
            
        # Bugünkü çıkış sayısını hesapla
        cursor.execute("""
            SELECT COUNT(*) FROM Stok_Cikis 
            WHERE date(islem_tarihi) = date('now')
        """)
        today_count = cursor.fetchone()[0]
        
        conn.close()
        return jsonify({
            'success': True,
            'kayitlar': kayitlar,
            'todayCount': today_count
        })
        
    except Exception as e:
        print(f"Hata: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Kayıtlar getirilirken bir hata oluştu!'
        })

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
        
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'Veritabanı bağlantısı kurulamadı!'})
            
        cursor = conn.cursor()
        
        birim_adi = request.form.get('birim_adi')
        aciklama = request.form.get('aciklama')

        if not birim_adi:
            return jsonify({'success': False, 'message': 'Birim adı zorunludur!'})

        # Aynı birim adı var mı kontrol et
        cursor.execute('SELECT id FROM Birimler WHERE birim_adi = ?', (birim_adi,))
        existing = cursor.fetchone()
        
        if existing:
            return jsonify({'success': False, 'message': 'Bu birim adı zaten kayıtlı!'})

        # Yeni birimi kaydet
        cursor.execute('''
            INSERT INTO Birimler (birim_adi, aciklama)
            VALUES (?, ?)
        ''', (birim_adi, aciklama))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Birim başarıyla kaydedildi.'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/birimler_listele')
def birimler_listele():
    try:
        cursor = get_db_connection().cursor()
        cursor.execute('''
            SELECT id, birim_adi, aciklama
            FROM Birimler
            ORDER BY id DESC
        ''')
        
        birimler = []
        for row in cursor.fetchall():
            birimler.append({
                'id': row[0],
                'birim_adi': row[1],
                'aciklama': row[2]
            })
            
        return jsonify({'success': True, 'birimler': birimler})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/birim_duzenle/<int:id>', methods=['POST'])
def birim_duzenle(id):
    try:
        birim_adi = request.form.get('birim_adi')
        aciklama = request.form.get('aciklama')

        if not birim_adi:
            return jsonify({'success': False, 'message': 'Birim adı zorunludur!'})

        # Aynı birim adı başka kayıtta var mı kontrol et
        cursor = get_db_connection().cursor()
        cursor.execute('SELECT id FROM Birimler WHERE birim_adi = ? AND id != ?', (birim_adi, id))
        existing = cursor.fetchone()
        
        if existing:
            return jsonify({'success': False, 'message': 'Bu birim adı zaten kayıtlı!'})

        # Birimi güncelle
        cursor.execute('''
            UPDATE Birimler 
            SET birim_adi = ?, 
                aciklama = ?
            WHERE id = ?
        ''', (birim_adi, aciklama, id))
        
        get_db_connection().commit()
        return jsonify({'success': True, 'message': 'Birim başarıyla güncellendi.'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/birim_sil/<int:id>', methods=['POST'])
def birim_sil(id):
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'Veritabanı bağlantısı kurulamadı!'})
            
        cursor = conn.cursor()
        
        # Birim kullanımda mı kontrol et
        cursor.execute('SELECT id FROM Stok_Giris WHERE birim_adi = (SELECT birim_adi FROM Birimler WHERE id = ?) LIMIT 1', (id,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Bu birim stok giriş kayıtlarında kullanılmış. Silinemez!'})
            
        cursor.execute('SELECT id FROM Stok_Cikis WHERE birim_adi = (SELECT birim_adi FROM Birimler WHERE id = ?) LIMIT 1', (id,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Bu birim stok çıkış kayıtlarında kullanılmış. Silinemez!'})

        # Birimi sil
        cursor.execute('DELETE FROM Birimler WHERE id = ?', (id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Birim başarıyla silindi.'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/stok_giris_detay/<stok_kodu>')
def stok_giris_detay(stok_kodu):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                sg.id,
                sg.stok_kodu,
                sg.malzeme_adi,
                sg.miktar,
                sg.birim_adi,
                strftime('%d.%m.%Y %H:%M', sg.islem_tarihi) as islem_tarihi,
                sg.aciklama
            FROM Stok_Giris sg
            WHERE sg.stok_kodu = ?
            ORDER BY sg.islem_tarihi DESC
        """, (stok_kodu,))
        
        girisler = []
        for row in cursor.fetchall():
            girisler.append({
                'id': row['id'],
                'stok_kodu': row['stok_kodu'],
                'malzeme_adi': row['malzeme_adi'],
                'miktar': row['miktar'],
                'birim_adi': row['birim_adi'],
                'islem_tarihi': row['islem_tarihi'],
                'aciklama': row['aciklama']
            })
            
        return jsonify({"success": True, "girisler": girisler})
    except Exception as e:
        print("Hata:", str(e))
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/son_giris_detay/<stok_kodu>')
def son_giris_detay(stok_kodu):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                sg.islem_tarihi,
                sg.miktar,
                sg.birim_adi,
                sg.gelis_nedeni_id,
                sg.firma_isyeri_adi,
                sg.aciklama
            FROM Stok_Giris sg
            WHERE sg.stok_kodu = ?
            ORDER BY sg.islem_tarihi DESC
            LIMIT 1
        """, (stok_kodu,))
        detay = cursor.fetchone()
        
        if detay:
            return jsonify({
                'success': True,
                'detay': {
                    'islem_tarihi': detay[0],
                    'miktar': detay[1],
                    'birim_adi': detay[2],
                    'gelis_nedeni_id': detay[3],
                    'firma_isyeri_adi': detay[4],
                    'aciklama': detay[5]
                }
            })
        return jsonify({'success': False, 'message': 'Detay bulunamadı'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/son_cikis_detay/<stok_kodu>')
def son_cikis_detay(stok_kodu):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                sc.islem_tarihi,
                sc.miktar,
                sc.birim_adi,
                sc.isyeri_adi,
                sc.teslim_alan,
                sc.aciklama
            FROM Stok_Cikis sc
            WHERE sc.stok_kodu = ?
            ORDER BY sc.islem_tarihi DESC
            LIMIT 1
        """, (stok_kodu,))
        detay = cursor.fetchone()
        
        if detay:
            return jsonify({
                'success': True,
                'detay': {
                    'islem_tarihi': detay[0],
                    'miktar': detay[1],
                    'birim_adi': detay[2],
                    'isyeri_adi': detay[3],
                    'teslim_alan': detay[4],
                    'aciklama': detay[5]
                }
            })
        return jsonify({'success': False, 'message': 'Detay bulunamadı'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower()
        
        # Claude ile mesajı analiz et
        message = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Stok yönetim sistemi asistanı olarak aşağıdaki soruyu yanıtla:

                Soru: {user_message}
                
                Yanıtı Türkçe olarak ver ve emoji kullan. Stok durumu, kritik stoklar, son işlemler ve malzeme bilgileri hakkında bilgi verebilirsin."""
            }]
        )
        
        # Claude'dan gelen yanıtı al
        assistant_response = message.content[0].text
        
        return jsonify({
            'success': True,
            'response': assistant_response
        })
        
    except Exception as e:
        print(f"Hata: {str(e)}")
        return jsonify({
            'success': False,
            'response': '❌ Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.'
        })

@app.route('/gelis_nedeni_kayit', methods=['GET', 'POST'])
def gelis_nedeni_kayit():
    if request.method == 'GET':
        return render_template('gelis_nedeni_kayit.html')
        
    try:
        neden_adi = request.form.get('neden_adi')
        aciklama = request.form.get('aciklama')
        
        if not neden_adi:
            return jsonify({'success': False, 'message': 'Geliş nedeni adı zorunludur!'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Gelis_Nedeni (neden_adi, aciklama)
            VALUES (?, ?)
        """, (neden_adi, aciklama))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Geliş nedeni başarıyla kaydedildi.'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/gelis_nedenleri_listele')
def gelis_nedenleri_listele():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, neden_adi, aciklama, olusturma_tarihi
            FROM Gelis_Nedeni
            ORDER BY neden_adi
        """)
        
        columns = [column[0] for column in cursor.description]
        gelis_nedenleri = []
        
        for row in cursor.fetchall():
            gelis_nedeni = dict(zip(columns, row))
            gelis_nedenleri.append(gelis_nedeni)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'gelis_nedenleri': gelis_nedenleri
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/gelis_nedeni_sil/<int:id>', methods=['POST'])
def gelis_nedeni_sil(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM Gelis_Nedeni WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Geliş nedeni başarıyla silindi.'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/gelis_nedeni_duzenle/<int:id>', methods=['POST'])
def gelis_nedeni_duzenle(id):
    try:
        neden_adi = request.form.get('neden_adi')
        aciklama = request.form.get('aciklama')
        
        if not neden_adi:
            return jsonify({'success': False, 'message': 'Geliş nedeni adı zorunludur!'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Gelis_Nedeni
            SET neden_adi = ?, aciklama = ?
            WHERE id = ?
        """, (neden_adi, aciklama, id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Geliş nedeni başarıyla güncellendi.'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/stok_giris_duzenle/<int:id>', methods=['POST'])
def stok_giris_duzenle(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Önce eski kaydın bilgilerini al
        cursor.execute("SELECT miktar, stok_kodu FROM Stok_Giris WHERE id = ?", (id,))
        eski_kayit = cursor.fetchone()
        
        if not eski_kayit:
            return jsonify({"success": False, "message": "Kayıt bulunamadı!"})
            
        eski_miktar = eski_kayit['miktar']
        eski_stok_kodu = eski_kayit['stok_kodu']
        
        # Yeni değerleri al
        stok_kodu = request.form.get('stok_kodu')
        malzeme_adi = request.form.get('malzeme_adi')
        yeni_miktar = int(request.form.get('miktar'))
        birim_adi = request.form.get('birim_adi')
        gelis_nedeni_id = request.form.get('gelis_nedeni_id')
        firma_isyeri_adi = request.form.get('firma_isyeri_adi')
        aciklama = request.form.get('aciklama')
        
        # Stok giriş kaydını güncelle
        cursor.execute("""
            UPDATE Stok_Giris 
            SET stok_kodu = ?, 
                malzeme_adi = ?, 
                miktar = ?,
                birim_adi = ?,
                gelis_nedeni_id = ?,
                firma_isyeri_adi = ?,
                aciklama = ?
            WHERE id = ?
        """, (stok_kodu, malzeme_adi, yeni_miktar, birim_adi,
              gelis_nedeni_id, firma_isyeri_adi, aciklama, id))
        
        # Stok tablosunu güncelle
        miktar_farki = yeni_miktar - eski_miktar
        
        # Eğer stok kodu değiştiyse eski stok kodundan düş, yeni stok koduna ekle
        if eski_stok_kodu != stok_kodu:
            # Eski stok kodundan miktarı düş
            cursor.execute("""
                UPDATE Stok 
                SET miktar = miktar - ?,
                    son_miktar = ?,
                    son_islem_tarihi = CURRENT_TIMESTAMP
                WHERE stok_kodu = ?
            """, (eski_miktar, eski_miktar, eski_stok_kodu))
            
            # Yeni stok koduna miktarı ekle
            cursor.execute("""
                UPDATE Stok 
                SET miktar = COALESCE(miktar, 0) + ?,
                    son_miktar = ?,
                    son_islem_tarihi = CURRENT_TIMESTAMP
                WHERE stok_kodu = ?
            """, (yeni_miktar, yeni_miktar, stok_kodu))
        else:
            # Aynı stok kodu ise sadece miktar farkını güncelle
            cursor.execute("""
                UPDATE Stok 
                SET miktar = miktar + ?,
                    son_miktar = ?,
                    son_islem_tarihi = CURRENT_TIMESTAMP
                WHERE stok_kodu = ?
            """, (miktar_farki, yeni_miktar, stok_kodu))
        
        conn.commit()
        return jsonify({"success": True, "message": "Kayıt başarıyla güncellendi."})
        
    except Exception as e:
        print("Hata:", str(e))
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/stok_cikis_duzenle/<int:id>', methods=['POST'])
def stok_cikis_duzenle(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Önce eski kaydın bilgilerini al
        cursor.execute("SELECT miktar, stok_kodu FROM Stok_Cikis WHERE id = ?", (id,))
        eski_kayit = cursor.fetchone()
        
        if not eski_kayit:
            return jsonify({"success": False, "message": "Kayıt bulunamadı!"})
            
        eski_miktar = eski_kayit['miktar']
        eski_stok_kodu = eski_kayit['stok_kodu']
        
        # Yeni değerleri al
        stok_kodu = request.form.get('stok_kodu')
        malzeme_adi = request.form.get('malzeme_adi')
        yeni_miktar = int(request.form.get('miktar'))
        birim_adi = request.form.get('birim_adi')
        isyeri_adi = request.form.get('isyeri_adi')
        teslim_alan = request.form.get('teslim_alan')
        aciklama = request.form.get('aciklama')
        
        # Stok kontrolü
        if eski_stok_kodu != stok_kodu:
            # Yeni stok kodu için stok kontrolü
            cursor.execute("SELECT miktar FROM Stok WHERE stok_kodu = ?", (stok_kodu,))
            yeni_stok = cursor.fetchone()
            if not yeni_stok or yeni_stok['miktar'] < yeni_miktar:
                return jsonify({"success": False, "message": "Yetersiz stok!"})
        else:
            # Aynı stok kodu için miktar kontrolü
            cursor.execute("SELECT miktar FROM Stok WHERE stok_kodu = ?", (stok_kodu,))
            mevcut_stok = cursor.fetchone()
            if mevcut_stok['miktar'] + eski_miktar < yeni_miktar:
                return jsonify({"success": False, "message": "Yetersiz stok!"})
        
        # Stok çıkış kaydını güncelle
        cursor.execute("""
            UPDATE Stok_Cikis 
            SET stok_kodu = ?, 
                malzeme_adi = ?, 
                miktar = ?,
                birim_adi = ?,
                isyeri_adi = ?,
                teslim_alan = ?,
                aciklama = ?
            WHERE id = ?
        """, (stok_kodu, malzeme_adi, yeni_miktar, birim_adi,
              isyeri_adi, teslim_alan, aciklama, id))
        
        # Stok tablosunu güncelle
        if eski_stok_kodu != stok_kodu:
            # Eski stok koduna miktarı geri ekle
            cursor.execute("""
                UPDATE Stok 
                SET miktar = miktar + ?,
                    son_miktar = ?,
                    son_islem_tarihi = CURRENT_TIMESTAMP
                WHERE stok_kodu = ?
            """, (eski_miktar, eski_miktar, eski_stok_kodu))
            
            # Yeni stok kodundan miktarı düş
            cursor.execute("""
                UPDATE Stok 
                SET miktar = miktar - ?,
                    son_miktar = ?,
                    son_islem_tarihi = CURRENT_TIMESTAMP
                WHERE stok_kodu = ?
            """, (yeni_miktar, yeni_miktar, stok_kodu))
        else:
            # Aynı stok kodu için miktar farkını güncelle
            miktar_farki = yeni_miktar - eski_miktar
            cursor.execute("""
                UPDATE Stok 
                SET miktar = miktar - ?,
                    son_miktar = ?,
                    son_islem_tarihi = CURRENT_TIMESTAMP
                WHERE stok_kodu = ?
            """, (miktar_farki, yeni_miktar, stok_kodu))
        
        conn.commit()
        return jsonify({"success": True, "message": "Kayıt başarıyla güncellendi."})
        
    except Exception as e:
        print("Hata:", str(e))
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/birimler_combo')
def birimler_combo():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, birim_adi
            FROM Birimler
            ORDER BY birim_adi
        """)
        birimler = [{'id': row[0], 'birim_adi': row[1]} for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'birimler': birimler})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/isyerleri_combo')
def isyerleri_combo():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, isyeri_adi
            FROM Isyerleri
            ORDER BY isyeri_adi
        """)
        isyerleri = [{'id': row[0], 'isyeri_adi': row[1]} for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'isyerleri': isyerleri})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/stok_cikis_detay/<stok_kodu>')
def stok_cikis_detay(stok_kodu):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                sc.id,
                sc.stok_kodu,
                sc.malzeme_adi,
                sc.miktar,
                sc.birim_adi,
                sc.isyeri_adi,
                sc.teslim_alan,
                strftime('%d.%m.%Y %H:%M', sc.islem_tarihi) as islem_tarihi,
                sc.aciklama
            FROM Stok_Cikis sc
            WHERE sc.stok_kodu = ?
            ORDER BY sc.islem_tarihi DESC
        """, (stok_kodu,))
        
        cikislar = []
        for row in cursor.fetchall():
            cikislar.append({
                'id': row['id'],
                'stok_kodu': row['stok_kodu'],
                'malzeme_adi': row['malzeme_adi'],
                'miktar': row['miktar'],
                'birim_adi': row['birim_adi'],
                'isyeri_adi': row['isyeri_adi'],
                'teslim_alan': row['teslim_alan'],
                'islem_tarihi': row['islem_tarihi'],
                'aciklama': row['aciklama']
            })
            
        return jsonify({"success": True, "cikislar": cikislar})
    except Exception as e:
        print("Hata:", str(e))
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

if __name__ == '__main__':
    init_db() 
    app.run('10.35.3.7', port=5000, debug=True)

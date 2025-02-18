from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

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
    cursor.execute('''CREATE TABLE IF NOT EXISTS Isyerleri (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        isyeri_adi TEXT NOT NULL,
                        isyeri_servisi TEXT,
                        konum TEXT,
                        kullanici_id INTEGER,
                        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stok_kodu TEXT UNIQUE NOT NULL,
                        malzeme_id INTEGER,
                        miktar REAL,
                        islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        kullanici_id INTEGER,
                        FOREIGN KEY (malzeme_id) REFERENCES Malzemeler(id)
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

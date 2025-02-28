from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)  # Frontend'den gelen isteklere izin vermek için

# Veritabanı bağlantısı
def get_db_connection():
    conn = sqlite3.connect('your_database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanı metadata'sını çıkarma
def extract_db_schema():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tüm tabloları al
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema = {}
    for table in tables:
        table_name = table['name']
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schema[table_name] = {
            'columns': [column['name'] for column in columns],
            'types': [column['type'] for column in columns]
        }
    
    conn.close()
    return schema

# API Endpoint'leri
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    # 1. Kullanıcı sorusunu al
    # 2. NLP/LLM ile sorguya dönüştür
    query = natural_language_to_sql(user_message)
    
    # 3. Sorguyu çalıştır
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        # 4. Sonuçları kullanıcı dostu formatta döndür
        formatted_response = format_query_results(results, user_message)
        return jsonify({"response": formatted_response, "success": True})
    
    except Exception as e:
        return jsonify({"response": f"Sorgunuz işlenirken bir hata oluştu: {str(e)}", "success": False})

# Ana sayfa
@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)

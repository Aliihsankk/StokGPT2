# OpenAI API için bağlantı
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def natural_language_to_sql(user_question):
    """Kullanıcı sorusunu SQL sorgusuna dönüştürür"""
    
    # Veritabanı şemasını al
    db_schema = extract_db_schema()
    
    # Şemayı metin formatına dönüştür
    schema_text = ""
    for table, info in db_schema.items():
        columns_with_types = [f"{col} ({typ})" for col, typ in zip(info['columns'], info['types'])]
        schema_text += f"Table: {table}\nColumns: {', '.join(columns_with_types)}\n\n"
    
    # LLM'e gönderilecek prompt
    prompt = f"""
    Veritabanı Şeması:
    {schema_text}
    
    Kullanıcı Sorusu: {user_question}
    
    Bu soruya cevap verebilecek bir SQLite sorgusu oluştur. 
    Sadece SQL sorgusunu döndür, başka açıklama ekleme.
    """
    
    # OpenAI API ile sorguyu oluştur
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sen bir SQL sorgusu oluşturan asistansın."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    # Yanıttan SQL sorgusunu çıkar
    sql_query = response.choices[0].message.content.strip()
    
    # Güvenlik kontrolü (Basit bir örnek - gerçek uygulamada daha kapsamlı olmalı)
    disallowed_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
    if any(keyword in sql_query.upper() for keyword in disallowed_keywords):
        return "SELECT 'Bu sorgu güvenlik nedeniyle çalıştırılamadı' as message"
    
    return sql_query

def format_query_results(results, original_question):
    """Sorgu sonuçlarını kullanıcı dostu bir metne dönüştürür"""
    
    if not results:
        return "Sorgunuza uygun bir sonuç bulunamadı."
    
    # Sonuçları metin formatına dönüştür
    result_list = [dict(row) for row in results]
    
    # LLM ile sonuçları yorumlama
    result_text = str(result_list)
    
    prompt = f"""
    Kullanıcı Sorusu: {original_question}
    
    Veritabanı Sorgu Sonuçları: {result_text}
    
    Bu sonuçları kullanıcının anlayabileceği doğal bir dilde açıkla.
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sen bir veritabanı analisti asistanısın."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

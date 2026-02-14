from flask import Flask, render_template, request, jsonify
import psycopg2
from urllib.parse import urlparse
import os

app = Flask(__name__)

# Pega a URL do banco (já configurada no Render)
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Conecta ao Neon - VERSÃO SIMPLIFICADA"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL não encontrada!")
        return None
    
    try:
        # Conexão direta com a URL completa (mais simples!)
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Conectado ao Neon com sucesso!")
        return conn
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None

# Rota principal
@app.route('/')
def home():
    return render_template('index.html')

# Rota de teste da conexão
@app.route('/testar-banco')
def testar_banco():
    conn = get_db_connection()
    if conn:
        conn.close()
        return "✅ Banco conectado!"
    return "❌ Falha na conexão"

# Rota de status detalhado
@app.route('/status')
def status():
    conn = get_db_connection()
    status_info = {
        'app': 'online',
        'ambiente': 'production',
        'database_url': 'configurada' if DATABASE_URL else 'não configurada'
    }
    
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT version()")
            status_info['database'] = 'conectado'
            status_info['versao'] = str(cur.fetchone()[0])[:50] + '...'
            cur.close()
            conn.close()
        except Exception as e:
            status_info['database'] = 'erro'
            status_info['erro'] = str(e)
    else:
        status_info['database'] = 'falha conexão'
    
    return jsonify(status_info)

# Suas rotas CRUD aqui...
# [cole aqui as rotas /clientes, /clientes/<id>, etc que você já tem]



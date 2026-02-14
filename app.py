from flask import Flask, render_template, request, jsonify
import psycopg2
from urllib.parse import urlparse
import os

app = Flask(__name__)

# Pega a URL do banco (já configurada no Render)
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Conecta ao Neon - APENAS PRODUÇÃO, sem fallback local"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL não configurada no ambiente!")
        return None
    
    try:
        # Conexão direta com a URL completa (funciona com Neon)
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Conectado ao Neon!")
        return conn
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None

# Rota principal
@app.route('/')
def home():
    return render_template('index.html')

# GET - Listar todos os clientes
@app.route('/clientes')
def get_clientes():
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Falha na conexão com o banco'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM clientes ORDER BY id DESC")
        rows = cur.fetchall()
        
        clientes = []
        for row in rows:
            clientes.append({
                'id': row[0],
                'nome': row[1],
                'email': row[2],
                'telefone': row[3],
                'data_cadastro': str(row[4]) if row[4] else None
            })
        
        cur.close()
        conn.close()
        return jsonify(clientes)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# POST - Adicionar cliente
@app.route('/clientes', methods=['POST'])
def add_cliente():
    data = request.json
    
    if not data.get('nome') or not data.get('email'):
        return jsonify({'erro': 'Nome e email são obrigatórios'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Falha na conexão com o banco'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO clientes (nome, email, telefone) VALUES (%s, %s, %s) RETURNING id",
            (data['nome'], data['email'], data.get('telefone', ''))
        )
        id_novo = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'id': id_novo, 'msg': 'Cliente adicionado com sucesso!'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# PUT - Atualizar cliente
@app.route('/clientes/<int:id>', methods=['PUT'])
def update_cliente(id):
    data = request.json
    
    if not data.get('nome') or not data.get('email'):
        return jsonify({'erro': 'Nome e email são obrigatórios'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Falha na conexão com o banco'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE clientes SET nome=%s, email=%s, telefone=%s WHERE id=%s",
            (data['nome'], data['email'], data.get('telefone', ''), id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'msg': 'Cliente atualizado com sucesso!'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# DELETE - Remover cliente
@app.route('/clientes/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Falha na conexão com o banco'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'msg': 'Cliente removido com sucesso!'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# Rota para verificar status (útil pra debug)
@app.route('/status')
def status():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM clientes")
            total = cur.fetchone()[0]
            cur.close()
            conn.close()
            return jsonify({
                'status': 'online',
                'database': 'conectado',
                'total_clientes': total
            })
        except Exception as e:
            return jsonify({
                'status': 'online',
                'database': 'erro',
                'erro': str(e)
            })
    else:
        return jsonify({
            'status': 'online',
            'database': 'desconectado'
        })

# Só executa em desenvolvimento local
if __name__ == '__main__':
    app.run(debug=True)

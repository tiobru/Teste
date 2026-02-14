from flask import Flask, render_template, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Pega a URL do banco do ambiente (Render)
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Conecta ao Neon - SEM LOCALHOST, só produção"""
    if not DATABASE_URL:
        print("❌ ERRO: DATABASE_URL não configurada!")
        return None
    
    try:
        # Conexão direta com Neon (simples e funcional)
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Conectado ao Neon!")
        return conn
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None

def criar_tabela():
    """Cria a tabela clientes se não existir"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                telefone VARCHAR(20),
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tabela 'clientes' criada/verificada")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        return False

# Rota principal - serve o HTML
@app.route('/')
def home():
    return render_template('index.html')

# GET - Listar todos os clientes
@app.route('/clientes', methods=['GET'])
def get_clientes():
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Banco de dados indisponível'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, telefone, data_cadastro FROM clientes ORDER BY id DESC")
        rows = cur.fetchall()
        
        clientes = []
        for row in rows:
            clientes.append({
                'id': row[0],
                'nome': row[1],
                'email': row[2],
                'telefone': row[3] or '',
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
        return jsonify({'erro': 'Falha na conexão'}), 500
    
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
        
        return jsonify({'id': id_novo, 'msg': 'Cliente adicionado!'})
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
        return jsonify({'erro': 'Falha na conexão'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE clientes SET nome=%s, email=%s, telefone=%s WHERE id=%s",
            (data['nome'], data['email'], data.get('telefone', ''), id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'msg': 'Cliente atualizado!'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# DELETE - Remover cliente
@app.route('/clientes/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'erro': 'Falha na conexão'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'msg': 'Cliente removido!'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# Rota de diagnóstico
@app.route('/status')
def status():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM clientes")
            total = cur.fetchone()[0]
            cur.execute("SELECT current_database()")
            db_name = cur.fetchone()[0]
            cur.close()
            conn.close()
            return jsonify({
                'status': 'online',
                'database': 'conectado',
                'banco': db_name,
                'total_clientes': total,
                'ambiente': 'produção'
            })
        except Exception as e:
            return jsonify({'status': 'erro', 'erro': str(e)})
    else:
        return jsonify({
            'status': 'erro',
            'database': 'desconectado',
            'DATABASE_URL': 'configurada' if DATABASE_URL else 'não configurada'
        })

# Inicialização
if __name__ == '__main__':
    criar_tabela()  # Cria a tabela ao iniciar
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



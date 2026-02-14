from flask import Flask, render_template, request, jsonify
import psycopg2
from urllib.parse import urlparse
import os

app = Flask(__name__)

# 🔧 CONFIGURAÇÃO PARA RENDER + NEON
# Usa variável de ambiente no Render, fallback para local
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Conecta ao banco (Neon na nuvem, nunca localhost em produção)"""
    if DATABASE_URL:  # MODO PRODUÇÃO (Render)
        try:
            url = urlparse(DATABASE_URL)
            conn = psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port or 5432,
                sslmode='require'  # ESSENCIAL para Neon!
            )
            print("✅ Conectado ao Neon PostgreSQL")
            return conn
        except Exception as e:
            print(f"❌ Erro ao conectar ao Neon: {e}")
            return None
    else:  # MODO DESENVOLVIMENTO (seu PC local)
        print("⚠️  Modo desenvolvimento - usando banco local")
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="1234",
                port="5433"
            )
            print("✅ Conectado ao PostgreSQL local")
            return conn
        except Exception as e:
            print(f"❌ Erro ao conectar localmente: {e}")
            return None

def criar_tabela():
    """Cria a tabela se não existir"""
    conn = get_db_connection()
    if not conn:
        print("⚠️  Não foi possível conectar para criar tabela")
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100),
                email VARCHAR(100),
                telefone VARCHAR(20),
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ Tabela 'clientes' criada/verificada")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        return False
    finally:
        if conn:
            conn.close()

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
        
        # Converter para dicionários
        clientes = []
        for row in rows:
            clientes.append({
                'id': row[0],
                'nome': row[1],
                'email': row[2],
                'telefone': row[3],
                'data_cadastro': str(row[4]) if row[4] else None
            })
        
        return jsonify(clientes)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

# POST - Adicionar cliente
@app.route('/clientes', methods=['POST'])
def add_cliente():
    data = request.json
    
    # Validação básica
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
        
        # Mensagem diferente para produção/desenvolvimento
        mensagem = "Cliente adicionado ao Neon!" if DATABASE_URL else "Cliente adicionado localmente!"
        
        return jsonify({
            'id': id_novo, 
            'msg': mensagem,
            'ambiente': 'production' if DATABASE_URL else 'development'
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

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
        return jsonify({'msg': 'Cliente atualizado'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

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
        return jsonify({'msg': 'Cliente removido'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Rota para verificar status
@app.route('/status')
def status():
    """Verifica status da aplicação e banco"""
    conn = get_db_connection()
    
    status_info = {
        'app': 'online',
        'ambiente': 'production' if DATABASE_URL else 'development',
        'database_url_configurada': bool(DATABASE_URL)
    }
    
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT version()")
            status_info['database'] = 'online'
            status_info['postgres_version'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM clientes")
            status_info['total_clientes'] = cur.fetchone()[0]
            
            cur.execute("SELECT current_database()")
            status_info['database_name'] = cur.fetchone()[0]
            
            conn.close()
        except Exception as e:
            status_info['database'] = 'error'
            status_info['database_error'] = str(e)
    else:
        status_info['database'] = 'offline'
    
    return jsonify(status_info)

# Iniciar app
if __name__ == '__main__':
    # Criar tabela se não existir
    criar_tabela()
    
    # Configuração do servidor
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 50)
    print("🚀 SISTEMA DE CADASTRO DE CLIENTES")
    print("=" * 50)
    
    if DATABASE_URL:
        print("🌐 Ambiente: PRODUÇÃO (Render + Neon)")
        print("💾 Banco: Neon PostgreSQL na nuvem")
    else:
        print("💻 Ambiente: DESENVOLVIMENTO (local)")
        print("💾 Banco: PostgreSQL local (porta 5433)")
    
    print(f"🔧 Porta: {port}")
    print(f"🐛 Debug: {debug_mode}")
    print("=" * 50)
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=port, debug=debug_mode)


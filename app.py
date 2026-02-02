from flask import Flask, render_template, request, jsonify
import psycopg2

app = Flask(__name__)

# Configuração SIMPLES do banco - altere conforme seu setup
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "123"  # Use uma senha sem caracteres especiais
DB_PORT = "5433"

def get_db():
    """Conecta ao banco de dados"""
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def criar_tabela():
    """Cria a tabela se não existir"""
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100),
                email VARCHAR(100),
                telefone VARCHAR(20)
            )
        """)
        conn.commit()
        print("Tabela criada/verificada") 
    except Exception as e:
        print(f"Erro: {e}")
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
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clientes ORDER BY id")
        rows = cur.fetchall()
        
        # Converter para dicionários
        clientes = []
        for row in rows:
            clientes.append({
                'id': row[0],
                'nome': row[1],
                'email': row[2],
                'telefone': row[3]
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
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO clientes (nome, email, telefone) VALUES (%s, %s, %s) RETURNING id",
            (data['nome'], data['email'], data.get('telefone', ''))
        )
        id_novo = cur.fetchone()[0]
        conn.commit()
        return jsonify({'id': id_novo, 'msg': 'Cliente adicionado'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

# PUT - Atualizar cliente
@app.route('/clientes/<int:id>', methods=['PUT'])
def update_cliente(id):
    data = request.json
    conn = None
    try:
        conn = get_db()
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
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id=%s", (id,))
        conn.commit()
        return jsonify({'msg': 'Cliente removido'})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Iniciar app
if __name__ == '__main__':
    criar_tabela()
    print("Servidor rodando em http://localhost:5000")
    app.run(debug=True)
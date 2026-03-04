from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'tecnando_chave_segura'

# --- 1. BANCO DE DADOS (CRIAÇÃO AUTOMÁTICA DE TUDO) ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Tabela de OS
    cursor.execute('''CREATE TABLE IF NOT EXISTS ordens (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        cliente TEXT, telefone TEXT, aparelho TEXT, 
        defeito TEXT, valor REAL, status TEXT DEFAULT 'Aguardando Orçamento')''')
    # Tabela de Estoque
    cursor.execute('''CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        peca TEXT, quantidade INTEGER, preco REAL)''')
    # Tabela de Financeiro
    cursor.execute('''CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        descricao TEXT, valor REAL, tipo TEXT, data DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. FUNÇÃO AUXILIAR PARA O WHATSAPP ---
def gerar_link_zap(telefone, id_os, cliente, aparelho):
    msg = f"Olá {cliente}, sua OS #{id_os} do aparelho {aparelho} foi atualizada no sistema da Técnando!"
    # Remove caracteres estranhos do telefone
    num = ''.join(filter(str.isdigit, str(telefone)))
    return f"https://api.whatsapp.com/send?phone=55{num}&text={msg}"

# --- 3. ROTAS DE ORDENS DE SERVIÇO ---
@app.route('/')
@app.route('/ordens')
def listar_ordens():
    busca = request.args.get('busca', '')
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if busca:
        cursor.execute("SELECT * FROM ordens WHERE cliente LIKE ? OR aparelho LIKE ? OR id LIKE ?", 
                       (f'%{busca}%', f'%{busca}%', f'%{busca}%'))
    else:
        cursor.execute("SELECT * FROM ordens ORDER BY id DESC")
    
    # Preparando os dados para o HTML (incluindo o link do Zap)
    ordens_data = []
    for row in cursor.fetchall():
        d = dict(row)
        d['zap_link'] = gerar_link_zap(d['telefone'], d['id'], d['cliente'], d['aparelho'])
        ordens_data.append(d)
        
    conn.close()
    return render_template('ordens.html', ordens=ordens_data)

@app.route('/inserir', methods=['POST'])
def inserir_ordem():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO ordens (cliente, telefone, aparelho, defeito, valor) VALUES (?, ?, ?, ?, ?)',
                   (request.form['cliente'], request.form['telefone'], request.form['equipamento'], 
                    request.form['defeito'], request.form['valor'] or 0))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_ordens'))

@app.route('/status/<int:id>/<novo_status>')
def mudar_status(id, novo_status):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE ordens SET status = ? WHERE id = ?', (novo_status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_ordens'))

@app.route('/excluir/<int:id>')
def excluir_ordem(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ordens WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_ordens'))

# --- 4. ROTAS DE ESTOQUE ---
@app.route('/estoque')
def listar_estoque():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM estoque ORDER BY peca ASC")
    itens = cursor.fetchall()
    conn.close()
    return render_template('estoque.html', estoque=itens)

@app.route('/inserir_estoque', methods=['POST'])
def inserir_estoque():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO estoque (peca, quantidade, preco) VALUES (?, ?, ?)',
                   (request.form['peca'], request.form['quantidade'], request.form['preco'] or 0))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_estoque'))

@app.route('/excluir_estoque/<int:id>')
def excluir_estoque(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM estoque WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('listar_estoque'))

# --- 5. OUTRAS FUNÇÕES ---
@app.route('/imprimir/<int:id>')
def imprimir(id):
    # Aqui você pode integrar com o ReportLab ou apenas abrir uma tela de impressão
    return f"<h1>Imprimindo OS #{id}</h1><script>window.print();</script>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('listar_ordens'))

@app.route('/financeiro')
def financeiro():
    # Rota básica para não dar erro 404
    return "<h1>Financeiro em Breve</h1><a href='/'>Voltar</a>"

if __name__ == '__main__':
    app.run(debug=True)
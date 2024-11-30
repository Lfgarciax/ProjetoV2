from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secreta-chave'  # Necessário para mensagens flash
DATABASE = 'tasks.db'

# Função de conexão com o banco de dados
def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Acessar colunas pelo nome
    return conn

# Rota principal: Exibir tarefas
@app.route('/')
def index():
    # Parâmetros de busca, ordenação e filtro
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'priority')  # Padrão: prioridade
    filter_value = request.args.get('filter_value', 'Todos')  # Valor atual do filtro

    # Colunas válidas para ordenação
    valid_columns = ['title', 'description', 'category', 'priority', 'status', 'created_at']
    if sort_by not in valid_columns:
        sort_by = 'priority'

    # Conexão ao banco
    conn = connect_db()
    cursor = conn.cursor()

    # Consulta SQL com busca, filtro e ordenação
    query = f"SELECT * FROM tasks"
    parameters = []

    if search_query:
        query += " WHERE title LIKE ? OR description LIKE ?"
        parameters.extend([f"%{search_query}%", f"%{search_query}%"])
    elif filter_value != 'Todos' and sort_by in ['category', 'priority', 'status']:
        query += f" WHERE {sort_by} = ?"
        parameters.append(filter_value)

    query += f" ORDER BY {sort_by} ASC"
    cursor.execute(query, parameters)

    tasks = cursor.fetchall()

    # Próxima opção para o filtro
    if sort_by == 'priority':
        options = ['Todos', 'Alta', 'Média', 'Baixa']
    elif sort_by == 'category':
        options = ['Todos', 'Trabalho', 'Pessoal', 'Urgente']
    elif sort_by == 'status':
        options = ['Todos', 'Pendente', 'Concluído']
    else:
        options = []

    next_filter_value = None
    if options:
        current_index = options.index(filter_value) if filter_value in options else 0
        next_filter_value = options[(current_index + 1) % len(options)]

    conn.close()

    return render_template('index.html', tasks=tasks, sort_by=sort_by, filter_value=filter_value,
                           next_filter_value=next_filter_value, search_query=search_query)

# Adicionar tarefa
@app.route('/add', methods=['POST'])
def add_task():
    title = request.form['title']
    description = request.form.get('description', '')
    category = request.form.get('category', 'Outros')
    priority = request.form.get('priority', 'Média')
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, description, category, priority, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, description, category, priority, 'Pendente', created_at, created_at))
    conn.commit()
    conn.close()
    flash('Tarefa adicionada com sucesso!', 'success')
    return redirect(url_for('index'))

# Alternar status
@app.route('/toggle_status/<int:task_id>', methods=['POST'])
def toggle_status(task_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    # Alternar entre Pendente e Concluído
    new_status = 'Concluído' if task['status'] == 'Pendente' else 'Pendente'
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()
    flash('Status da tarefa atualizado!', 'info')
    return redirect(url_for('index'))

# Editar tarefa
@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    conn = connect_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        priority = request.form['priority']
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            UPDATE tasks
            SET title = ?, description = ?, category = ?, priority = ?, updated_at = ?
            WHERE id = ?
        """, (title, description, category, priority, updated_at, task_id))
        conn.commit()
        conn.close()
        flash('Tarefa editada com sucesso!', 'success')
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    return render_template('edit.html', task=task)

# Excluir tarefa
@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    flash('Tarefa excluída com sucesso!', 'danger')
    return redirect(url_for('index'))

# Inicializar banco de dados
if __name__ == '__main__':
    conn = connect_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        priority TEXT,
        status TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.close()
    app.run(debug=True)

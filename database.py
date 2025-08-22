# database.py
import sqlite3
from datetime import datetime

DB_NAME = "chamados.db"

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Cria as tabelas do banco de dados se elas não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de Obras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_obra TEXT NOT NULL,
            endereco TEXT,
            cidade TEXT,
            estado TEXT
        )
    """)
    
    # Tabela de Chamados (adicionamos a coluna obra_id)
    # CUIDADO: Em um projeto real, alterar uma tabela existente (ALTER TABLE) é mais complexo.
    # Para este projeto, vamos assumir que estamos começando do zero ou podemos apagar o .db e recriá-lo.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            obra_id INTEGER,
            titulo TEXT NOT NULL,
            solicitante TEXT NOT NULL,
            data_solicitacao TEXT NOT NULL,
            descricao TEXT NOT NULL,
            status TEXT NOT NULL,
            previsao_retorno TEXT,
            responsavel_analise TEXT,
            data_analise TEXT,
            resultado TEXT,
            razao_negativa TEXT,
            FOREIGN KEY (obra_id) REFERENCES obras (id)
        )
    """)
    conn.commit()
    conn.close()

# --- Funções para Obras ---

def adicionar_obra(nome, endereco, cidade, estado):
    """Adiciona uma nova obra ao banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO obras (nome_obra, endereco, cidade, estado) VALUES (?, ?, ?, ?)",
        (nome, endereco, cidade, estado)
    )
    conn.commit()
    conn.close()

def listar_obras():
    """Retorna todas as obras do banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM obras ORDER BY nome_obra ASC")
    obras = cursor.fetchall()
    conn.close()
    return obras

# --- Funções para Chamados (MODIFICADA) ---

def adicionar_chamado(obra_id, titulo, solicitante, descricao, previsao_retorno):
    """Adiciona um novo chamado, agora vinculado a uma obra."""
    conn = get_db_connection()
    cursor = conn.cursor()
    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO chamados (obra_id, titulo, solicitante, data_solicitacao, descricao, status, previsao_retorno) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (obra_id, titulo, solicitante, data_hoje, descricao, "Novo", previsao_retorno)
    )
    conn.commit()
    conn.close()

# As outras funções (listar_chamados, atualizar_chamado, etc.) continuam iguais.
# ... (mantenha as funções que já existiam aqui)
def listar_chamados():
    """Retorna todos os chamados do banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chamados ORDER BY data_solicitacao DESC")
    chamados = cursor.fetchall()
    conn.close()
    return chamados

def atualizar_chamado(chamado_id, status, responsavel, resultado, razao):
    """Atualiza um chamado existente com os dados da análise."""
    conn = get_db_connection()
    cursor = conn.cursor()
    data_analise = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE chamados
        SET status = ?, responsavel_analise = ?, data_analise = ?, resultado = ?, razao_negativa = ?
        WHERE id = ?
    """, (status, responsavel, data_analise, resultado, razao, chamado_id))
    conn.commit()
    conn.close()

def get_chamado_by_id(chamado_id):
    """Busca um chamado específico pelo seu ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chamados WHERE id = ?", (chamado_id,))
    chamado = cursor.fetchone()
    conn.close()
    return chamado

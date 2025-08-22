# database.py
import sqlite3
from datetime import datetime

DB_NAME = "chamados.db"

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
    return conn

def init_db():
    """Cria a tabela de chamados se ela não existir."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            solicitante TEXT NOT NULL,
            data_solicitacao TEXT NOT NULL,
            descricao TEXT NOT NULL,
            status TEXT NOT NULL,
            previsao_retorno TEXT,
            responsavel_analise TEXT,
            data_analise TEXT,
            resultado TEXT,
            razao_negativa TEXT
        )
    """)
    conn.commit()
    conn.close()

def adicionar_chamado(titulo, solicitante, descricao, previsao_retorno):
    """Adiciona um novo chamado ao banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO chamados (titulo, solicitante, data_solicitacao, descricao, status, previsao_retorno) VALUES (?, ?, ?, ?, ?, ?)",
        (titulo, solicitante, data_hoje, descricao, "Novo", previsao_retorno)
    )
    conn.commit()
    conn.close()

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

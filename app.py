# database.py

import sqlite3
import datetime

DB_NAME = "dados.db"

# --- FUNÇÕES DE CONEXÃO E INICIALIZAÇÃO ---

def get_db_connection():
    """Cria uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Permite acessar as colunas como um dicionário
    return conn

def init_db():
    """Cria as tabelas do banco de dados se elas ainda não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela de obras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_obra TEXT NOT NULL,
            endereco TEXT,
            cidade TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    """)

    # Tabela de chamados
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
            resultado TEXT,
            razao_negativa TEXT,
            FOREIGN KEY (obra_id) REFERENCES obras(id)
        )
    """)

    conn.commit()
    conn.close()

def limpar_db():
    """Limpa todos os registros das tabelas."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chamados")
    cursor.execute("DELETE FROM obras")
    conn.commit()
    conn.close()


# --- FUNÇÕES DE LÓGICA DE NEGÓCIO ---

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
    """Lista todas as obras cadastradas."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM obras")
    obras = cursor.fetchall()
    conn.close()
    return obras

def adicionar_chamado(obra_id, titulo, solicitante, descricao, previsao_retorno):
    """
    Adiciona um novo chamado ao banco de dados.
    A data da solicitação é gerada automaticamente aqui.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # GERA a data atual aqui dentro da função
    data_hoje = datetime.date.today().strftime("%Y-%m-%d")

    cursor.execute(
        "INSERT INTO chamados (obra_id, titulo, solicitante, data_solicitacao, descricao, status, previsao_retorno) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (obra_id, titulo, solicitante, data_hoje, descricao, "Na Fila de Espera", previsao_retorno)
    )
    conn.commit()
    conn.close()


def listar_chamados():
    """
    Lista todos os chamados e retorna os dados
    juntamente com os nomes das colunas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chamados")
    # Retorna uma lista de tuplas, onde a primeira tupla é o nome das colunas
    colunas = [descricao[0] for descricao in cursor.description]
    chamados = cursor.fetchall()
    conn.close()
    return chamados, colunas


def get_chamado_by_id(chamado_id):
    """Busca um chamado pelo ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chamados WHERE id = ?", (chamado_id,))
    chamado = cursor.fetchone()
    conn.close()
    return chamado

def atualizar_chamado(chamado_id, status, responsavel, resultado, razao_negativa):
    """Atualiza o status e a análise de um chamado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE chamados SET status = ?, responsavel_analise = ?, resultado = ?, razao_negativa = ? WHERE id = ?",
        (status, responsavel, resultado, razao_negativa, chamado_id)
    )
    conn.commit()
    conn.close()

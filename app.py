# app.py
import streamlit as st
import pandas as pd
from datetime import date
import database as db # Importa nosso módulo de banco de dados

# Inicializa o banco de dados e a tabela
db.init_db()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor de Chamados", layout="wide")
st.title("🚀 Gestor de Solicitações de Alteração de Projetos")

# --- INTERFACE DO USUÁRIO ---

# Opções do menu na barra lateral
menu = ["Abrir Novo Chamado", "Visualizar Chamados"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Abrir Novo Chamado":
    st.subheader("📝 Formulário de Nova Solicitação")

    with st.form("novo_chamado_form", clear_on_submit=True):
        titulo = st.text_input("Título do Chamado")
        solicitante = st.text_input("Seu Nome/Email")
        descricao = st.text_area("Descrição detalhada da alteração")
        previsao_retorno = st.date_input("Previsão de Retorno Desejada", min_value=date.today())

        submitted = st.form_submit_button("Enviar Solicitação")
        if submitted:
            if not all([titulo, solicitante, descricao]):
                st.error("Por favor, preencha todos os campos obrigatórios.")
            else:
                db.adicionar_chamado(titulo, solicitante, descricao, previsao_retorno.strftime("%Y-%m-%d"))
                st.success("Chamado enviado com sucesso!")

elif choice == "Visualizar Chamados":
    st.subheader("📊 Painel de Acompanhamento de Chamados")

    chamados = db.listar_chamados()

    if not chamados:
        st.info("Nenhum chamado encontrado.")
    else:
        # Converte a lista de chamados para um DataFrame do Pandas para melhor visualização
        df = pd.DataFrame(chamados, columns=[desc[0] for desc in db.get_db_connection().execute("PRAGMA table_info(chamados)").fetchall()])
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 Analisar e Atualizar um Chamado")

        # Selecionar um chamado para análise
        ids_chamados = [chamado['id'] for chamado in chamados]
        chamado_id_selecionado = st.selectbox("Selecione o ID do Chamado para analisar:", options=ids_chamados)

        if chamado_id_selecionado:
            chamado_atual = db.get_chamado_by_id(chamado_id_selecionado)
            
            with st.form(f"analise_form_{chamado_id_selecionado}", clear_on_submit=True):
                st.write(f"**Analisando Chamado #{chamado_atual['id']} - {chamado_atual['titulo']}**")
                
                responsavel = st.text_input("Responsável pela Análise", value=st.session_state.get('user', ''))
                status_opcoes = ["Em Análise", "Aprovado", "Negado", "Concluído"]
                status = st.selectbox("Novo Status", options=status_opcoes, index=status_opcoes.index(chamado_atual['status']) if chamado_atual['status'] in status_opcoes else 0)
                
                resultado_opcoes = ["", "Aceito", "Negado"]
                resultado = st.selectbox("Resultado Final", options=resultado_opcoes, index=resultado_opcoes.index(chamado_atual['resultado']) if chamado_atual['resultado'] else 0)

                razao_negativa = st.text_area("Justificativa (se negado)")

                update_button = st.form_submit_button("Salvar Análise")

                if update_button:
                    db.atualizar_chamado(chamado_id_selecionado, status, responsavel, resultado, razao_negativa)
                    st.success(f"Chamado #{chamado_id_selecionado} atualizado com sucesso!")
                    # A página irá recarregar para mostrar os dados atualizados
                    st.experimental_rerun()

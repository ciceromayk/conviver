# app.py
import streamlit as st
import pandas as pd
from datetime import date
import database as db # Importa nosso módulo de banco de dados

# Inicializa o banco de dados e as tabelas
db.init_db()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor de Chamados e Obras", layout="wide")
st.title("🚀 Gestor de Solicitações e Obras")

# --- INTERFACE DO USUÁRIO ---

# Opções do menu na barra lateral
menu = ["Abrir Novo Chamado", "Visualizar Chamados", "Cadastrar Obra"] # Adicionamos a nova página
choice = st.sidebar.selectbox("Menu", menu)

# --- Página: Abrir Novo Chamado (MODIFICADA) ---
if choice == "Abrir Novo Chamado":
    st.subheader("📝 Formulário de Nova Solicitação")
    
    # Busca a lista de obras cadastradas para o selectbox
    obras = db.listar_obras()
    # Formata a lista para exibição (ex: "1 - Obra Central")
    opcoes_obras = {f"{obra['id']} - {obra['nome_obra']}": obra['id'] for obra in obras}

    with st.form("novo_chamado_form", clear_on_submit=True):
        
        # Novo campo para selecionar a obra
        obra_selecionada_str = st.selectbox("Selecione a Obra Relacionada", options=opcoes_obras.keys())
        
        titulo = st.text_input("Título do Chamado")
        solicitante = st.text_input("Seu Nome/Email")
        descricao = st.text_area("Descrição detalhada da alteração")
        previsao_retorno = st.date_input("Previsão de Retorno Desejada", min_value=date.today())

        submitted = st.form_submit_button("Enviar Solicitação")
        if submitted:
            if not all([titulo, solicitante, descricao, obra_selecionada_str]):
                st.error("Por favor, preencha todos os campos obrigatórios, incluindo a seleção da obra.")
            else:
                # Pega o ID da obra selecionada
                obra_id = opcoes_obras[obra_selecionada_str]
                db.adicionar_chamado(obra_id, titulo, solicitante, descricao, previsao_retorno.strftime("%Y-%m-%d"))
                st.success("Chamado enviado com sucesso!")

# --- Página: Cadastrar Obra (NOVA PÁGINA) ---
elif choice == "Cadastrar Obra":
    st.subheader("🏗️ Gestão de Obras")

    # DIALOG (POP-UP) PARA CADASTRO RÁPIDO
    @st.dialog("Cadastro Rápido de Obra")
    def obra_dialog():
        with st.form("form_obra"):
            st.write("Preencha os dados da nova obra.")
            nome = st.text_input("Nome da Obra")
            endereco = st.text_input("Endereço")
            cidade = st.text_input("Cidade")
            estado = st.text_input("Estado (UF)")
            
            if st.form_submit_button("Cadastrar"):
                if nome and cidade and estado:
                    db.adicionar_obra(nome, endereco, cidade, estado)
                    st.rerun() # Recarrega a página para atualizar a lista
                else:
                    st.warning("Nome, Cidade e Estado são obrigatórios.")

    if st.button("➕ Adicionar Nova Obra"):
        obra_dialog()

    st.markdown("---")
    st.subheader("📋 Obras Cadastradas")
    
    # Exibe a lista de obras cadastradas
    lista_de_obras = db.listar_obras()
    if lista_de_obras:
        df_obras = pd.DataFrame(lista_de_obras, columns=['id', 'nome_obra', 'endereco', 'cidade', 'estado'])
        st.dataframe(df_obras, use_container_width=True)
    else:
        st.info("Nenhuma obra cadastrada ainda.")


# --- Página: Visualizar Chamados (sem grandes alterações) ---
elif choice == "Visualizar Chamados":
    st.subheader("📊 Painel de Acompanhamento de Chamados")
    # ... (o código desta página continua o mesmo de antes)
    chamados = db.listar_chamados()

    if not chamados:
        st.info("Nenhum chamado encontrado.")
    else:
        # Converte a lista de chamados para um DataFrame do Pandas para melhor visualização
        df = pd.DataFrame(chamados, columns=[desc[0] for desc in db.get_db_connection().execute("PRAGMA table_info(chamados)").fetchall()])
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 Analisar e Atualizar um Chamado")

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
                    st.rerun()

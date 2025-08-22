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

# --- Gerenciamento de Estado da Página ---
# Define a página inicial se ainda não estiver definida
if 'pagina_ativa' not in st.session_state:
    st.session_state.pagina_ativa = "Visualizar Chamados"
if 'chamado_selecionado_id' not in st.session_state:
    st.session_state.chamado_selecionado_id = None

# --- DEFINIÇÃO DO DIALOG (POP-UP) ---
@st.dialog("Cadastro Rápido de Obra")
def obra_dialog():
    with st.form("form_obra_popup"):
        st.write("Preencha os dados da nova obra.")
        nome = st.text_input("Nome da Obra")
        endereco = st.text_input("Endereço")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado (UF)")
        
        if st.form_submit_button("Cadastrar"):
            if nome and cidade and estado:
                db.adicionar_obra(nome, endereco, cidade, estado)
                st.success("Obra cadastrada com sucesso!") # Mensagem de sucesso
                # O st.rerun() fecha o pop-up e atualiza a aplicação.
                st.rerun()  
            else:
                st.warning("Nome, Cidade e Estado são obrigatórios.")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("Menu")

# Botão para o pop-up de cadastro de obra
if st.sidebar.button("🏗️ Cadastrar Nova Obra", use_container_width=True):
    obra_dialog()

st.sidebar.markdown("---") 

# Botões de navegação que alteram o estado da página
if st.sidebar.button("📊 Visualizar Chamados", use_container_width=True):
    st.session_state.pagina_ativa = "Visualizar Chamados"
if st.sidebar.button("📝 Abrir Novo Chamado", use_container_width=True):
    st.session_state.pagina_ativa = "Abrir Novo Chamado"


# --- CONTEÚDO PRINCIPAL DA PÁGINA (Controlado pelo st.session_state) ---

# --- Página: Visualizar Chamados (AGORA É A PADRÃO) ---
if st.session_state.pagina_ativa == "Visualizar Chamados":
    st.subheader("📊 Painel de Acompanhamento de Chamados")
    
    # A função listar_chamados agora retorna dois valores
    chamados, colunas = db.listar_chamados()

    if not chamados:
        st.info("Nenhum chamado encontrado.")
    else:
        # Cria o DataFrame com os dados e colunas corretos
        df = pd.DataFrame(chamados, columns=colunas)
        
        # Para melhorar a visualização, vamos buscar o nome da obra
        obras = db.listar_obras()
        mapa_obras = {obra['id']: obra['nome_obra'] for obra in obras}
        df['nome_obra'] = df['obra_id'].map(mapa_obras).fillna("Obra não encontrada")
        
        # --- CARDS COM O STATUS DOS CHAMADOS ---
        st.markdown("---")
        st.subheader("Visão Geral")
        
        # Converte as colunas de data para o tipo datetime para comparação
        df['data_solicitacao'] = pd.to_datetime(df['data_solicitacao'])
        df['previsao_retorno'] = pd.to_datetime(df['previsao_retorno'])
        
        # Filtra os chamados que não foram concluídos
        df_abertos = df[df['status'] != 'Concluído']
        
        # Calcula o número de chamados em aberto (não concluídos)
        num_abertos = len(df_abertos)
        
        # Calcula o número de chamados resolvidos (Concluído)
        num_resolvidos = len(df[df['status'] == 'Concluído'])
        
        # Verifica se a previsão de retorno já passou para os chamados em aberto
        hoje = pd.to_datetime(date.today())
        df_abertos_atrasados = df_abertos[df_abertos['previsao_retorno'] < hoje]
        num_atrasados = len(df_abertos_atrasados)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Chamados em Aberto", value=num_abertos)
        with col2:
            st.metric(label="Chamados Concluídos", value=num_resolvidos)
        with col3:
            st.metric(label="Chamados Atrasados", value=num_atrasados)

        # --- GRÁFICOS ---
        st.markdown("---")
        st.subheader("Análise Gráfica")
        col_grafico1, col_grafico2 = st.columns(2)

        with col_grafico1:
            st.bar_chart(df.groupby('status').size().rename("Contagem"))
            st.markdown("<p style='text-align: center;'>Chamados por Status</p>", unsafe_allow_html=True)

        with col_grafico2:
            st.bar_chart(df.groupby('nome_obra').size().rename("Contagem"))
            st.markdown("<p style='text-align: center;'>Chamados por Obra</p>", unsafe_allow_html=True)
        
        
        # --- TABELA INTERATIVA E FORMULÁRIO DE EDIÇÃO ---
        st.markdown("---")
        st.subheader("Tabela de Chamados")
        st.markdown("Selecione um chamado na tabela para analisar.")
        
        # st.data_editor com o callback
        edited_df = st.data_editor(
            df[['id', 'titulo', 'nome_obra', 'solicitante', 'status', 'data_solicitacao', 'previsao_retorno']],
            hide_index=True,
            use_container_width=True,
            column_order=('id', 'titulo', 'nome_obra', 'solicitante', 'status', 'data_solicitacao', 'previsao_retorno'),
            disabled=df.columns, # Desabilita edição direta na tabela
            column_config={
                "id": st.column_config.NumberColumn(label="ID", help="Identificador único do chamado"),
                "titulo": "Título",
                "nome_obra": "Obra",
                "solicitante": "Solicitante",
                "status": "Status",
                "data_solicitacao": "Data da Solicitação",
                "previsao_retorno": "Previsão de Retorno"
            },
            # Adicionando a seleção
            key='data_editor_chamados'
        )
        
        # Detecta se uma linha foi selecionada ou se a seleção mudou
        if st.session_state.data_editor_chamados['selection']['rows']:
            # Pega o ID da linha selecionada
            selected_id = edited_df.loc[st.session_state.data_editor_chamados['selection']['rows'][0], 'id']
            if selected_id != st.session_state.chamado_selecionado_id:
                st.session_state.chamado_selecionado_id = selected_id
                st.rerun() # Reinicia para carregar os dados
        else:
            # Limpa a seleção se nenhuma linha estiver selecionada
            if st.session_state.chamado_selecionado_id is not None:
                st.session_state.chamado_selecionado_id = None
                st.rerun()

        st.markdown("---")
        st.subheader("🔍 Analisar e Atualizar um Chamado")
        
        # Agora o formulário só aparece se um chamado for selecionado
        if st.session_state.chamado_selecionado_id:
            chamado_id_selecionado = st.session_state.chamado_selecionado_id
            chamado_atual = db.get_chamado_by_id(chamado_id_selecionado)
            
            if chamado_atual:
                with st.form(f"analise_form_{chamado_id_selecionado}", clear_on_submit=True):
                    st.write(f"**Analisando Chamado #{chamado_atual['id']} - {chamado_atual['titulo']}**")
                    
                    responsavel = st.text_input("Responsável pela Análise", value=chamado_atual['responsavel_analise'] or "")
                    status_opcoes = ["Novo", "Em Análise", "Aprovado", "Negado", "Concluído"]
                    status_atual = chamado_atual['status'] if chamado_atual['status'] in status_opcoes else "Novo"
                    status = st.selectbox("Novo Status", options=status_opcoes, index=status_opcoes.index(status_atual))
                    
                    resultado_opcoes = ["", "Aceito", "Negado"]
                    resultado_atual = chamado_atual['resultado'] if chamado_atual['resultado'] else ""
                    resultado = st.selectbox("Resultado Final", options=resultado_opcoes, index=resultado_opcoes.index(resultado_atual))

                    razao_negativa = st.text_area("Justificativa (se negado)", value=chamado_atual['razao_negativa'] or "")

                    if st.form_submit_button("Salvar Análise"):
                        db.atualizar_chamado(chamado_id_selecionado, status, responsavel, resultado, razao_negativa)
                        st.success(f"Chamado #{chamado_id_selecionado} atualizado com sucesso!")
                        st.session_state.chamado_selecionado_id = None # Limpa a seleção
                        st.rerun()
            else:
                st.warning("Chamado selecionado não encontrado.")
        else:
            st.info("Selecione um chamado na tabela acima para editar.")

# --- Página: Abrir Novo Chamado ---
elif st.session_state.pagina_ativa == "Abrir Novo Chamado":
    st.subheader("📝 Formulário de Nova Solicitação")
    
    obras = db.listar_obras()
    
    if not obras:
        st.warning("Nenhuma obra cadastrada. Clique em 'Cadastrar Nova Obra' na barra lateral para começar.")
    else:
        opcoes_obras = {f"{obra['id']} - {obra['nome_obra']}": obra['id'] for obra in obras}

        with st.form("novo_chamado_form", clear_on_submit=True):
            
            obra_selecionada_str = st.selectbox("Selecione a Obra Relacionada", options=opcoes_obras.keys())
            titulo = st.text_input("Título do Chamado")
            solicitante = st.text_input("Seu Nome/Email")
            descricao = st.text_area("Descrição detalhada da alteração")
            previsao_retorno = st.date_input("Previsão de Retorno Desejada", min_value=date.today())

            if st.form_submit_button("Enviar Solicitação"):
                obra_id = opcoes_obras[obra_selecionada_str]
                db.adicionar_chamado(obra_id, titulo, solicitante, descricao, previsao_retorno.strftime("%Y-%m-%d"))
                st.success("Chamado enviado com sucesso!")

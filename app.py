# app.py
import streamlit as st
import pandas as pd
from datetime import date
import database as db # Importa nosso módulo de banco de dados
import plotly.express as px

# Inicializa o banco de dados e as tabelas
db.init_db()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor de Chamados e Obras", layout="wide")

# Adiciona um título e uma descrição estilizados
st.markdown("<h1 style='text-align: center; color: #00796B;'>🚀 Gestor de Solicitações e Obras</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #616161;'>Otimize o controle e acompanhamento de chamados e obras da sua empresa.</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Gerenciamento de Estado da Página ---
# Define a página inicial se ainda não estiver definida
if 'pagina_ativa' not in st.session_state:
    st.session_state.pagina_ativa = "Visualizar Chamados"
if 'chamado_selecionado_id' not in st.session_state:
    st.session_state.chamado_selecionado_id = None

# --- DEFINIÇÃO DOS DIALOGS (POP-UPS) ---
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
                st.rerun()  
            else:
                st.warning("Nome, Cidade e Estado são obrigatórios.")

@st.dialog("Abrir Novo Chamado")
def novo_chamado_dialog():
    obras = db.listar_obras()
    
    if not obras:
        st.warning("Nenhuma obra cadastrada. Clique em 'Cadastrar Nova Obra' na barra lateral para começar.")
    else:
        opcoes_obras = {f"{obra['id']} - {obra['nome_obra']}": obra['id'] for obra in obras}

        with st.form("novo_chamado_form", clear_on_submit=True):
            st.write("Preencha os dados da nova solicitação.")
            obra_selecionada_str = st.selectbox("Selecione a Obra Relacionada", options=opcoes_obras.keys())
            titulo = st.text_input("Título do Chamado")
            solicitante = st.text_input("Seu Nome/Email")
            descricao = st.text_area("Descrição detalhada da alteração")
            previsao_retorno = st.date_input("Previsão de Retorno Desejada", min_value=date.today())

            if st.form_submit_button("Enviar Solicitação"):
                obra_id = opcoes_obras[obra_selecionada_str]
                db.adicionar_chamado(obra_id, titulo, solicitante, descricao, previsao_retorno.strftime("%Y-%m-%d"))
                st.success("Chamado enviado com sucesso!")
                st.rerun()

@st.dialog("Editar Status do Chamado")
def editar_chamado_dialog():
    # Lista todos os chamados para que o usuário possa selecionar
    chamados_disponiveis, _ = db.listar_chamados()
    if not chamados_disponiveis:
        st.error("Nenhum chamado disponível para edição.")
        return

    opcoes_chamados = {f"ID {c['id']} - {c['titulo']}": c['id'] for c in chamados_disponiveis}
    chamado_selecionado_str = st.selectbox("Selecione o Chamado para Editar", options=opcoes_chamados.keys())
    
    if chamado_selecionado_str:
        chamado_id_selecionado = opcoes_chamados[chamado_selecionado_str]
        chamado_atual = db.get_chamado_by_id(chamado_id_selecionado)

        if not chamado_atual:
            st.error("Chamado não encontrado.")
            return

        st.markdown(f"**Detalhes do Chamado #{chamado_atual['id']}**")
        with st.form("editar_chamado_form"):
            responsavel = st.text_input("Responsável pela Análise", value=chamado_atual['responsavel_analise'] or "")
            
            # Use o status do banco de dados para controlar o fluxo no pop-up
            current_status = chamado_atual['status']
            current_resultado = chamado_atual['resultado']
            
            # --- Lógica de Edição ---
            new_status = current_status
            new_resultado = current_resultado
            razao_negativa = chamado_atual['razao_negativa']

            # Se o chamado está em fase de triagem (status 'Na Fila de Espera')
            if current_status == "Na Fila de Espera":
                st.markdown(f"**Status Atual:** `{current_status}`")
                step_options = st.radio("Ação:", ["Aprovar", "Negar", "Manter na Fila de Espera"], index=2)
                if step_options == "Aprovar":
                    new_status = "Aprovado"
                    new_resultado = "Aceito"
                elif step_options == "Negar":
                    new_status = "Negado"
                    new_resultado = "Negado"
                else:
                    new_status = "Na Fila de Espera"
            # Se o chamado já foi aprovado e está em execução
            elif current_resultado == "Aceito":
                st.markdown(f"**Status Atual:** `{current_status}`")
                st.write("Ação:")
                step_options = st.radio("Ação:", ["Mover para Em Andamento", "Marcar como Concluído", "Manter Status Atual"])
                if step_options == "Marcar como Concluído":
                    new_status = "Concluído"
                if step_options == "Mover para Em Andamento":
                    new_status = "Em Andamento"
            else:
                 # Chamados negados não podem ser alterados
                st.info(f"Este chamado foi `{current_status}` e não pode ser alterado.")
            
            # Campo de justificativa se a negação for selecionada
            if new_status == "Negado":
                razao_negativa = st.text_area("Justificativa da Negação", value=chamado_atual['razao_negativa'] or "")
                if not razao_negativa:
                    st.warning("A justificativa é obrigatória para chamados negados.")
            else:
                razao_negativa = ""

            if st.form_submit_button("Salvar Alterações"):
                if new_status == "Negado" and not razao_negativa:
                    st.error("Por favor, preencha a justificativa para negar o chamado.")
                else:
                    db.atualizar_chamado(chamado_id_selecionado, new_status, responsavel, new_resultado, razao_negativa)
                    st.success(f"Chamado #{chamado_id_selecionado} atualizado com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhum chamado selecionado.")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("Menu")

# Botões que abrem dialogs
if st.sidebar.button("🏗️ Cadastrar Nova Obra", use_container_width=True):
    obra_dialog()
if st.sidebar.button("📝 Abrir Novo Chamado", use_container_width=True):
    novo_chamado_dialog()
if st.sidebar.button("📝 Editar Chamado", use_container_width=True):
    editar_chamado_dialog()

st.sidebar.markdown("---") 

# Botões de navegação
if st.sidebar.button("📊 Visualizar Chamados", use_container_width=True):
    st.session_state.pagina_ativa = "Visualizar Chamados"

# --- CONTEÚDO PRINCIPAL DA PÁGINA (Controlado pelo st.session_state) ---

# --- Página: Visualizar Chamados (AGORA É A PADRÃO) ---
if st.session_state.pagina_ativa == "Visualizar Chamados":
    st.subheader("📊 Painel de Acompanhamento de Chamados")
    
    chamados, colunas = db.listar_chamados()

    if not chamados:
        st.info("Nenhum chamado encontrado.")
    else:
        df = pd.DataFrame(chamados, columns=colunas)
        obras = db.listar_obras()
        mapa_obras = {obra['id']: obra['nome_obra'] for obra in obras}
        df['nome_obra'] = df['obra_id'].map(mapa_obras).fillna("Obra não encontrada")
        
        # --- CARDS COM OS NOVOS STATUS DOS CHAMADOS ---
        st.markdown("---")
        st.subheader("Visão Geral do Status dos Chamados")
        
        df['data_solicitacao'] = pd.to_datetime(df['data_solicitacao'])
        df['previsao_retorno'] = pd.to_datetime(df['previsao_retorno'])
        
        hoje = pd.to_datetime(date.today())
        
        # Contagem para os novos cards
        num_em_andamento = len(df[df['status'] == 'Em Andamento'])
        num_concluidos = len(df[df['status'] == 'Concluído'])
        num_negados = len(df[df['status'] == 'Negado'])
        
        # Filtra chamados em andamento para verificar prazo
        df_em_andamento = df[df['status'] == 'Em Andamento']
        num_no_prazo = len(df_em_andamento[df_em_andamento['previsao_retorno'] >= hoje])
        num_atrasados = len(df_em_andamento[df_em_andamento['previsao_retorno'] < hoje])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(
                f"<div style='background-color:#E0F7FA; padding:10px; border-radius:10px;'>"
                f"<h3 style='color:#00796B; text-align:center;'>Em Andamento</h3>"
                f"<h1 style='color:#00796B; text-align:center;'>{num_em_andamento}</h1>"
                f"</div>", unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"<div style='background-color:#E8F5E9; padding:10px; border-radius:10px;'>"
                f"<h3 style='color:#2E7D32; text-align:center;'>No Prazo</h3>"
                f"<h1 style='color:#2E7D32; text-align:center;'>{num_no_prazo}</h1>"
                f"</div>", unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                f"<div style='background-color:#FBE9E7; padding:10px; border-radius:10px;'>"
                f"<h3 style='color:#D84315; text-align:center;'>Atrasados</h3>"
                f"<h1 style='color:#D84315; text-align:center;'>{num_atrasados}</h1>"
                f"</div>", unsafe_allow_html=True
            )
        with col4:
            st.markdown(
                f"<div style='background-color:#E8EAF6; padding:10px; border-radius:10px;'>"
                f"<h3 style='color:#3F51B5; text-align:center;'>Concluídos</h3>"
                f"<h1 style='color:#3F51B5; text-align:center;'>{num_concluidos}</h1>"
                f"</div>", unsafe_allow_html=True
            )
        with col5:
            st.markdown(
                f"<div style='background-color:#FFEBEE; padding:10px; border-radius:10px;'>"
                f"<h3 style='color:#C62828; text-align:center;'>Negados</h3>"
                f"<h1 style='color:#C62828; text-align:center;'>{num_negados}</h1></div>", unsafe_allow_html=True
            )


        # --- GRÁFICOS ---
        st.markdown("---")
        with st.expander("📈 Análise Gráfica", expanded=True):
            col_grafico1, col_grafico2 = st.columns(2)

            with col_grafico1:
                df_status = df.groupby('status').size().reset_index(name='Contagem')
                fig_status = px.pie(
                    df_status, 
                    values='Contagem', 
                    names='status', 
                    title='Distribuição por Status',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_status, use_container_width=True)

            with col_grafico2:
                df_obras = df.groupby('nome_obra').size().reset_index(name='Contagem')
                fig_obras = px.pie(
                    df_obras, 
                    values='Contagem', 
                    names='nome_obra', 
                    title='Distribuição por Obra',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_obras, use_container_width=True)
        
        # --- TABELA DE VISUALIZAÇÃO ---
        st.markdown("---")
        st.subheader("Tabela de Chamados")
        st.dataframe(
            df[['id', 'titulo', 'nome_obra', 'solicitante', 'status', 'data_solicitacao', 'previsao_retorno']],
            hide_index=True,
            use_container_width=True
        )

# --- A PÁGINA 'ABRIR NOVO CHAMADO' FOI REMOVIDA, AGORA É UM POP-UP ---

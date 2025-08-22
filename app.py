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
            status_opcoes = ["Novo", "Em Análise", "Aprovado", "Negado", "Concluído"]
            status_atual = chamado_atual['status'] if chamado_atual['status'] in status_opcoes else "Novo"
            status = st.selectbox("Novo Status", options=status_opcoes, index=status_opcoes.index(status_atual))
            
            resultado_opcoes = ["", "Aceito", "Negado"]
            resultado_atual = chamado_atual['resultado'] if chamado_atual['resultado'] else ""
            resultado = st.selectbox("Resultado Final", options=resultado_opcoes, index=resultado_opcoes.index(resultado_atual))

            razao_negativa = st.text_area("Justificativa (se negado)", value=chamado_atual['razao_negativa'] or "")

            if st.form_submit_button("Salvar Alterações"):
                db.atualizar_chamado(chamado_id_selecionado, status, responsavel, resultado, razao_negativa)
                st.success(f"Chamado #{chamado_id_selecionado} atualizado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhum chamado selecionado.")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("Menu")

# Botões que abrem dialogs
if st.sidebar.button("🏗️ Cadastrar Nova Obra", use_container_width=True):
    obra_dialog()
if st.sidebar.button("📝 Editar Chamado", use_container_width=True):
    editar_chamado_dialog()

st.sidebar.markdown("---") 

# Botões de navegação
if st.sidebar.button("📊 Visualizar Chamados", use_container_width=True):
    st.session_state.pagina_ativa = "Visualizar Chamados"
if st.sidebar.button("📝 Abrir Novo Chamado", use_container_width=True):
    st.session_state.pagina_ativa = "Abrir Novo Chamado"


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
        
        # --- CARDS COM O STATUS DOS CHAMADOS ---
        st.markdown("---")
        st.subheader("Visão Geral")
        
        df['data_solicitacao'] = pd.to_datetime(df['data_solicitacao'])
        df['previsao_retorno'] = pd.to_datetime(df['previsao_retorno'])
        df_abertos = df[df['status'] != 'Concluído']
        num_abertos = len(df_abertos)
        num_resolvidos = len(df[df['status'] == 'Concluído'])
        hoje = pd.to_datetime(date.today())
        df_abertos_atrasados = df_abertos[df_abertos['previsao_retorno'] < hoje]
        num_atrasados = len(df_abertos_atrasados)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"<div style='background-color:#E0F7FA; padding:10px; border-radius:10px;'>"
                f"<h3 style='color:#00796B; text-align:center;'>Chamados em Aberto</h3>"
                f"<h1 style='color:#00796B; text-align:center;'>{num_abertos}</h1>"
                f"</div>", unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"<div style='background-color:#E8F5E9; padding:10px; border-radius:10px;'>"
                f"<h3 style='color:#2E7D32; text-align:center;'>Chamados Concluídos</h3>"
                f"<h1 style='color:#2E7D32; text-align:center;'>{num_resolvidos}</h1>"
                f"</div>", unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                f"<div style='background-color:#FBE9E7; padding:10px; border-radius:10px;'>"
                f"<h3 style='color:#D84315; text-align:center;'>Chamados Atrasados</h3>"
                f"<h1 style='color:#D84315; text-align:center;'>{num_atrasados}</h1>"
                f"</div>", unsafe_allow_html=True
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

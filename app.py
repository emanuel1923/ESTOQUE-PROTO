import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Arquivos de banco de dados
DB_FILE = "estoque_dados.csv"
HIST_FILE = "historico_saidas.csv"

# Função para carregar dados do estoque
def carregar_dados():
    colunas = ["Código", "Material", "Qtd", "Categoria"]
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype={'Código': str})
            if not all(col in df.columns for col in colunas):
                return pd.DataFrame(columns=colunas)
            return df.dropna(subset=['Código'])
        except:
            return pd.DataFrame(columns=colunas)
    return pd.DataFrame(columns=colunas)

# Função para carregar histórico de saídas
def carregar_historico():
    if os.path.exists(HIST_FILE):
        try:
            return pd.read_csv(HIST_FILE, dtype={'Código': str})
        except:
            return pd.DataFrame(columns=["Data", "Código", "Material", "Qtd"])
    return pd.DataFrame(columns=["Data", "Código", "Material", "Qtd"])

# Função para salvar arquivos CSV
def salvar_dados(df, arquivo):
    df.to_csv(arquivo, index=False)

st.set_page_config(page_title="Controle de Estoque", layout="wide")

# Inicialização do estado da sessão
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()
if 'historico' not in st.session_state:
    st.session_state.historico = carregar_historico()

st.title("Controle de Estoque v1.0")

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada/Cadastro", "Saída", "Histórico de Saídas", "Gerenciar Estoque"])

# Categorias definidas (Sem Consumíveis)
CATEGORIAS = ["EPI'S", "FERRAMENTAS", "ESCRITÓRIO", "OUTROS"]

if aba == "Visão Geral":
    st.subheader("Itens em Estoque")
    if st.session_state.estoque.empty:
        st.info("O estoque está vazio.")
    else:
        st.dataframe(st.session_state.estoque, use_container_width=True, hide_index=True)

elif aba == "Entrada/Cadastro":
    st.subheader("Cadastrar ou Adicionar Item")
    with st.form("form_entrada", clear_on_submit=True):
        codigo = st.text_input("Código do Material").strip().upper()
        nome = st.text_input("Nome do Material").strip().upper()
        cat = st.selectbox("Categoria", CATEGORIAS)
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        btn = st.form_submit_button("Confirmar Entrada")
        
        if btn and codigo and nome:
            df = st.session_state.estoque
            if codigo in df['Código'].values:
                df.loc[df['Código'] == codigo, 'Qtd'] += qtd
            else:
                novo_item = pd.DataFrame({"Código": [codigo], "Material": [nome], "Qtd": [qtd], "Categoria": [cat]})
                df = pd.concat([df, novo_item], ignore_index=True)
            
            st.session_state.estoque = df
            salvar_dados(df, DB_FILE)
            st.success(f"Item {nome} atualizado!")
            st.rerun()

elif aba == "Saída":
    st.subheader("Registrar Saída de Material")
    df = st.session_state.estoque
    if df.empty:
        st.warning("Não há materiais cadastrados.")
    else:
        lista_itens = df.apply(lambda x: f"{x['Código']} - {x['Material']}", axis=1).tolist()
        escolha = st.selectbox("Selecione o Item", lista_itens)
        codigo_sel = escolha.split(" - ")[0]
        nome_sel = escolha.split(" - ")[1]
        
        qtd_saida = st.number_input("Quantidade de Saída", min_value=1, step=1)
        if st.button("Confirmar Saída"):
            idx = df[df['Código'] == codigo_sel].index[0]
            qtd_atual = df.at[idx, 'Qtd']
            
            if qtd_saida <= qtd_atual:
                # Atualiza Estoque
                df.at[idx, 'Qtd'] -= qtd_saida
                st.session_state.estoque = df
                salvar_dados(df, DB_FILE)
                
                # Ajuste de Horário para Brasil (UTC-3)
                data_br = datetime.now() - timedelta(hours=3)
                data_f = data_br.strftime("%d/%m/%Y %H:%M:%S")
                
                # Salva no Histórico
                novo_h = pd.DataFrame({
                    "Data": [data_f],
                    "Código": [codigo_sel],
                    "Material": [nome_sel],
                    "Qtd": [qtd_saida]
                })
                hist_df = pd.concat([st.session_state.historico, novo_h], ignore_index=True)
                st.session_state.historico = hist_df
                salvar_dados(hist_df, HIST_FILE)
                
                st.success(f"Saída de {qtd_saida} unidades registrada!")
                st.rerun()
            else:
                st.error(f"Saldo insuficiente! Stock atual: {qtd_atual}")

elif aba == "Histórico de Saídas":
    st.subheader("Relatório de Movimentação (Saídas)")
    if st.session_state.historico.empty:
        st.info("Nenhuma saída registrada.")
    else:
        st.dataframe(st.session_state.historico.iloc[::-1], use_container_width=True, hide_index=True)
        if st.button("Limpar Histórico"):
            if os.path.exists(HIST_FILE):
                os.remove(HIST_FILE)
            st.session_state.historico = pd.DataFrame(columns=["Data", "Código", "Material", "Qtd"])
            st.rerun()

elif aba == "Gerenciar Estoque":
    st.subheader("Editar ou Excluir Materiais")
    df = st.session_state.estoque
    if df.empty:
        st.info("Nada para gerenciar.")
    else:
        item_sel = st.selectbox("Escolha um item para Modificar", df['Código'] + " - " + df['Material'])
        cod_gerar = item_sel.split(" - ")[0]
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ APAGAR ITEM COMPLETAMENTE"):
                df = df[df['Código'] != cod_gerar]
                st.session_state.estoque = df
                salvar_dados(df, DB_FILE)
                st.warning("Item removido.")
                st.rerun()
        
        with col2:
            st.write("Editar Informações:")
            n_nome = st.text_input("Novo Nome").strip().upper()
            n_cat = st.selectbox("Nova Categoria", CATEGORIAS)
            if st.button("💾 SALVAR ALTERAÇÕES"):
                if n_nome:
                    df.loc[df['Código'] == cod_gerar, 'Material'] = n_nome
                    df.loc[df['Código'] == cod_gerar, 'Categoria'] = n_cat
                    st.session_state.estoque = df
                    salvar_dados(df, DB_FILE)
                    st.success("Dados alterados!")
                    st.rerun()

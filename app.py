import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Arquivos de banco de dados
DB_FILE = "estoque_dados.csv"
HIST_FILE = "historico_saidas.csv"

# Funções de Dados
def carregar_dados():
    colunas = ["Código", "Material", "Qtd", "Categoria"]
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype={'Código': str})
            return df.dropna(subset=['Código'])
        except:
            return pd.DataFrame(columns=colunas)
    return pd.DataFrame(columns=colunas)

def carregar_historico():
    if os.path.exists(HIST_FILE):
        return pd.read_csv(HIST_FILE)
    return pd.DataFrame(columns=["Data", "Código", "Material", "Qtd"])

def salvar_dados(df, arquivo):
    df.to_csv(arquivo, index=False)

st.set_page_config(page_title="Controle de Estoque", layout="wide")

if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()
if 'historico' not in st.session_state:
    st.session_state.historico = carregar_historico()

st.title("Controle de Estoque v1.0")

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada/Cadastro", "Saída", "Histórico de Saídas", "Gerenciar Estoque"])

if aba == "Visão Geral":
    st.subheader("Itens em Estoque")
    st.dataframe(st.session_state.estoque, use_container_width=True, hide_index=True)

elif aba == "Entrada/Cadastro":
    st.subheader("Cadastrar ou Adicionar Item")
    with st.form("form_entrada", clear_on_submit=True):
        codigo = st.text_input("Código do Material").strip().upper()
        nome = st.text_input("Nome do Material").strip().upper()
        cat = st.selectbox("Categoria", ["EPI'S", "FERRAMENTAS", "ESCRITÓRIO", "OUTROS"])
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        if st.form_submit_button("Confirmar Entrada"):
            if codigo and nome:
                df = st.session_state.estoque
                if codigo in df['Código'].values:
                    df.loc[df['Código'] == codigo, 'Qtd'] += qtd
                else:
                    novo = pd.DataFrame({"Código": [codigo], "Material": [nome], "Qtd": [qtd], "Categoria": [cat]})
                    df = pd.concat([df, novo], ignore_index=True)
                st.session_state.estoque = df
                salvar_dados(df, DB_FILE)
                st.success("Estoque atualizado!")
                st.rerun()

elif aba == "Saída":
    st.subheader("Registrar Saída")
    df = st.session_state.estoque
    if df.empty:
        st.warning("Estoque vazio.")
    else:
        lista = df.apply(lambda x: f"{x['Código']} - {x['Material']}", axis=1).tolist()
        escolha = st.selectbox("Selecione o Item", lista)
        cod_sel = escolha.split(" - ")[0]
        nome_sel = escolha.split(" - ")[1]
        qtd_s = st.number_input("Quantidade de Saída", min_value=1, step=1)
        
        if st.button("Confirmar Saída"):
            idx = df[df['Código'] == cod_sel].index[0]
            if qtd_s <= df.at[idx, 'Qtd']:
                # Atualiza Estoque
                df.at[idx, 'Qtd'] -= qtd_s
                salvar_dados(df, DB_FILE)
                
                # Registra no Histórico
                novo_h = pd.DataFrame({
                    "Data": [datetime.now().strftime("%d/%m/%Y %H:%M:%S")],
                    "Código": [cod_sel],
                    "Material": [nome_sel],
                    "Qtd": [qtd_s]
                })
                hist_df = pd.concat([st.session_state.historico, novo_h], ignore_index=True)
                st.session_state.historico = hist_df
                salvar_dados(hist_df, HIST_FILE)
                
                st.success("Saída registrada no histórico!")
                st.rerun()
            else:
                st.error("Saldo insuficiente.")

elif aba == "Histórico de Saídas":
    st.subheader("Relatório de Movimentação (Saídas)")
    if st.session_state.historico.empty:
        st.info("Nenhuma saída registrada ainda.")
    else:
        # Mostra o histórico do mais recente para o mais antigo
        st.dataframe(st.session_state.historico.iloc[::-1], use_container_width=True, hide_index=True)
        if st.button("Limpar Histórico"):
            if os.path.exists(HIST_FILE):
                os.remove(HIST_FILE)
            st.session_state.historico = pd.DataFrame(columns=["Data", "Código", "Material", "Qtd"])
            st.rerun()

elif aba == "Gerenciar Estoque":
    # (Mantém o código anterior de apagar/editar)
    st.subheader("Editar ou Excluir Materiais")
    df = st.session_state.estoque
    if not df.empty:
        item = st.selectbox("Escolha um item", df['Código'] + " - " + df['Material'])
        cod = item.split(" - ")[0]
        if st.button("🗑️ APAGAR ITEM"):
            df = df[df['Código'] != cod]
            st.session_state.estoque = df
            salvar_dados(df, DB_FILE)
            st.rerun()
    

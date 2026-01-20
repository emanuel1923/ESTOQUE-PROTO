import streamlit as st
import pandas as pd
import os

# Nome do arquivo de banco de dados
DB_FILE = "estoque_dados.csv"

# Função para carregar dados
def carregar_dados():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Material", "Qtd", "Categoria"])

# Função para salvar dados
def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

st.set_page_config(page_title="Controle de Estoque", layout="centered")

# Inicializa o estado do app
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()

st.title("📦 Controle de Estoque v1.0")

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada/Cadastro", "Saída"])

if aba == "Visão Geral":
    st.subheader("Itens em Estoque")
    if st.session_state.estoque.empty:
        st.info("O estoque está vazio.")
    else:
        st.dataframe(st.session_state.estoque, use_container_width=True)

elif aba == "Entrada/Cadastro":
    st.subheader("Cadastrar ou Adicionar Item")
    with st.form("form_entrada"):
        nome = st.text_input("Nome do Material").strip().upper()
        cat = st.selectbox("Categoria", ["Elétrico", "Mecânico", "Escritório", "Outros"])
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        btn = st.form_submit_button("Confirmar Entrada")
        
        if btn and nome:
            df = st.session_state.estoque
            if nome in df['Material'].values:
                df.loc[df['Material'] == nome, 'Qtd'] += qtd
            else:
                novo_item = pd.DataFrame({"Material": [nome], "Qtd": [qtd], "Categoria": [cat]})
                df = pd.concat([df, novo_item], ignore_index=True)
            
            st.session_state.estoque = df
            salvar_dados(df)
            st.success(f"Estoque de {nome} atualizado!")

elif aba == "Saída":
    st.subheader("Registrar Saída de Material")
    if st.session_state.estoque.empty:
        st.warning("Não há materiais para dar saída.")
    else:
        with st.form("form_saida"):
            material = st.selectbox("Selecione o Item", st.session_state.estoque['Material'])
            qtd_saida = st.number_input("Quantidade de Saída", min_value=1, step=1)
            btn_saida = st.form_submit_button("Registrar Saída")
            
            if btn_saida:
                df = st.session_state.estoque
                qtd_atual = df.loc[df['Material'] == material, 'Qtd'].values[0]
                
                if qtd_saida <= qtd_atual:
                    df.loc[df['Material'] == material, 'Qtd'] -= qtd_saida
                    st.session_state.estoque = df
                    salvar_dados(df)
                    st.warning(f"Saída de {qtd_saida} unidades de {material} registrada.")
                else:
                    st.error(f"Saldo insuficiente! Você só tem {qtd_atual} unidades.")

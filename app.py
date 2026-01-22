import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Suassuna Fernandes - Inventário", layout="wide")

# LINK DIRETO (Substitua apenas o ID se o seu for diferente)
# O ID é essa parte entre o /d/ e o /edit no seu link
ID_PLANILHA = "1jSO0S0qvRerM8mdgZlfldHHjEyYQKETlCy__m7BdluY"
URL_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet=estoque"

def carregar_dados():
    try:
        # Força o pandas a ler o CSV direto do Google sem cache chato
        return pd.read_csv(URL_ESTOQUE, on_bad_lines='skip')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame(columns=["Código", "Material", "Qtd", "Mínimo", "Categoria"])

# --- INTERFACE ---
st.markdown("<h1 style='text-align: center;'>Suassuna Fernandes</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Controle de Inventário Profissional</p>", unsafe_allow_html=True)
st.divider()

aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada/Cadastro", "Saída"])

if aba == "Visão Geral":
    st.subheader("Estado Atual do Inventário")
    df = carregar_dados()
    if df.empty:
        st.warning("Aguardando dados da planilha...")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    if st.button("Atualizar Dados"):
        st.rerun()

elif aba == "Entrada/Cadastro":
    st.subheader("Entrada de Materiais")
    st.info("Para este protótipo, use a planilha para cadastrar e o site para visualizar.")
    st.markdown(f"[Abrir Planilha do Google](https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/edit)")

# --- REQUISITOS ---
# No seu requirements.txt, deixe apenas:
# streamlit
# pandas

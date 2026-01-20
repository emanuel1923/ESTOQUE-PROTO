import streamlit as st
import pandas as pd
import os

# Nome do arquivo de banco de dados
DB_FILE = "estoque_dados.csv"

# Função para carregar dados com correção de colunas
def carregar_dados():
    colunas_corretas = ["Código", "Material", "Qtd", "Categoria"]
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype={'Código': str})
            # Verifica se todas as colunas necessárias existem
            if not all(col in df.columns for col in colunas_corretas):
                return pd.DataFrame(columns=colunas_corretas)
            return df.dropna(subset=['Código'])
        except:
            return pd.DataFrame(columns=colunas_corretas)
    return pd.DataFrame(columns=colunas_corretas)

# Função para salvar dados
def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

st.set_page_config(page_title="Controle de Estoque", layout="centered")

# Inicializa o estado do app
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()

st.title("Controle de Estoque v1.0")

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada/Cadastro", "Saída", "Gerenciar Estoque"])

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
        cat = st.selectbox("Categoria", ["EPI'S", "FERRAMENTAS", "CONSUMÍVEIS", "ESCRITÓRIO", "OUTROS"])
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
            salvar_dados(df)
            st.success(f"Item atualizado!")
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
        
        qtd_saida = st.number_input("Quantidade de Saída", min_value=1, step=1)
        if st.button("Confirmar Saída"):
            qtd_atual = df.loc[df['Código'] == codigo_sel, 'Qtd'].values[0]
            if qtd_saida <= qtd_atual:
                df.loc[df['Código'] == codigo_sel, 'Qtd'] -= qtd_saida
                st.session_state.estoque = df
                salvar_dados(df)
                st.success("Saída registrada!")
                st.rerun()
            else:
                st.error(f"Saldo insuficiente! Estoque atual: {qtd_atual}")

elif aba == "Gerenciar Estoque":
    st.subheader("Editar ou Excluir Materiais")
    df = st.session_state.estoque
    if df.empty:
        st.info("Nada para gerenciar.")
    else:
        item_para_gerenciar = st.selectbox("Escolha um item para Modificar", df['Código'] + " - " + df['Material'])
        cod_gerenciar = item_para_gerenciar.split(" - ")[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ APAGAR ITEM"):
                df = df[df['Código'] != cod_gerenciar]
                st.session_state.estoque = df
                salvar_dados(df)
                st.warning("Item removido do sistema.")
                st.rerun()
        
        with col2:
            st.write("Para editar, preencha abaixo:")
            novo_nome = st.text_input("Novo Nome").strip().upper()
            nova_cat = st.selectbox("Nova Categoria", ["EPI'S", "FERRAMENTAS", "CONSUMÍVEIS", "ESCRITÓRIO", "OUTROS"], key="edit_cat")
            if st.button("💾 SALVAR EDIÇÃO"):
                if novo_nome:
                    df.loc[df['Código'] == cod_gerenciar, 'Material'] = novo_nome
                    df.loc[df['Código'] == cod_gerenciar, 'Categoria'] = nova_cat
                    st.session_state.estoque = df
                    salvar_dados(df)
                    st.success("Dados alterados!")
                    st.rerun()
                else:
                    st.error("Digite um nome para editar.")

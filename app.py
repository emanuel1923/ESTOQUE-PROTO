import streamlit as st
import pandas as pd
import os

# Nome do arquivo de banco de dados
DB_FILE = "estoque_dados.csv"

# Função para carregar dados
def carregar_dados():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={'Código': str})
    return pd.DataFrame(columns=["Código", "Material", "Qtd", "Categoria"])

# Função para salvar dados
def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

st.set_page_config(page_title="Controle de Estoque", layout="centered")

# Inicializa o estado do app
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()

st.title("Controle de Estoque v1.0")

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada/Cadastro", "Saída"])

if aba == "Visão Geral":
    st.subheader("Itens em Estoque")
    if st.session_state.estoque.empty:
        st.info("O estoque está vazio.")
    else:
        st.dataframe(st.session_state.estoque, use_container_width=True, hide_index=True)

elif aba == "Entrada/Cadastro":
    st.subheader("Cadastrar ou Adicionar Item")
    with st.form("form_entrada"):
        # Agora você escolhe o número do código que quiser
        codigo = st.text_input("Código do Material (Ex: 001, A10)").strip().upper()
        nome = st.text_input("Nome do Material").strip().upper()
        
        # Categoria com EPI'S inclusa
        cat = st.selectbox("Categoria", [
            "EPI'S", 
            "FERRAMENTAS", 
            "CONSUMÍVEIS", 
            "ESCRITÓRIO", 
            "OUTROS"
        ])
        
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        btn = st.form_submit_button("Confirmar Entrada")
        
        if btn and codigo and nome:
            df = st.session_state.estoque
            
            # Verifica se o código já existe para somar a quantidade, senão cria novo
            if codigo in df['Código'].values:
                df.loc[df['Código'] == codigo, 'Qtd'] += qtd
                # Atualiza o nome e categoria caso tenham mudado
                df.loc[df['Código'] == codigo, 'Material'] = nome
                df.loc[df['Código'] == codigo, 'Categoria'] = cat
            else:
                novo_item = pd.DataFrame({"Código": [codigo], "Material": [nome], "Qtd": [qtd], "Categoria": [cat]})
                df = pd.concat([df, novo_item], ignore_index=True)
            
            st.session_state.estoque = df
            salvar_dados(df)
            st.success(f"Item {nome} (Cód: {codigo}) atualizado com sucesso!")
        elif btn:
            st.error("Por favor, preencha o Código e o Nome.")

elif aba == "Saída":
    st.subheader("Registrar Saída de Material")
    if st.session_state.estoque.empty:
        st.warning("Não há materiais para dar saída.")
    else:
        with st.form("form_saida"):
            # Seleção baseada no Código e Nome para facilitar
            opcoes = st.session_state.estoque.apply(lambda x: f"{x['Código']} - {x['Material']}", axis=1)
            escolha = st.selectbox("Selecione o Item (Código - Nome)", opcoes)
            
            codigo_selecionado = escolha.split(" - ")[0]
            qtd_saida = st.number_input("Quantidade de Saída", min_value=1, step=1)
            btn_saida = st.form_submit_button("Registrar Saída")
            
            if btn_saida:
                df = st.session_state.estoque
                qtd_atual = df.loc[df['Código'] == codigo_selecionado, 'Qtd'].values[0]
                
                if qtd_saida <= qtd_atual:
                    df.loc[df['Código'] == codigo_selecionado, 'Qtd'] -= qtd_saida
                    st.session_state.estoque = df
                    salvar_dados(df)
                    st.warning(f"Saída de {qtd_saida} unidades do código {codigo_selecionado} registrada.")
                else:
                    st.error(f"Saldo insuficiente! Estoque atual: {qtd_atual}")

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Arquivos de banco de dados
DB_FILE = "estoque_dados.csv"
HIST_SAIDA_FILE = "historico_saidas.csv"
HIST_ENTRADA_FILE = "historico_entradas.csv"

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

def carregar_hist(arquivo, colunas):
    if os.path.exists(arquivo):
        try:
            return pd.read_csv(arquivo, dtype={'Código': str})
        except:
            return pd.DataFrame(columns=colunas)
    return pd.DataFrame(columns=colunas)

def salvar_dados(df, arquivo):
    df.to_csv(arquivo, index=False)

st.set_page_config(page_title="Controle de Estoque", layout="wide")

# Inicialização dos estados
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()
if 'hist_saida' not in st.session_state:
    st.session_state.hist_saida = carregar_hist(HIST_SAIDA_FILE, ["Data", "Código", "Material", "Qtd"])
if 'hist_entrada' not in st.session_state:
    st.session_state.hist_entrada = carregar_hist(HIST_ENTRADA_FILE, ["Data", "Código", "Material", "Qtd", "Tipo"])

st.title("Controle de Estoque")

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada/Cadastro", "Saída", "Histórico de Entradas", "Histórico de Saídas", "Gerenciar Estoque"])

CATEGORIAS = ["EPI'S", "FERRAMENTAS", "ESCRITÓRIO", "OUTROS"]

if aba == "Visão Geral":
    st.subheader("Itens em Estoque")
    if st.session_state.estoque.empty:
        st.info("O estoque está vazio.")
    else:
        st.dataframe(st.session_state.estoque, use_container_width=True, hide_index=True)

elif aba == "Entrada/Cadastro":
    st.subheader("Cadastrar ou Adicionar Item")
    
    # Campo de Código fora do Form para permitir a busca automática
    codigo_input = st.text_input("Digite o Código do Material").strip().upper()
    
    nome_padrao = ""
    cat_index = 0
    item_existente = False

    # Busca automática se o código já existir
    if codigo_input:
        df_atual = st.session_state.estoque
        if codigo_input in df_atual['Código'].values:
            dados_item = df_atual[df_atual['Código'] == codigo_input].iloc[0]
            nome_padrao = dados_item['Material']
            cat_index = CATEGORIAS.index(dados_item['Categoria']) if dados_item['Categoria'] in CATEGORIAS else 0
            item_existente = True
            st.info(f"Produto encontrado: {nome_padrao}")

    with st.form("form_entrada", clear_on_submit=True):
        nome = st.text_input("Nome do Material", value=nome_padrao).strip().upper()
        cat = st.selectbox("Categoria", CATEGORIAS, index=cat_index)
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        btn = st.form_submit_button("Confirmar Entrada")
        
        if btn and codigo_input and nome:
            df = st.session_state.estoque
            tipo_entrada = "Novo Cadastro"
            
            if item_existente:
                df.loc[df['Código'] == codigo_input, 'Qtd'] += qtd
                tipo_entrada = "Reposição"
                msg = f"Quantidade de '{nome}' atualizada!"
            else:
                novo_item = pd.DataFrame({"Código": [codigo_input], "Material": [nome], "Qtd": [qtd], "Categoria": [cat]})
                df = pd.concat([df, novo_item], ignore_index=True)
                msg = f"Produto '{nome}' cadastrado!"
            
            st.session_state.estoque = df
            salvar_dados(df, DB_FILE)
            
            # Histórico
            data_br = datetime.now() - timedelta(hours=3)
            data_f = data_br.strftime("%d/%m/%Y %H:%M:%S")
            novo_hist_e = pd.DataFrame({
                "Data": [data_f], "Código": [codigo_input], "Material": [nome], "Qtd": [qtd], "Tipo": [tipo_entrada]
            })
            st.session_state.hist_entrada = pd.concat([st.session_state.hist_entrada, novo_hist_e], ignore_index=True)
            salvar_dados(st.session_state.hist_entrada, HIST_ENTRADA_FILE)
            
            st.success(msg)
            st.toast(msg, icon='✅')

elif aba == "Saída":
    st.subheader("Registrar Saída de Material")
    df = st.session_state.estoque
    if df.empty:
        st.warning("Não há materiais cadastrados.")
    else:
        # Busca por Código ou Seleção
        lista_itens = df.apply(lambda x: f"{x['Código']} - {x['Material']}", axis=1).tolist()
        escolha = st.selectbox("Selecione o Item (Código - Nome)", lista_itens)
        codigo_sel = escolha.split(" - ")[0]
        nome_sel = escolha.split(" - ")[1]
        
        qtd_saida = st.number_input("Quantidade de Saída", min_value=1, step=1)
        if st.button("Confirmar Saída"):
            idx = df[df['Código'] == codigo_sel].index[0]
            if qtd_saida <= df.at[idx, 'Qtd']:
                df.at[idx, 'Qtd'] -= qtd_saida
                salvar_dados(df, DB_FILE)
                
                data_br = datetime.now() - timedelta(hours=3)
                data_f = data_br.strftime("%d/%m/%Y %H:%M:%S")
                
                novo_h_s = pd.DataFrame({
                    "Data": [data_f], "Código": [codigo_sel], "Material": [nome_sel], "Qtd": [qtd_saida]
                })
                st.session_state.hist_saida = pd.concat([st.session_state.hist_saida, novo_h_s], ignore_index=True)
                salvar_dados(st.session_state.hist_saida, HIST_SAIDA_FILE)
                
                msg_s = f"Saída de {qtd_saida} unidade(s) de '{nome_sel}' registrada!"
                st.success(msg_s)
                st.toast(msg_s, icon='📤')
                st.rerun()
            else:
                st.error(f"Saldo insuficiente! Estoque atual: {df.at[idx, 'Qtd']}")

elif aba == "Histórico de Entradas":
    st.subheader("Relatório de Entradas e Cadastros")
    if st.session_state.hist_entrada.empty:
        st.info("Nenhuma entrada registrada.")
    else:
        st.dataframe(st.session_state.hist_entrada.iloc[::-1], use_container_width=True, hide_index=True)
        if st.button("Limpar Histórico de Entradas"):
            if os.path.exists(HIST_ENTRADA_FILE): os.remove(HIST_ENTRADA_FILE)
            st.session_state.hist_entrada = pd.DataFrame(columns=["Data", "Código", "Material", "Qtd", "Tipo"])
            st.rerun()

elif aba == "Histórico de Saídas":
    st.subheader("Relatório de Saídas")
    if st.session_state.hist_saida.empty:
        st.info("Nenhuma saída registrada.")
    else:
        st.dataframe(st.session_state.hist_saida.iloc[::-1], use_container_width=True, hide_index=True)
        if st.button("Limpar Histórico de Saídas"):
            if os.path.exists(HIST_SAIDA_FILE): os.remove(HIST_SAIDA_FILE)
            st.session_state.hist_saida = pd.DataFrame(columns=["Data", "Código", "Material", "Qtd"])
            st.rerun()

elif aba == "Gerenciar Estoque":
    st.subheader("Editar ou Excluir Materiais")
    df = st.session_state.estoque
    if not df.empty:
        item_sel = st.selectbox("Escolha um item", df['Código'] + " - " + df['Material'])
        cod_gerar = item_sel.split(" - ")[0]
        if st.button("🗑️ APAGAR ITEM COMPLETAMENTE"):
            df = df[df['Código'] != cod_gerar]
            st.session_state.estoque = df
            salvar_dados(df, DB_FILE)
            st.rerun()

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

# --- VISÃO GERAL ---
if aba == "Visão Geral":
    st.subheader("Itens em Estoque")
    if st.session_state.estoque.empty:
        st.info("O estoque está vazio.")
    else:
        st.dataframe(st.session_state.estoque, use_container_width=True, hide_index=True)

# --- ENTRADA (COM AVISOS) ---
elif aba == "Entrada/Cadastro":
    st.subheader("Cadastrar ou Repor Item")
    cod_in = st.text_input("Bipe ou Digite o Código (Entrada)").strip().upper()
    
    nome_p = ""
    cat_i = 0
    existe = False

    if cod_in:
        df_at = st.session_state.estoque
        if cod_in in df_at['Código'].values:
            item = df_at[df_at['Código'] == cod_in].iloc[0]
            nome_p = item['Material']
            cat_i = CATEGORIAS.index(item['Categoria']) if item['Categoria'] in CATEGORIAS else 0
            existe = True
            st.info(f"Produto Identificado: {nome_p}")

    with st.form("form_e", clear_on_submit=True):
        nome = st.text_input("Descrição do Material", value=nome_p).strip().upper()
        cat = st.selectbox("Categoria", CATEGORIAS, index=cat_i)
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        btn_e = st.form_submit_button("Confirmar Entrada")
        
        if btn_e:
            if cod_in and nome:
                df = st.session_state.estoque
                tipo = "Reposição" if existe else "Novo Cadastro"
                if existe:
                    df.loc[df['Código'] == cod_in, 'Qtd'] += qtd
                else:
                    novo = pd.DataFrame({"Código": [cod_in], "Material": [nome], "Qtd": [qtd], "Categoria": [cat]})
                    df = pd.concat([df, novo], ignore_index=True)
                
                st.session_state.estoque = df
                salvar_dados(df, DB_FILE)
                
                # Histórico
                dt = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                n_h = pd.DataFrame({"Data": [dt], "Código": [cod_in], "Material": [nome], "Qtd": [qtd], "Tipo": [tipo]})
                st.session_state.hist_entrada = pd.concat([st.session_state.hist_entrada, n_h], ignore_index=True)
                salvar_dados(st.session_state.hist_entrada, HIST_ENTRADA_FILE)
                
                msg = f"Sucesso: {tipo} de '{nome}' realizado!"
                st.success(msg)
                st.toast(msg, icon='✅')
            else:
                st.error("Preencha o código e a descrição.")

# --- SAÍDA (COM AVISOS) ---
elif aba == "Saída":
    st.subheader("Registrar Saída (Bipe o Código)")
    cod_out = st.text_input("Bipe ou Digite o Código (Saída)").strip().upper()
    
    if cod_out:
        df = st.session_state.estoque
        if cod_out in df['Código'].values:
            item_s = df[df['Código'] == cod_out].iloc[0]
            st.warning(f"Produto: {item_s['Material']} | Estoque Atual: {item_s['Qtd']}")
            
            qtd_s = st.number_input("Quantidade para Saída", min_value=1, max_value=int(item_s['Qtd']) if item_s['Qtd'] > 0 else 1, step=1)
            
            if st.button("Confirmar Saída"):
                if item_s['Qtd'] >= qtd_s:
                    idx = df[df['Código'] == cod_out].index[0]
                    df.at[idx, 'Qtd'] -= qtd_s
                    st.session_state.estoque = df
                    salvar_dados(df, DB_FILE)
                    
                    # Histórico
                    dt_s = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                    n_h_s = pd.DataFrame({"Data": [dt_s], "Código": [cod_out], "Material": [item_s['Material']], "Qtd": [qtd_s]})
                    st.session_state.hist_saida = pd.concat([st.session_state.hist_saida, n_h_s], ignore_index=True)
                    salvar_dados(st.session_state.hist_saida, HIST_SAIDA_FILE)
                    
                    msg_saida = f"Saída de {qtd_s} unidades de '{item_s['Material']}' confirmada!"
                    st.success(msg_saida)
                    st.toast(msg_saida, icon='📤')
                else:
                    st.error("Estoque insuficiente para esta saída.")
        else:
            st.error("Código não encontrado.")

# --- HISTÓRICOS (COM AVISOS DE LIMPEZA) ---
elif aba == "Histórico de Entradas":
    st.subheader("Relatório de Entradas")
    if not st.session_state.hist_entrada.empty:
        st.dataframe(st.session_state.hist_entrada.iloc[::-1], use_container_width=True, hide_index=True)
        if st.button("Limpar Histórico de Entradas"):
            if os.path.exists(HIST_ENTRADA_FILE): os.remove(HIST_ENTRADA_FILE)
            st.session_state.hist_entrada = pd.DataFrame(columns=["Data", "Código", "Material", "Qtd", "Tipo"])
            st.success("Histórico de entradas excluído!")
            st.rerun()
    else:
        st.info("Sem registros de entrada.")

elif aba == "Histórico de Saídas":
    st.subheader("Relatório de Saídas")
    if not st.session_state.hist_saida.empty:
        st.dataframe(st.session_state.hist_saida.iloc[::-1], use_container_width=True, hide_index=True)
        if st.button("Limpar Histórico de Saídas"):
            if os.path.exists(HIST_SAIDA_FILE): os.remove(HIST_SAIDA_FILE)
            st.session_state.hist_saida = pd.DataFrame(columns=["Data", "Código", "Material", "Qtd"])
            st.success("Histórico de saídas excluído!")
            st.rerun()
    else:
        st.info("Sem registros de saída.")

# --- GERENCIAR (COM AVISOS) ---
elif aba == "Gerenciar Estoque":
    st.subheader("Gerenciamento de Itens")
    df_g = st.session_state.estoque
    if not df_g.empty:
        sel = st.selectbox("Selecione o Item para remover", df_g['Código'] + " - " + df_g['Material'])
        c_g = sel.split(" - ")[0]
        n_g = sel.split(" - ")[1]
        
        if st.button("🗑️ APAGAR PRODUTO DO SISTEMA"):
            df_novo = df_g[df_g['Código'] != c_g]
            st.session_state.estoque = df_novo
            salvar_dados(df_novo, DB_FILE)
            st.warning(f"O item '{n_g}' foi removido permanentemente.")
            st.toast("Item removido", icon='⚠️')
            st.rerun()
    else:
        st.info("Nada para gerenciar.")

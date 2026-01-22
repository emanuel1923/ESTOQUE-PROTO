import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# Configuração da Página
st.set_page_config(page_title="Gestão de Inventário - Suassuna Fernandes", layout="wide")

# URL DA SUA PLANILHA (COLE AQUI)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1jSO0S0qvRerM8mdgZlfldHHjEyYQKEtlCy__m7BdIuY/edit?usp=sharing"

# Estabelece conexão com o banco de dados na nuvem
conn = st.connection("gsheets", type=GSheetsConnection)

# Funções de Leitura
def carregar_estoque():
    return conn.read(spreadsheet=URL_PLANILHA, worksheet="estoque", ttl=0)

def carregar_entradas():
    return conn.read(spreadsheet=URL_PLANILHA, worksheet="hist_entrada", ttl=0)

def carregar_saidas():
    return conn.read(spreadsheet=URL_PLANILHA, worksheet="hist_saida", ttl=0)

# --- CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.markdown("### SUASSUNA\n### FERNANDES")

with col_titulo:
    st.title("Sistema de Controle de Inventário")
    st.write("Controle de Suprimentos e Logística - Dados em Nuvem")

st.divider()

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação Principal", ["Visão Geral", "Entrada e Cadastro", "Saída de Material", "Históricos", "Gerenciar Itens"])

CATEGORIAS = ["EPI'S", "FERRAMENTAS", "ESCRITÓRIO", "OUTROS"]

# --- VISÃO GERAL ---
if aba == "Visão Geral":
    df_v = carregar_estoque()
    st.subheader("Estado Atual do Inventário")
    if df_v.empty:
        st.info("Nenhum item cadastrado no sistema.")
    else:
        def destacar_critico(row):
            color = 'red' if row['Qtd'] <= row['Mínimo'] else 'white'
            return [f'color: {color}'] * len(row)
        
        st.write("Itens em vermelho atingiram o limite mínimo de segurança.")
        st.dataframe(df_v.style.apply(destacar_critico, axis=1), use_container_width=True, hide_index=True)
        
        csv = df_v.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar Inventário Atual (CSV)", csv, "estoque_sf.csv", "text/csv")

# --- ENTRADA E CADASTRO ---
elif aba == "Entrada e Cadastro":
    st.subheader("Registro de Entrada")
    df_estoque = carregar_estoque()
    cod_in = st.text_input("Bipe ou Digite o Código").strip().upper()
    
    nome_p, cat_i, min_p, existe = "", 0, 5, False
    if cod_in and not df_estoque.empty:
        if cod_in in df_estoque['Código'].astype(str).values:
            item = df_estoque[df_estoque['Código'].astype(str) == cod_in].iloc[0]
            nome_p, existe = item['Material'], True
            min_p = int(item['Mínimo'])
            cat_i = CATEGORIAS.index(item['Categoria']) if item['Categoria'] in CATEGORIAS else 0
            st.info(f"Material Identificado: {nome_p}")

    with st.form("form_entrada", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Descrição", value=nome_p).upper()
        cat = col2.selectbox("Categoria", CATEGORIAS, index=cat_i)
        
        col3, col4 = st.columns(2)
        qtd = col3.number_input("Quantidade", min_value=1)
        minimo = col4.number_input("Estoque Mínimo", value=min_p)
        
        if st.form_submit_button("Salvar Registro"):
            if cod_in and nome:
                tipo = "Reposição" if existe else "Novo Cadastro"
                if existe:
                    df_estoque.loc[df_estoque['Código'].astype(str) == cod_in, 'Qtd'] += qtd
                    df_estoque.loc[df_estoque['Código'].astype(str) == cod_in, 'Mínimo'] = minimo
                else:
                    novo = pd.DataFrame([{"Código": cod_in, "Material": nome, "Qtd": qtd, "Mínimo": minimo, "Categoria": cat}])
                    df_estoque = pd.concat([df_estoque, novo], ignore_index=True)
                
                # Salvar Estoque e Histórico na Planilha
                conn.update(spreadsheet=URL_PLANILHA, worksheet="estoque", data=df_estoque)
                
                dt = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                df_h_e = carregar_entradas()
                novo_h_e = pd.DataFrame([{"Data": dt, "Código": cod_in, "Material": nome, "Qtd": qtd, "Tipo": tipo}])
                df_h_e = pd.concat([df_h_e, novo_h_e], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, worksheet="hist_entrada", data=df_h_e)
                
                st.success(f"{tipo} de '{nome}' concluído com sucesso.")
                st.rerun()

# --- SAÍDA DE MATERIAL ---
elif aba == "Saída de Material":
    st.subheader("Registro de Saída")
    df_estoque = carregar_estoque()
    cod_out = st.text_input("Bipe o Código para Saída").strip().upper()
    
    if cod_out and cod_out in df_estoque['Código'].astype(str).values:
        idx = df_estoque[df_estoque['Código'].astype(str) == cod_out].index[0]
        item = df_estoque.iloc[idx]
        st.warning(f"Material: {item['Material']} | Saldo: {item['Qtd']}")
        
        with st.form("form_saida"):
            destino = st.text_input("Setor ou Responsável").upper()
            qtd_s = st.number_input("Quantidade", min_value=1, max_value=int(item['Qtd']))
            
            if st.form_submit_button("Confirmar Saída"):
                if destino:
                    df_estoque.at[idx, 'Qtd'] -= qtd_s
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="estoque", data=df_estoque)
                    
                    dt_s = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                    df_h_s = carregar_saidas()
                    n_h_s = pd.DataFrame([{"Data": dt_s, "Código": cod_out, "Material": item['Material'], "Qtd": qtd_s, "Destino_Responsavel": destino}])
                    df_h_s = pd.concat([df_h_s, n_h_s], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="hist_saida", data=df_h_s)
                    
                    st.success(f"Saída registrada para {destino}")
                    st.rerun()

# --- HISTÓRICOS ---
elif aba == "Históricos":
    st.subheader("Relatórios de Movimentação")
    t1, t2 = st.tabs(["Entradas", "Saídas"])
    with t1:
        st.dataframe(carregar_entradas().iloc[::-1], use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(carregar_saidas().iloc[::-1], use_container_width=True, hide_index=True)

# --- GERENCIAR ITENS ---
elif aba == "Gerenciar Itens":
    st.subheader("Edição Técnica de Cadastro")
    df_g = carregar_estoque()
    if not df_g.empty:
        sel = st.selectbox("Selecione o Item", df_g['Código'].astype(str) + " - " + df_g['Material'])
        cod_ref = sel.split(" - ")[0]
        dados = df_g[df_g['Código'].astype(str) == cod_ref].iloc[0]
        
        with st.form("edicao_gestao"):
            c1, c2 = st.columns(2); n_cod = c1.text_input("Novo Código", value=dados['Código']); n_nom = c2.text_input("Nova Descrição", value=dados['Material'])
            c3, c4 = st.columns(2); n_cat = c3.selectbox("Categoria", CATEGORIAS, index=CATEGORIAS.index(dados['Categoria'])); n_min = c4.number_input("Estoque Mínimo", value=int(dados['Mínimo']))
            
            b1, b2 = st.columns(2)
            if b1.form_submit_button("Salvar Alterações"):
                idx = df_g[df_g['Código'].astype(str) == cod_ref].index[0]
                df_g.at[idx, 'Código'], df_g.at[idx, 'Material'] = n_cod, n_nom
                df_g.at[idx, 'Categoria'], df_g.at[idx, 'Mínimo'] = n_cat, n_min
                conn.update(spreadsheet=URL_PLANILHA, worksheet="estoque", data=df_g)
                st.success("Dados Atualizados!")
                st.rerun()
            if b2.form_submit_button("Excluir Item Permanentemente"):
                df_g = df_g[df_g['Código'].astype(str) != cod_ref]
                conn.update(spreadsheet=URL_PLANILHA, worksheet="estoque", data=df_g)
                st.warning("Item Removido.")
                st.rerun()

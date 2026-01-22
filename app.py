import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# Configuração da Página
st.set_page_config(page_title="Suassuna Fernandes - Inventário", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
# Use o link da barra de endereços que termina em /edit
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1jSO0S0qvRerM8mdgZlfldHHjEyYQKETlCy__m7BdluY/edit"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_aba(nome_aba, colunas_esperadas):
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=nome_aba, ttl=0)
        if df.empty:
            return pd.DataFrame(columns=colunas_esperadas)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a aba '{nome_aba}': Verifique se o nome da aba e das colunas estão corretos.")
        return pd.DataFrame(columns=colunas_esperadas)

# --- CABEÇALHO ---
st.markdown("<h1 style='text-align: center;'>Suassuna Fernandes</h1>", unsafe_allow_html=True)
st.divider()

# --- MENU ---
aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada e Cadastro", "Saída de Material", "Históricos"])

CATEGORIAS = ["EPI'S", "FERRAMENTAS", "ESCRITÓRIO", "OUTROS"]

# --- LÓGICA DAS ABAS ---

if aba == "Visão Geral":
    df_v = carregar_aba("estoque", ["Código", "Material", "Qtd", "Mínimo", "Categoria"])
    st.subheader("Estado Atual do Inventário")
    if not df_v.empty:
        def destacar_critico(row):
            color = 'red' if row['Qtd'] <= row['Mínimo'] else 'white'
            return [f'color: {color}'] * len(row)
        st.dataframe(df_v.style.apply(destacar_critico, axis=1), use_container_width=True, hide_index=True)

elif aba == "Entrada e Cadastro":
    st.subheader("Entrada de Materiais")
    df_estoque = carregar_aba("estoque", ["Código", "Material", "Qtd", "Mínimo", "Categoria"])
    
    cod_in = st.text_input("Bipe o Código").strip().upper()
    
    nome_p, min_p, existe = "", 5, False
    if cod_in and not df_estoque.empty:
        # Garante que o código seja tratado como string para comparação
        df_estoque['Código'] = df_estoque['Código'].astype(str)
        if cod_in in df_estoque['Código'].values:
            item = df_estoque[df_estoque['Código'] == cod_in].iloc[0]
            nome_p, min_p, existe = item['Material'], int(item['Mínimo']), True
            st.info(f"Item Identificado: {nome_p}")

    with st.form("form_entrada", clear_on_submit=True):
        nome = st.text_input("Descrição", value=nome_p).upper()
        col1, col2 = st.columns(2)
        qtd = col1.number_input("Quantidade", min_value=1)
        mini = col2.number_input("Mínimo", value=min_p)
        cat = st.selectbox("Categoria", CATEGORIAS)
        
        if st.form_submit_button("Salvar Registro"):
            if cod_in and nome:
                if existe:
                    df_estoque.loc[df_estoque['Código'] == cod_in, 'Qtd'] += qtd
                else:
                    novo = pd.DataFrame([{"Código":cod_in, "Material":nome, "Qtd":qtd, "Mínimo":mini, "Categoria":cat}])
                    df_estoque = pd.concat([df_estoque, novo], ignore_index=True)
                
                conn.update(spreadsheet=URL_PLANILHA, worksheet="estoque", data=df_estoque)
                
                # Registro no Histórico de Entrada
                df_h_e = carregar_aba("hist_entrada", ["Data", "Código", "Material", "Qtd", "Tipo"])
                dt = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                nova_ent = pd.DataFrame([{"Data":dt, "Código":cod_in, "Material":nome, "Qtd":qtd, "Tipo":"Entrada"}])
                df_h_e = pd.concat([df_h_e, nova_ent], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, worksheet="hist_entrada", data=df_h_e)
                
                st.success("Dados salvos na nuvem!")
                st.rerun()

elif aba == "Saída de Material":
    st.subheader("Saída de Material")
    df_s = carregar_aba("estoque", ["Código", "Material", "Qtd", "Mínimo", "Categoria"])
    cod_out = st.text_input("Código para Saída").strip().upper()
    
    if cod_out and cod_out in df_s['Código'].astype(str).values:
        idx = df_s[df_s['Código'].astype(str) == cod_out].index[0]
        item = df_s.iloc[idx]
        st.warning(f"Saindo: {item['Material']} | Saldo: {item['Qtd']}")
        
        with st.form("form_saida"):
            resp = st.text_input("Setor ou Responsável").upper()
            qtd_s = st.number_input("Quantidade", min_value=1, max_value=int(item['Qtd']))
            if st.form_submit_button("Confirmar Saída"):
                if resp:
                    df_s.at[idx, 'Qtd'] -= qtd_s
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="estoque", data=df_s)
                    
                    df_h_s = carregar_aba("hist_saida", ["Data", "Código", "Material", "Qtd", "Destino_Responsavel"])
                    dt_s = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                    nova_sai = pd.DataFrame([{"Data":dt_s, "Código":cod_out, "Material":item['Material'], "Qtd":qtd_s, "Destino_Responsavel":resp}])
                    df_h_s = pd.concat([df_h_s, nova_sai], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="hist_saida", data=df_h_s)
                    
                    st.success("Saída registrada!")
                    st.rerun()

elif aba == "Históricos":
    st.subheader("Relatórios")
    tab1, tab2 = st.tabs(["Entradas", "Saídas"])
    with tab1:
        st.dataframe(carregar_aba("hist_entrada", []), use_container_width=True)
    with tab2:
        st.dataframe(carregar_aba("hist_saida", []), use_container_width=True)
                

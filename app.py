import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Configurações de Banco de Dados
DB_FILE = "estoque_dados.csv"
HIST_SAIDA_FILE = "historico_saidas.csv"
HIST_ENTRADA_FILE = "historico_entradas.csv"

def carregar_dados():
    colunas = ["Código", "Material", "Qtd", "Mínimo", "Categoria"]
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype={'Código': str})
            for col in colunas:
                if col not in df.columns: df[col] = 0 if col in ["Qtd", "Mínimo"] else "N/A"
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

# Configuração da Página
st.set_page_config(page_title="Suassuna Fernandes - Estoque", layout="wide")

# --- CABEÇALHO PERSONALIZADO ---
# Usando colunas para organizar a Logo e o Título
col_logo, col_titulo = st.columns([1, 3])

with col_logo:
    # Verifica variações comuns de nome de arquivo
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    elif os.path.exists("logo.PNG"):
        st.image("logo.PNG", width=180)
    else:
        # Se não achar a imagem, mostra o nome da empresa em destaque
        st.markdown("### SUASSUNA\n### FERNANDES")

with col_titulo:
    st.markdown("<h1 style='margin-bottom: 0;'>Sistema de Controle de Inventário</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.2em; color: gray;'>Gestão de Suprimentos e Logística Interna</p>", unsafe_allow_html=True)

st.divider()

# Inicialização de Estados
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()
if 'hist_saida' not in st.session_state:
    st.session_state.hist_saida = carregar_hist(HIST_SAIDA_FILE, ["Data", "Código", "Material", "Qtd", "Destino_Responsavel"])
if 'hist_entrada' not in st.session_state:
    st.session_state.hist_entrada = carregar_hist(HIST_ENTRADA_FILE, ["Data", "Código", "Material", "Qtd", "Tipo"])

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação Principal", ["Visão Geral", "Entrada e Cadastro", "Saída de Material", "Histórico de Movimentação", "Gerenciar Itens"])

CATEGORIAS = ["EPI'S", "FERRAMENTAS", "ESCRITÓRIO", "OUTROS"]

# --- VISÃO GERAL ---
if aba == "Visão Geral":
    st.subheader("Estado Atual do Inventário")
    df_v = st.session_state.estoque.copy()
    
    if df_v.empty:
        st.info("O inventário está vazio.")
    else:
        def destacar_estoque_critico(row):
            color = 'red' if row['Qtd'] <= row['Mínimo'] else 'white'
            return [f'color: {color}'] * len(row)
        
        st.write("Itens em vermelho indicam necessidade de reposição (estoque abaixo do mínimo).")
        st.dataframe(df_v.style.apply(destacar_estoque_critico, axis=1), use_container_width=True, hide_index=True)
        
        csv = df_v.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar Dados para Excel (CSV)", csv, "inventario_suassuna.csv", "text/csv")

# --- ENTRADA E CADASTRO ---
elif aba == "Entrada e Cadastro":
    st.subheader("Registro de Entrada de Material")
    cod_in = st.text_input("Bipe o Código do Produto").strip().upper()
    
    nome_p, cat_i, min_p, existe = "", 0, 5, False
    if cod_in:
        df_at = st.session_state.estoque
        if cod_in in df_at['Código'].values:
            item = df_at[df_at['Código'] == cod_in].iloc[0]
            nome_p, existe = item['Material'], True
            min_p = int(item['Mínimo'])
            cat_i = CATEGORIAS.index(item['Categoria']) if item['Categoria'] in CATEGORIAS else 0
            st.info(f"Material Identificado: {nome_p}")

    with st.form("form_registro_entrada", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Descrição", value=nome_p).strip().upper()
        cat = col2.selectbox("Categoria", CATEGORIAS, index=cat_i)
        
        col3, col4 = st.columns(2)
        qtd = col3.number_input("Quantidade a Adicionar", min_value=1, step=1)
        minimo = col4.number_input("Definir Estoque Mínimo", min_value=0, value=min_p, step=1)
        
        if st.form_submit_button("Confirmar Entrada"):
            if cod_in and nome:
                df = st.session_state.estoque
                tipo = "Reposição" if existe else "Novo Cadastro"
                if existe:
                    df.loc[df['Código'] == cod_in, 'Qtd'] += qtd
                    df.loc[df['Código'] == cod_in, 'Mínimo'] = minimo
                else:
                    novo = pd.DataFrame({"Código": [cod_in], "Material": [nome], "Qtd": [qtd], "Mínimo": [minimo], "Categoria": [cat]})
                    df = pd.concat([df, novo], ignore_index=True)
                
                st.session_state.estoque = df
                salvar_dados(df, DB_FILE)
                
                dt = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                n_h = pd.DataFrame({"Data": [dt], "Código": [cod_in], "Material": [nome], "Qtd": [qtd], "Tipo": [tipo]})
                st.session_state.hist_entrada = pd.concat([st.session_state.hist_entrada, n_h], ignore_index=True)
                salvar_dados(st.session_state.hist_entrada, HIST_ENTRADA_FILE)
                
                st.success(f"Operação concluída: {nome}")
                st.rerun()

# --- SAÍDA DE MATERIAL ---
elif aba == "Saída de Material":
    st.subheader("Registro de Saída / Requisição")
    cod_out = st.text_input("Bipe o Código do Produto").strip().upper()
    
    if cod_out:
        df = st.session_state.estoque
        if cod_out in df['Código'].values:
            item_s = df[df['Código'] == cod_out].iloc[0]
            st.warning(f"Item: {item_s['Material']} | Saldo em Estoque: {item_s['Qtd']}")
            
            with st.form("form_requisicao"):
                destino = st.text_input("Setor ou Responsável pelo Recebimento").strip().upper()
                qtd_s = st.number_input("Quantidade a Retirar", min_value=1, max_value=int(item_s['Qtd']) if item_s['Qtd'] > 0 else 1, step=1)
                
                if st.form_submit_button("Validar Saída"):
                    if destino:
                        idx = df[df['Código'] == cod_out].index[0]
                        df.at[idx, 'Qtd'] -= qtd_s
                        salvar_dados(df, DB_FILE)
                        dt_s = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                        n_h_s = pd.DataFrame({"Data": [dt_s], "Código": [cod_out], "Material": [item_s['Material']], "Qtd": [qtd_s], "Destino_Responsavel": [destino]})
                        st.session_state.hist_saida = pd.concat([st.session_state.hist_saida, n_h_s], ignore_index=True)
                        salvar_dados(st.session_state.hist_saida, HIST_SAIDA_FILE)
                        st.success(f"Saída para {destino} registrada com sucesso.")
                        st.rerun()
                    else:
                        st.error("Informe o destino ou responsável.")
        else:
            st.error("Material não localizado no inventário.")

# --- HISTÓRICO ---
elif aba == "Histórico de Movimentação":
    st.subheader("Relatórios de Auditoria")
    tab1, tab2 = st.tabs(["Fluxo de Entradas", "Fluxo de Saídas"])
    with tab1:
        st.dataframe(st.session_state.hist_entrada.iloc[::-1], use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(st.session_state.hist_saida.iloc[::-1], use_container_width=True, hide_index=True)

# --- GERENCIAR ---
elif aba == "Gerenciar Itens":
    st.subheader("Modificação de Cadastro")
    df_g = st.session_state.estoque
    if not df_g.empty:
        item_sel = st.selectbox("Selecione o Item", df_g['Código'] + " - " + df_g['Material'])
        cod_ref = item_sel.split(" - ")[0]
        dados = df_g[df_g['Código'] == cod_ref].iloc[0]
        
        with st.form("form_edicao_gestao"):
            c1, c2 = st.columns(2)
            n_cod = c1.text_input("Código", value=dados['Código']).strip().upper()
            n_nom = c2.text_input("Descrição", value=dados['Material']).strip().upper()
            c3, c4 = st.columns(2)
            n_cat = c3.selectbox("Categoria", CATEGORIAS, index=CATEGORIAS.index(dados['Categoria']))
            n_min = c4.number_input("Estoque Mínimo", value=int(dados['Mínimo']))
            
            col_b1, col_b2 = st.columns(2)
            if col_b1.form_submit_button("Salvar Alterações"):
                idx = df_g[df_g['Código'] == cod_ref].index[0]
                df_g.at[idx, 'Código'], df_g.at[idx, 'Material'] = n_cod, n_nom
                df_g.at[idx, 'Categoria'], df_g.at[idx, 'Mínimo'] = n_cat, n_min
                salvar_dados(df_g, DB_FILE)
                st.success("Dados atualizados.")
                st.rerun()
            
            if col_b2.form_submit_button("Excluir Material"):
                df_novo = df_g[df_g['Código'] != cod_ref]
                salvar_dados(df_novo, DB_FILE)
                st.session_state.estoque = df_novo
                st.warning("Material removido do sistema.")
                st.rerun()

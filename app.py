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

st.set_page_config(page_title="Sistema de Controle de Inventário", layout="wide")

# Inicialização de Estados
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()
if 'hist_saida' not in st.session_state:
    st.session_state.hist_saida = carregar_hist(HIST_SAIDA_FILE, ["Data", "Código", "Material", "Qtd", "Destino_Responsavel"])
if 'hist_entrada' not in st.session_state:
    st.session_state.hist_entrada = carregar_hist(HIST_ENTRADA_FILE, ["Data", "Código", "Material", "Qtd", "Tipo"])

st.title("Sistema de Controle de Inventário")

aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada e Cadastro", "Saída de Material", "Histórico de Movimentação", "Gerenciar Itens"])

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
        
        st.write("Itens destacados em vermelho atingiram o limite mínimo de segurança.")
        st.dataframe(df_v.style.apply(destacar_estoque_critico, axis=1), use_container_width=True, hide_index=True)
        
        csv = df_v.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar Inventário Atual (CSV)", csv, "inventario_atual.csv", "text/csv")

# --- ENTRADA E CADASTRO ---
elif aba == "Entrada e Cadastro":
    st.subheader("Registro de Entrada")
    cod_in = st.text_input("Código do Material (Leitura de Scanner ou Digitação)").strip().upper()
    
    nome_p, cat_i, min_p, existe = "", 0, 5, False
    if cod_in:
        df_at = st.session_state.estoque
        if cod_in in df_at['Código'].values:
            item = df_at[df_at['Código'] == cod_in].iloc[0]
            nome_p, existe = item['Material'], True
            min_p = int(item['Mínimo'])
            cat_i = CATEGORIAS.index(item['Categoria']) if item['Categoria'] in CATEGORIAS else 0
            st.info(f"Material Identificado: {nome_p}")

    with st.form("form_entrada_material", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Descrição do Material", value=nome_p).strip().upper()
        cat = col2.selectbox("Categoria", CATEGORIAS, index=cat_i)
        
        col3, col4 = st.columns(2)
        qtd = col3.number_input("Quantidade a Adicionar", min_value=1, step=1)
        minimo = col4.number_input("Ponto de Pedido (Estoque Mínimo)", min_value=0, value=min_p, step=1)
        
        if st.form_submit_button("Confirmar Registro"):
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
                
                # Registro de Histórico
                dt = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                n_h = pd.DataFrame({"Data": [dt], "Código": [cod_in], "Material": [nome], "Qtd": [qtd], "Tipo": [tipo]})
                st.session_state.hist_entrada = pd.concat([st.session_state.hist_entrada, n_h], ignore_index=True)
                salvar_dados(st.session_state.hist_entrada, HIST_ENTRADA_FILE)
                
                st.success(f"Registro de {tipo} efetuado com sucesso.")
            else:
                st.error("Campos obrigatórios ausentes.")

# --- SAÍDA DE MATERIAL ---
elif aba == "Saída de Material":
    st.subheader("Registro de Saída")
    cod_out = st.text_input("Código do Material para Saída").strip().upper()
    
    if cod_out:
        df = st.session_state.estoque
        if cod_out in df['Código'].values:
            item_s = df[df['Código'] == cod_out].iloc[0]
            st.warning(f"Material: {item_s['Material']} | Saldo Disponível: {item_s['Qtd']}")
            
            with st.form("form_saida_material"):
                # Campo para entrada manual de Setor ou Responsável
                destino = st.text_input("Setor ou Responsável pelo Recebimento").strip().upper()
                qtd_s = st.number_input("Quantidade", min_value=1, max_value=int(item_s['Qtd']) if item_s['Qtd'] > 0 else 1, step=1)
                
                if st.form_submit_button("Confirmar Saída"):
                    if destino:
                        idx = df[df['Código'] == cod_out].index[0]
                        df.at[idx, 'Qtd'] -= qtd_s
                        st.session_state.estoque = df
                        salvar_dados(df, DB_FILE)
                        
                        dt_s = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                        n_h_s = pd.DataFrame({"Data": [dt_s], "Código": [cod_out], "Material": [item_s['Material']], "Qtd": [qtd_s], "Destino_Responsavel": [destino]})
                        st.session_state.hist_saida = pd.concat([st.session_state.hist_saida, n_h_s], ignore_index=True)
                        salvar_dados(st.session_state.hist_saida, HIST_SAIDA_FILE)
                        
                        st.success(f"Saída para {destino} registrada no sistema.")
                        st.rerun()
                    else:
                        st.error("Informe o setor ou o responsável.")
        else:
            st.error("Código não localizado.")

# --- HISTÓRICO DE MOVIMENTAÇÃO ---
elif aba == "Histórico de Movimentação":
    st.subheader("Relatórios de Movimentação")
    
    col_e, col_s = st.tabs(["Entradas", "Saídas"])
    
    with col_e:
        if not st.session_state.hist_entrada.empty:
            st.dataframe(st.session_state.hist_entrada.iloc[::-1], use_container_width=True, hide_index=True)
            st.download_button("Exportar Entradas (CSV)", st.session_state.hist_entrada.to_csv(index=False).encode('utf-8'), "historico_entradas.csv")
        else: st.info("Sem registros de entrada.")
        
    with col_s:
        if not st.session_state.hist_saida.empty:
            st.dataframe(st.session_state.hist_saida.iloc[::-1], use_container_width=True, hide_index=True)
            st.download_button("Exportar Saídas (CSV)", st.session_state.hist_saida.to_csv(index=False).encode('utf-8'), "historico_saidas.csv")
        else: st.info("Sem registros de saída.")

# --- GERENCIAR ITENS ---
elif aba == "Gerenciar Itens":
    st.subheader("Edição e Exclusão de Materiais")
    df_g = st.session_state.estoque
    
    if not df_g.empty:
        item_sel = st.selectbox("Selecione o Item para Gestão", df_g['Código'] + " - " + df_g['Material'])
        cod_ref = item_sel.split(" - ")[0]
        dados_atuais = df_g[df_g['Código'] == cod_ref].iloc[0]
        
        st.divider()
        st.write(f"Editando dados de: {dados_atuais['Material']}")
        
        with st.form("form_edicao"):
            col_ed1, col_ed2 = st.columns(2)
            novo_cod = col_ed1.text_input("Código do Material", value=dados_atuais['Código']).strip().upper()
            novo_nome = col_ed2.text_input("Descrição do Material", value=dados_atuais['Material']).strip().upper()
            
            col_ed3, col_ed4 = st.columns(2)
            nova_cat = col_ed3.selectbox("Categoria", CATEGORIAS, index=CATEGORIAS.index(dados_atuais['Categoria']))
            novo_min = col_ed4.number_input("Estoque Mínimo", value=int(dados_atuais['Mínimo']), step=1)
            
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.form_submit_button("Salvar Alterações"):
                idx = df_g[df_g['Código'] == cod_ref].index[0]
                df_g.at[idx, 'Código'] = novo_cod
                df_g.at[idx, 'Material'] = novo_nome
                df_g.at[idx, 'Categoria'] = nova_cat
                df_g.at[idx, 'Mínimo'] = novo_min
                st.session_state.estoque = df_g
                salvar_dados(df_g, DB_FILE)
                st.success("Alterações salvas com sucesso.")
                st.rerun()
                
            if col_btn2.form_submit_button("Excluir Item"):
                df_novo = df_g[df_g['Código'] != cod_ref]
                st.session_state.estoque = df_novo
                salvar_dados(df_novo, DB_FILE)
                st.warning("Item removido permanentemente.")
                st.rerun()
    else:
        st.info("Não há itens para gerenciar.")

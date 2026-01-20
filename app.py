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
    colunas = ["Código", "Material", "Qtd", "Mínimo", "Categoria"]
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype={'Código': str})
            # Garantir que a coluna Mínimo existe em arquivos antigos
            if "Mínimo" not in df.columns:
                df["Mínimo"] = 5
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

st.set_page_config(page_title="Controle de Estoque - Suassuna Fernandes", layout="wide")

if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_dados()
if 'hist_saida' not in st.session_state:
    st.session_state.hist_saida = carregar_hist(HIST_SAIDA_FILE, ["Data", "Código", "Material", "Qtd", "Responsável"])
if 'hist_entrada' not in st.session_state:
    st.session_state.hist_entrada = carregar_hist(HIST_ENTRADA_FILE, ["Data", "Código", "Material", "Qtd", "Tipo"])

st.title("🏛️ Controle de Estoque")

aba = st.sidebar.radio("Navegação", ["Visão Geral", "Entrada/Cadastro", "Saída", "Histórico de Entradas", "Histórico de Saídas", "Gerenciar Estoque"])

CATEGORIAS = ["EPI'S", "FERRAMENTAS", "ESCRITÓRIO", "OUTROS"]

# --- VISÃO GERAL ---
if aba == "Visão Geral":
    st.subheader("Estado Atual do Inventário")
    df_v = st.session_state.estoque.copy()
    
    if df_v.empty:
        st.info("O estoque está vazio.")
    else:
        # Lógica de cor comparando Qtd com Mínimo
        def destacar_baixo_estoque(row):
            color = 'red' if row['Qtd'] <= row['Mínimo'] else 'black'
            return [f'color: {color}'] * len(row)
        
        st.write("⚠️ *Itens em vermelho atingiram ou estão abaixo do estoque mínimo definido.*")
        st.dataframe(df_v.style.apply(destacar_baixo_estoque, axis=1), use_container_width=True, hide_index=True)
        
        csv = df_v.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Planilha de Estoque", csv, "estoque_atual.csv", "text/csv")

# --- ENTRADA / CADASTRO ---
elif aba == "Entrada/Cadastro":
    st.subheader("Entrada de Materiais")
    cod_in = st.text_input("Bipe o Código (Entrada)").strip().upper()
    
    nome_p, cat_i, min_p, existe = "", 0, 5, False
    if cod_in:
        df_at = st.session_state.estoque
        if cod_in in df_at['Código'].values:
            item = df_at[df_at['Código'] == cod_in].iloc[0]
            nome_p, existe = item['Material'], True
            min_p = int(item['Mínimo'])
            cat_i = CATEGORIAS.index(item['Categoria']) if item['Categoria'] in CATEGORIAS else 0
            st.info(f"Produto Identificado: {nome_p} | Mínimo atual: {min_p}")

    with st.form("form_e", clear_on_submit=True):
        nome = st.text_input("Descrição", value=nome_p).strip().upper()
        cat = st.selectbox("Categoria", CATEGORIAS, index=cat_i)
        col_q1, col_q2 = st.columns(2)
        qtd = col_q1.number_input("Quantidade a Adicionar", min_value=1, step=1)
        minimo = col_q2.number_input("Definir Estoque Mínimo (Alerta)", min_value=0, value=min_p, step=1)
        
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
                
                st.success(f"✅ Sucesso!")
                st.rerun()

# --- SAÍDA ---
elif aba == "Saída":
    st.subheader("Retirada de Material")
    cod_out = st.text_input("Bipe o Código (Saída)").strip().upper()
    
    if cod_out:
        df = st.session_state.estoque
        if cod_out in df['Código'].values:
            item_s = df[df['Código'] == cod_out].iloc[0]
            st.warning(f"📦 {item_s['Material']} | Saldo: {item_s['Qtd']} | Mínimo: {item_s['Mínimo']}")
            
            with st.form("form_s"):
                resp = st.text_input("Responsável pela Retirada").upper()
                qtd_s = st.number_input("Quantidade", min_value=1, max_value=int(item_s['Qtd']) if item_s['Qtd'] > 0 else 1, step=1)
                if st.form_submit_button("Confirmar Saída"):
                    if resp:
                        idx = df[df['Código'] == cod_out].index[0]
                        df.at[idx, 'Qtd'] -= qtd_s
                        salvar_dados(df, DB_FILE)
                        dt_s = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                        n_h_s = pd.DataFrame({"Data": [dt_s], "Código": [cod_out], "Material": [item_s['Material']], "Qtd": [qtd_s], "Responsável": [resp]})
                        st.session_state.hist_saida = pd.concat([st.session_state.hist_saida, n_h_s], ignore_index=True)
                        salvar_dados(st.session_state.hist_saida, HIST_SAIDA_FILE)
                        st.success("Saída registrada!")
                        st.rerun()
                    else: st.error("Informe o responsável.")
        else: st.error("Código não encontrado.")

# --- HISTÓRICOS ---
elif "Histórico" in aba:
    tipo = "Entrada" if "Entrada" in aba else "Saída"
    df_h = st.session_state.hist_entrada if tipo == "Entrada" else st.session_state.hist_saida
    st.subheader(f"Relatório de {tipo}s")
    st.dataframe(df_h.iloc[::-1], use_container_width=True, hide_index=True)
    st.download_button(f"📥 Baixar CSV", df_h.to_csv(index=False).encode('utf-8'), f"relatorio_{tipo.lower()}.csv")

# --- GERENCIAR ---
elif aba == "Gerenciar Estoque":
    st.subheader("Ajustar Itens")
    df_g = st.session_state.estoque
    if not df_g.empty:
        sel = st.selectbox("Escolha o item", df_g['Código'] + " - " + df_g['Material'])
        c_g = sel.split(" - ")[0]
        if st.button("🗑️ REMOVER ITEM"):
            st.session_state.estoque = df_g[df_g['Código'] != c_g]
            salvar_dados(st.session_state.estoque, DB_FILE)
            st.rerun()

"""
SMHB GESTÃO — v9.2 (Edição Especial Corrigida)
Sociedade Missionária de Homens Batistas, GAM e ER
────────────────────────────────────────
Correção Crítica: Navegação Persistente e Menu Blindado
"""

import io
import contextlib
import threading
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import sqlite3

# ─── CONFIGURAÇÃO DE ESTADO E DB ──────────────────────────────────────────────
_db_lock = threading.Lock()
DB_PATH  = Path(__file__).parent / "smhb_master_v7.db"

st.set_page_config(
    page_title="SMHB | GAM | ER - Gestão",
    layout="wide",
    page_icon="⛪",
    initial_sidebar_state="expanded"
)

# ─── ESTILIZAÇÃO E CORREÇÃO DE INTERFACE ─────────────────────────────────────
st.markdown("""
<style>
    /* Forçar a barra lateral a ser visível e legível */
    section[data-testid="stSidebar"] {
        background-color: #1B2B5E !important;
        min-width: 250px !important;
    }
    
    /* Estilizar o menu de rádio para parecer botões de app */
    div[role="radiogroup"] > label {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        padding: 10px 15px !important;
        border-radius: 8px !important;
        color: #B8CDE8 !important;
        margin-bottom: 8px !important;
        transition: 0.3s;
    }
    
    div[role="radiogroup"] > label:hover {
        background: rgba(201,150,61,0.2) !important;
        color: #F5D78E !important;
    }

    div[role="radiogroup"] [data-checked="true"] {
        background: #C9963D !important;
        color: white !important;
        font-weight: bold !important;
    }

    /* Ajuste para não sumir no Mobile */
    .stApp {
        margin-bottom: 50px;
    }
</style>
""", unsafe_allow_html=True)

# ─── DATABASE ENGINE ─────────────────────────────────────────────────────────
@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        conn.rollback()
    finally:
        conn.close()

def init_db():
    with _db_lock:
        with get_db() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS membros (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
                cargo TEXT, telefone TEXT, igreja TEXT, departamento TEXT DEFAULT 'SMHB')""")
            
            conn.execute("""CREATE TABLE IF NOT EXISTS reunioes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL,
                tipo TEXT, horario TEXT, local_igreja TEXT, departamento_alvo TEXT DEFAULT 'Geral')""")
            
            conn.execute("""CREATE TABLE IF NOT EXISTS frequencia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reuniao_id INTEGER NOT NULL REFERENCES reunioes(id) ON DELETE CASCADE,
                membro_id INTEGER NOT NULL REFERENCES membros(id) ON DELETE CASCADE,
                status TEXT NOT NULL)""")
            conn.commit()

init_db()

# ─── BARRA LATERAL (FIXA E PERSISTENTE) ──────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3661/3661334.png", width=80)
    st.title("SMHB GESTÃO")
    st.write("---")
    
    # Usar um selectbox ou radio na sidebar garante que o estado se mantenha 
    # mesmo se a página fizer um "refresh" parcial.
    menu_options = {
        "🏠 Início": "home",
        "➕ Cadastrar Membro": "new",
        "👥 Lista de Membros": "membros",
        "📅 Agendar Evento": "agenda",
        "✅ Realizar Chamada": "attendance",
        "📊 Relatórios": "relatorio"
    }
    
    # Seletor de página principal
    escolha = st.radio(
        "Navegação Principal",
        options=list(menu_options.keys()),
        index=0,
        key="main_nav_radio"
    )
    
    page = menu_options[escolha]
    st.write("---")
    st.caption("v9.2 Gold Edition")

# ─── LÓGICA DE PÁGINAS ───────────────────────────────────────────────────────

if page == "home":
    st.header("Painel de Controlo")
    with get_db() as conn:
        c1, c2, c3 = st.columns(3)
        res = conn.execute("SELECT departamento, count(*) as total FROM membros GROUP BY departamento").fetchall()
        stats = {r['departamento']: r['total'] for r in res}
        
        c1.metric("Homens (SMHB)", stats.get("SMHB", 0))
        c2.metric("Jovens (GAM)", stats.get("GAM", 0))
        c3.metric("Crianças (ER)", stats.get("ER", 0))

elif page == "new":
    st.header("➕ Novo Cadastro")
    with st.form("novo_membro", clear_on_submit=True):
        nome = st.text_input("Nome Completo").upper()
        col1, col2 = st.columns(2)
        dep = col1.selectbox("Departamento", ["SMHB", "GAM", "ER"])
        igreja = col2.selectbox("Igreja", ["IB Cristo Rei", "IB Proclamai"])
        tel = st.text_input("Telemóvel/WhatsApp")
        cargo = st.text_input("Cargo", "Integrante")
        
        if st.form_submit_button("Gravar Membro"):
            if len(nome) > 3:
                with _db_lock, get_db() as conn:
                    conn.execute("INSERT INTO membros (nome, cargo, telefone, igreja, departamento) VALUES (?,?,?,?,?)",
                                 (nome, cargo, tel, igreja, dep))
                    conn.commit()
                st.success(f"Sucesso! {nome} adicionado.")
            else:
                st.error("Nome inválido.")

elif page == "membros":
    st.header("👥 Lista de Membros")
    dep_filt = st.segmented_control("Filtrar por:", ["SMHB", "GAM", "ER"], default="SMHB")
    
    with get_db() as conn:
        membros = conn.execute("SELECT * FROM membros WHERE departamento=? ORDER BY nome ASC", (dep_filt,)).fetchall()
        for m in membros:
            with st.expander(f"{m['nome']} - {m['cargo']}"):
                st.write(f"Igreja: {m['igreja']}")
                st.write(f"Contacto: {m['telefone']}")
                if st.button("Remover", key=f"del_{m['id']}"):
                    with _db_lock, get_db() as conn:
                        conn.execute("DELETE FROM membros WHERE id=?", (m['id'],))
                        conn.commit()
                    st.rerun()

elif page == "agenda":
    st.header("📅 Agenda de Atividades")
    with st.form("nova_reuniao"):
        dt = st.date_input("Data do Evento")
        tipo = st.selectbox("Tipo", ["Culto", "Reunião", "Esporte", "Ação Social"])
        alvo = st.selectbox("Público Alvo", ["Geral", "SMHB", "GAM", "ER"])
        local = st.text_input("Local", "Templo")
        hora = st.text_input("Hora", "19:30")
        
        if st.form_submit_button("Agendar Atividade"):
            with _db_lock, get_db() as conn:
                conn.execute("INSERT INTO reunioes (data, tipo, horario, local_igreja, departamento_alvo) VALUES (?,?,?,?,?)",
                             (str(dt), tipo, hora, local, alvo))
                conn.commit()
            st.success("Evento agendado com sucesso!")

elif page == "attendance":
    st.header("✅ Chamada de Frequência")
    with get_db() as conn:
        reunioes = conn.execute("SELECT * FROM reunioes ORDER BY data DESC LIMIT 10").fetchall()
    
    if not reunioes:
        st.info("Nenhuma reunião agendada.")
    else:
        opcoes = {f"{r['data']} - {r['tipo']} ({r['departamento_alvo']})": r['id'] for r in reunioes}
        selecionada = st.selectbox("Escolha o Evento", list(opcoes.keys()))
        rid = opcoes[selecionada]
        
        # Filtro de membros por departamento da reunião
        dep_alvo = [r['departamento_alvo'] for r in reunioes if r['id'] == rid][0]
        
        with get_db() as conn:
            if dep_alvo == "Geral":
                lista = conn.execute("SELECT * FROM membros ORDER BY nome ASC").fetchall()
            else:
                lista = conn.execute("SELECT * FROM membros WHERE departamento=? ORDER BY nome ASC", (dep_alvo,)).fetchall()
            
            # Carregar frequências já salvas
            saved = {f['membro_id']: f['status'] for f in conn.execute("SELECT * FROM frequencia WHERE reuniao_id=?", (rid,)).fetchall()}

        if not lista:
            st.warning("Sem membros cadastrados para este público.")
        else:
            with st.form("form_chamada"):
                results = {}
                for m in lista:
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{m['nome']}**")
                    results[m['id']] = col2.radio("Status", ["P", "F", "J"], 
                                                 index=["P", "F", "J"].index(saved.get(m['id'], "P")),
                                                 key=f"m_{m['id']}", horizontal=True, label_visibility="collapsed")
                
                if st.form_submit_button("Finalizar Chamada"):
                    with _db_lock, get_db() as conn:
                        conn.execute("DELETE FROM frequencia WHERE reuniao_id=?", (rid,))
                        for mid, status in results.items():
                            conn.execute("INSERT INTO frequencia (reuniao_id, membro_id, status) VALUES (?,?,?)", (rid, mid, status))
                        conn.commit()
                    st.success("Chamada guardada!")

elif page == "relatorio":
    st.header("📊 Relatórios")
    with get_db() as conn:
        df_m = pd.read_sql("SELECT id, nome, departamento, igreja FROM membros", conn)
        df_f = pd.read_sql("SELECT membro_id, status FROM frequencia", conn)
    
    if df_f.empty:
        st.info("Aguardando dados de frequência.")
    else:
        stats = df_f[df_f['status'] == 'P'].groupby('membro_id').size().reset_index(name='Presenças')
        df_final = df_m.merge(stats, left_on='id', right_on='membro_id', how='left').fillna(0)
        st.dataframe(df_final[['nome', 'departamento', 'igreja', 'Presenças']], use_container_width=True)

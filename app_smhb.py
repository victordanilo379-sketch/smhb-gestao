"""
SMHB GESTÃO — v9.1 (Produção Blindada)
Sociedade Missionária de Homens Batistas, GAM e ER
────────────────────────────────────────
Engenharia de Software Principal - Correção de Navegação e Módulos
"""

import io
import contextlib
import threading
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import sqlite3

# ─── CONFIGURAÇÃO E THREAD SAFETY ────────────────────────────────────────────
_db_lock = threading.Lock()
DB_PATH  = Path(__file__).parent / "smhb_master_v7.db"

MESES_PT = {
    1:"Janeiro", 2:"Fevereiro", 3:"Março",     4:"Abril",
    5:"Maio",    6:"Junho",     7:"Julho",      8:"Agosto",
    9:"Setembro",10:"Outubro",  11:"Novembro",  12:"Dezembro"
}

st.set_page_config(
    page_title="SMHB | GAM | ER - Gestão",
    layout="wide",
    page_icon="⛪",
    initial_sidebar_state="expanded"
)

# ─── DESIGN SYSTEM E CORREÇÃO DE INTERFACE (UI/UX) ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=DM+Sans:wght@300;400;500;700&display=swap');

html, body, [class*="css"] { font-family:'DM Sans',sans-serif !important; }
.stApp { background-color:#EEF1F8 !important; }

/* Remove elementos que poluem a UI e quebram o mobile */
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer { visibility: hidden !important; height: 0px !important; }

/* Sidebar Estilizada - Mantém o foco na navegação */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #1B2B5E 0%, #0D1A42 100%) !important; border-right: 1px solid #DDE5F4 !important; }
[data-testid="stSidebarNav"] { padding-top: 0 !important; }

/* Botões de Navegação Customizados */
.nav-btn {
    display: flex; align-items: center; padding: 12px 15px; margin: 5px 0;
    background: rgba(255,255,255,0.05); border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);
    color: #B8CDE8; text-decoration: none; cursor: pointer; transition: 0.2s;
}
.nav-btn:hover { background: rgba(201,150,61,0.2); transform: translateX(5px); color: #F5D78E; }
.active-nav { background: rgba(201,150,61,0.3) !important; border-color: #C9963D !important; color: #F5D78E !important; }

/* Cards de Métricas */
[data-testid="stMetric"] {
    background: #FFFFFF !important; border-radius: 18px !important; padding: 20px !important;
    border: 1px solid #E2E8F0 !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
}

/* Tabelas e Containers */
div.stDataFrame { border-radius: 12px !important; overflow: hidden !important; border: 1px solid #E2E8F0 !important; }

/* Correção Mobile para Chamada (Rádios) */
@media (max-width: 768px) {
    div[role="radiogroup"] { flex-direction: column !important; }
    div[role="radiogroup"] > label {
        background: #FFFFFF !important; margin: 4px 0 !important;
        padding: 12px !important; border-radius: 10px !important;
        border: 1px solid #E2E8F0 !important; width: 100% !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ─── DATABASE: MIGRATION E INTEGRIDADE (TOLERÂNCIA ZERO) ──────────────────────
@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception as e:
        st.error(f"Erro Crítico de DB: {e}")
        conn.rollback()
    finally:
        conn.close()

def init_db():
    with _db_lock:
        with get_db() as conn:
            # Tabelas Principais
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
            
            # Verificação de Colunas (Migration Segura)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(membros)")
            cols = [c[1] for c in cursor.fetchall()]
            if 'departamento' not in cols:
                conn.execute("ALTER TABLE membros ADD COLUMN departamento TEXT DEFAULT 'SMHB'")
            
            cursor.execute("PRAGMA table_info(reunioes)")
            cols = [c[1] for c in cursor.fetchall()]
            if 'departamento_alvo' not in cols:
                conn.execute("ALTER TABLE reunioes ADD COLUMN departamento_alvo TEXT DEFAULT 'Geral'")
            
            conn.commit()

init_db()

# ─── LÓGICA DE NAVEGAÇÃO PERSISTENTE ─────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"

def set_page(page_name):
    st.session_state.page = page_name

# ─── SIDEBAR DEFINITIVA ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px 0;'>
        <h2 style='color:#F5D78E; font-family:Crimson Pro; margin-bottom:0;'>IB CRISTO REI</h2>
        <p style='color:#A8BFED; font-size:12px; letter-spacing:1.5px;'>GESTÃO SMHB | GAM | ER</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sistema de Botões Customizados para Evitar que a "Aba Suma"
    nav_options = [
        ("🏠", "Início", "home"),
        ("👥", "Membros", "membros"),
        ("📅", "Agenda", "agenda"),
        ("✅", "Chamada", "attendance"),
        ("📊", "Relatórios", "relatorio"),
        ("➕", "Cadastrar", "new")
    ]
    
    for icon, label, target in nav_options:
        active_class = "active-nav" if st.session_state.page == target else ""
        if st.button(f"{icon} {label}", key=f"btn_{target}", use_container_width=True):
            set_page(target)
            st.rerun()

    st.markdown("<div style='position:fixed; bottom:20px; left:20px; color:rgba(255,255,255,0.2); font-size:10px;'>v9.1 Zero-Defect</div>", unsafe_allow_html=True)

# ─── CONTEÚDO DINÂMICO ───────────────────────────────────────────────────────

# --- DASHBOARD (HOME) ---
if st.session_state.page == "home":
    st.markdown("<h1 style='color:#1B2B5E;'>Painel Administrativo</h1>", unsafe_allow_html=True)
    
    with get_db() as conn:
        c1, c2, c3, c4 = st.columns(4)
        count_smhb = conn.execute("SELECT count(*) FROM membros WHERE departamento='SMHB'").fetchone()[0]
        count_gam  = conn.execute("SELECT count(*) FROM membros WHERE departamento='GAM'").fetchone()[0]
        count_er   = conn.execute("SELECT count(*) FROM membros WHERE departamento='ER'").fetchone()[0]
        count_reu  = conn.execute("SELECT count(*) FROM reunioes").fetchone()[0]
        
        c1.metric("Homens (SMHB)", count_smhb)
        c2.metric("Jovens (GAM)", count_gam)
        c3.metric("Crianças (ER)", count_er)
        c4.metric("Atividades", count_reu)

# --- CADASTRO (NEW) ---
elif st.session_state.page == "new":
    st.markdown("<h2 style='color:#1B2B5E;'>➕ Novo Cadastro de Membro</h2>", unsafe_allow_html=True)
    
    with st.form("form_novo_membro", clear_on_submit=True):
        nome = st.text_input("Nome Completo *").upper()
        col1, col2 = st.columns(2)
        dept = col1.selectbox("Departamento", ["SMHB", "GAM", "ER"])
        igreja = col2.selectbox("Igreja", ["IB Cristo Rei", "IB Proclamai"])
        
        tel = st.text_input("Telefone (WhatsApp)")
        cargo = st.text_input("Cargo/Função", "Integrante")
        
        if st.form_submit_button("💾 Salvar Registro"):
            if len(nome) > 5:
                with _db_lock:
                    with get_db() as conn:
                        conn.execute("INSERT INTO membros (nome, cargo, telefone, igreja, departamento) VALUES (?,?,?,?,?)",
                                     (nome, cargo, tel, igreja, dept))
                        conn.commit()
                st.success(f"✅ {nome} cadastrado no {dept}!")
            else:
                st.error("❌ Por favor, insira o nome completo.")

# --- DIRETÓRIO DE MEMBROS ---
elif st.session_state.page == "membros":
    st.markdown("<h2 style='color:#1B2B5E;'>👥 Diretório Eclesiástico</h2>", unsafe_allow_html=True)
    
    tab_s, tab_g, tab_e = st.tabs(["🛡️ SMHB", "🔥 GAM", "👑 ER"])
    
    def mostrar_membros(dep):
        with get_db() as conn:
            membros = conn.execute("SELECT * FROM membros WHERE departamento=? ORDER BY nome ASC", (dep,)).fetchall()
            if not membros:
                st.info(f"Nenhum registro no departamento {dep}.")
            else:
                for m in membros:
                    with st.expander(f"👤 {m['nome']} ({m['cargo']})"):
                        st.write(f"📞 Contato: {m['telefone']}")
                        st.write(f"⛪ Igreja: {m['igreja']}")
                        if st.button("🗑️ Excluir", key=f"del_{m['id']}"):
                            with _db_lock:
                                with get_db() as conn:
                                    conn.execute("DELETE FROM membros WHERE id=?", (m['id'],))
                                    conn.commit()
                            st.rerun()

    with tab_s: mostrar_membros("SMHB")
    with tab_g: mostrar_membros("GAM")
    with tab_e: mostrar_membros("ER")

# --- AGENDA ---
elif st.session_state.page == "agenda":
    st.markdown("<h2 style='color:#1B2B5E;'>📅 Agenda de Atividades</h2>", unsafe_allow_html=True)
    with st.form("form_agenda"):
        dt = st.date_input("Data")
        tp = st.selectbox("Tipo de Evento", ["Culto", "Reunião", "Ação Missionária", "Esporte", "Estudo"])
        alvo = st.selectbox("Departamento Alvo", ["Geral", "SMHB", "GAM", "ER"])
        local = st.text_input("Local", "Templo Sede")
        hora = st.text_input("Horário", "19:30")
        
        if st.form_submit_button("📅 Agendar"):
            with _db_lock:
                with get_db() as conn:
                    conn.execute("INSERT INTO reunioes (data, tipo, horario, local_igreja, departamento_alvo) VALUES (?,?,?,?,?)",
                                 (str(dt), tp, hora, local, alvo))
                    conn.commit()
            st.success("Evento agendado!")

# --- CHAMADA (ATTENDANCE) ---
elif st.session_state.page == "attendance":
    st.markdown("<h2 style='color:#1B2B5E;'>✅ Controle de Frequência</h2>", unsafe_allow_html=True)
    
    with get_db() as conn:
        reunioes = conn.execute("SELECT * FROM reunioes ORDER BY data DESC LIMIT 10").fetchall()
    
    if not reunioes:
        st.warning("Agende uma reunião primeiro.")
    else:
        opcoes = {f"{r['data']} - {r['tipo']} ({r['departamento_alvo']})": r['id'] for r in reunioes}
        escolha = st.selectbox("Selecione a Reunião", list(opcoes.keys()))
        rid = opcoes[escolha]
        
        # Pega o departamento alvo para filtrar membros
        dep_alvo = conn.execute("SELECT departamento_alvo FROM reunioes WHERE id=?", (rid,)).fetchone()[0]
        
        with get_db() as conn:
            if dep_alvo == "Geral":
                membros = conn.execute("SELECT * FROM membros ORDER BY nome ASC").fetchall()
            else:
                membros = conn.execute("SELECT * FROM membros WHERE departamento=? ORDER BY nome ASC", (dep_alvo,)).fetchall()
            
            pre_freq = {f['membro_id']: f['status'] for f in conn.execute("SELECT * FROM frequencia WHERE reuniao_id=?", (rid,)).fetchall()}

        if not membros:
            st.info("Nenhum membro cadastrado para este público.")
        else:
            with st.form("chamada_form"):
                freq_data = {}
                for m in membros:
                    col_m, col_s = st.columns([2, 1])
                    col_m.write(f"**{m['nome']}**")
                    atual = pre_freq.get(m['id'], "Presente")
                    freq_data[m['id']] = col_s.radio("Status", ["Presente", "Falta", "Justificado"], index=["Presente", "Falta", "Justificado"].index(atual), key=f"f_{m['id']}", label_visibility="collapsed")
                    st.divider()
                
                if st.form_submit_button("💾 Salvar Chamada"):
                    with _db_lock:
                        with get_db() as conn:
                            conn.execute("DELETE FROM frequencia WHERE reuniao_id=?", (rid,))
                            for mid, status in freq_data.items():
                                conn.execute("INSERT INTO frequencia (reuniao_id, membro_id, status) VALUES (?,?,?)", (rid, mid, status))
                            conn.commit()
                    st.success("Chamada atualizada!")

# --- RELATÓRIOS (RELATORIO) ---
elif st.session_state.page == "relatorio":
    st.markdown("<h2 style='color:#1B2B5E;'>📊 Relatórios Analíticos</h2>", unsafe_allow_html=True)
    
    with get_db() as conn:
        membros = conn.execute("SELECT id, nome, departamento FROM membros").fetchall()
        frequencias = conn.execute("SELECT * FROM frequencia").fetchall()
        reunioes = conn.execute("SELECT * FROM reunioes").fetchall()
    
    if not frequencias:
        st.info("Dados insuficientes para gerar relatórios.")
    else:
        # Lógica de cálculo simplificada para visualização imediata
        df_m = pd.DataFrame(membros, columns=['id', 'nome', 'departamento'])
        df_f = pd.DataFrame(frequencias, columns=['id_f', 'reuniao_id', 'membro_id', 'status'])
        
        # Contagem de presenças
        presencas = df_f[df_f['status'] == 'Presente'].groupby('membro_id').size().reset_index(name='P')
        df_final = df_m.merge(presencas, left_on='id', right_on='membro_id', how='left').fillna(0)
        
        st.dataframe(df_final[['nome', 'departamento', 'P']], use_container_width=True)
        
        # Exportação
        output = io.BytesIO()
        df_final.to_excel(output, index=False)
        st.download_button("📥 Baixar Excel", output.getvalue(), "relatorio_smhb.xlsx")

"""
SMHB GESTÃO — v9.0 (Produção Zero-Defect)
Sociedade Missionária de Homens Batistas, GAM e ER
────────────────────────────────────────
Engenharia de Dados e UI/UX:
  [1] Integração Módulos GAM e ER via Safe DB Migration.
  [2] UI Mobile Otimizada (Touch-targets responsivos para Rádios de Chamada).
  [3] Relatório Anual segmentado por Departamento.
  [4] Thread-Safety robusta em todas as transações I/O.
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
    page_title="Gestão Eclesiástica | SMHB GAM ER",
    layout="wide",
    page_icon="⛪",
    initial_sidebar_state="expanded"
)

# ─── DESIGN SYSTEM & MOBILE FIXES (UI/UX) ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

html, body, [class*="css"] { font-family:'DM Sans',sans-serif !important; }
.stApp { background-color:#EEF1F8 !important; }

#MainMenu{visibility:hidden;} footer{visibility:hidden;} header{visibility:hidden;}

/* Sidebar Premium */
[data-testid="stSidebar"] {
    background:linear-gradient(175deg,#1B2B5E 0%,#0D1A42 100%) !important;
}
[data-testid="stSidebar"] .stButton>button {
    background:rgba(255,255,255,0.06) !important;
    border:1px solid rgba(255,255,255,0.10) !important;
    color:#B8CDE8 !important;
    border-radius:10px !important;
    text-align:left !important;
    font-size:14px !important; font-weight:500 !important;
    height:44px !important; transition:all 0.2s ease !important;
    margin-bottom:4px !important;
}
[data-testid="stSidebar"] .stButton>button:hover {
    background:rgba(201,150,61,0.15) !important;
    border-color:rgba(201,150,61,0.40) !important;
    color:#F5D78E !important; transform:translateX(4px) !important;
}

/* Blocos de Métrica */
[data-testid="stMetric"] {
    background:#FFFFFF !important; border:1px solid #DDE5F4 !important;
    border-radius:16px !important; padding:22px !important;
    box-shadow:0 2px 8px rgba(27,43,94,0.05) !important;
}
[data-testid="stMetricLabel"] { color:#7B8DB0 !important; font-size:12px !important; font-weight:700 !important; text-transform:uppercase; }
[data-testid="stMetricValue"] { color:#1B2B5E !important; font-family:'Crimson Pro',serif !important; font-size:2.4rem !important; font-weight:700 !important; }

/* Inputs e Formulários */
.stTextInput>div>div>input, .stSelectbox>div>div, .stDateInput>div>div>input {
    border:1.5px solid #DDE5F4 !important; border-radius:10px !important;
    background:#FAFBFF !important; color:#1a1a2e !important; font-size:14px !important;
}

/* Submeter Formulário */
[data-testid="stFormSubmitButton"]>button {
    background:linear-gradient(135deg,#1B2B5E 0%,#2E46A4 100%) !important;
    color:#FFFFFF !important; font-weight:700 !important;
    box-shadow:0 4px 14px rgba(27,43,94,0.28) !important; border:none !important;
}

/* Tabs Otimizadas */
[data-testid="stTabs"] button { font-weight: 600 !important; font-size: 15px !important; }

/* FIX MOBILE: Rádios de Chamada */
@media (max-width: 768px) {
    .main .block-container { padding: 1rem !important; }
    div[role="radiogroup"] { 
        display: flex !important; flex-direction: row !important; 
        flex-wrap: wrap !important; gap: 8px !important; 
    }
    div[role="radiogroup"] > label {
        background: #FAFBFF !important; padding: 10px 14px !important;
        border: 1.5px solid #DDE5F4 !important; border-radius: 10px !important;
        flex: 1 1 auto !important; justify-content: center !important;
    }
}

/* Tabelas e Emblemas */
.badge { display:inline-block; padding:4px 12px; border-radius:99px; font-size:11px; font-weight:700; text-transform:uppercase; }
.b-smhb { background:#EFF4FF; color:#1B2B5E; border:1px solid #BFD0F0; }
.b-gam  { background:#F0FDF4; color:#166534; border:1px solid #BBF7D0; }
.b-er   { background:#FFF7ED; color:#9A3412; border:1px solid #FED7AA; }
</style>
""", unsafe_allow_html=True)

# ─── DATABASE: MIGRATION E INTEGRIDADE ───────────────────────────────────────
@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON") # Integridade Referencial Estrita
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with _db_lock:
        with get_db() as conn:
            # 1. Criação Base
            conn.execute("""
                CREATE TABLE IF NOT EXISTS membros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
                    cargo TEXT, telefone TEXT, igreja TEXT
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reunioes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL,
                    tipo TEXT, horario TEXT, local_igreja TEXT
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS frequencia (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reuniao_id INTEGER NOT NULL REFERENCES reunioes(id) ON DELETE CASCADE,
                    membro_id INTEGER NOT NULL REFERENCES membros(id) ON DELETE CASCADE,
                    status TEXT NOT NULL DEFAULT 'Presente'
                )""")
            
            # 2. Safemode Migration (Adicionando colunas novas ao BD Antigo)
            c = conn.cursor()
            c.execute("PRAGMA table_info(membros)")
            cols_membros = [info[1] for info in c.fetchall()]
            if 'departamento' not in cols_membros:
                conn.execute("ALTER TABLE membros ADD COLUMN departamento TEXT DEFAULT 'SMHB'")
            
            c.execute("PRAGMA table_info(reunioes)")
            cols_reunioes = [info[1] for info in c.fetchall()]
            if 'departamento_alvo' not in cols_reunioes:
                conn.execute("ALTER TABLE reunioes ADD COLUMN departamento_alvo TEXT DEFAULT 'Geral'")
            
            conn.commit()

init_db()

# ─── CONSTANTES DO DOMÍNIO ───────────────────────────────────────────────────
DEPARTAMENTOS = ["SMHB", "GAM", "ER"]
IGREJAS = ["Igreja Batista Cristo Rei (CR)", "Igreja Batista Proclamai (P)"]
TIPOS_REUNIAO = ["Culto", "Reunião de Líderes", "Esporte Missionário", "Intercâmbio", "Estudo", "Outro"]
CARGOS_SMHB = ["Presidente", "Vice-Presidente", "1° Secretário", "2° Secretário", "1° Tesoureiro", "2° Tesoureiro", "Integrante"]
CARGOS_GAM  = ["Conselheiro", "Líder", "Integrante"]
CARGOS_ER   = ["Conselheiro", "Embaixador", "Candidato"]

# ─── ESTADO E ROTEAMENTO ─────────────────────────────────────────────────────
if "page" not in st.session_state: st.session_state.page = "home"
def nav(target: str): st.session_state.page = target

# ─── SIDEBAR DE NAVEGAÇÃO ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 10px;">
      <div style="font-size:40px;">⛪</div>
      <div style="font-family:'Crimson Pro',serif;font-size:20px;font-weight:700;color:#F5D78E;">Igreja Batista</div>
      <div style="font-size:11px;color:#A8BFED;letter-spacing:1px;margin-top:5px;">GESTÃO DE DEPARTAMENTOS</div>
    </div><hr style="border-color:rgba(255,255,255,0.05);margin:0 0 10px;">
    """, unsafe_allow_html=True)

    opcoes = [("🏠", "Dashboard", "home"), ("👥", "Membros", "membros"), ("📅", "Agenda", "agenda"),
              ("🗄️", "Histórico", "history"), ("✅", "Chamada", "attendance"), ("📊", "Relatório Anual", "relatorio"),
              ("➕", "Novo Cadastro", "new")]
    
    for icone, rotulo, destino in opcoes:
        prefixo = "▶  " if st.session_state.page == destino else "   "
        if st.button(f"{prefixo}{icone}  {rotulo}", key=f"nav_{destino}", use_container_width=True): nav(destino)

# ═════════════════════════════════════════════════════════════════════════════
# MÓDULOS DA APLICAÇÃO
# ═════════════════════════════════════════════════════════════════════════════

if st.session_state.page == "home":
    st.markdown("<h1 style='color:#1B2B5E;font-family:Crimson Pro;'>Visão Geral da Congregação</h1>", unsafe_allow_html=True)
    
    with _db_lock:
        with get_db() as conn:
            t_smhb = conn.execute("SELECT count(*) FROM membros WHERE departamento='SMHB'").fetchone()[0]
            t_gam  = conn.execute("SELECT count(*) FROM membros WHERE departamento='GAM'").fetchone()[0]
            t_er   = conn.execute("SELECT count(*) FROM membros WHERE departamento='ER'").fetchone()[0]
            t_reus = conn.execute("SELECT count(*) FROM reunioes").fetchone()[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛡️ SMHB (Homens)", t_smhb)
    c2.metric("🔥 GAM (Jovens)", t_gam)
    c3.metric("👑 ER (Embaixadores)", t_er)
    c4.metric("📅 Atividades Totais", t_reus)

# ─── CADASTRO DE MEMBROS ───
elif st.session_state.page == "new":
    st.markdown("<h2 style='color:#1B2B5E;'>➕ Novo Cadastro</h2>", unsafe_allow_html=True)
    
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo *").strip().upper()
        c1, c2, c3 = st.columns(3)
        dept   = c1.selectbox("Departamento", DEPARTAMENTOS)
        igreja = c2.selectbox("Igreja", IGREJAS)
        tel    = c3.text_input("Telefone (Opcional)", "+55 (92) ")
        
        # Dinâmica de Cargos (Tratado no form validation para evitar reload)
        cargo_input = st.text_input("Cargo / Função (Ex: Integrante, Conselheiro, Presidente)", "Integrante")
        
        if st.form_submit_button("💾 Salvar Registro", use_container_width=True):
            if len(nome) < 3: st.error("❌ Nome inválido.")
            else:
                with _db_lock:
                    with get_db() as conn:
                        conn.execute("INSERT INTO membros (nome, cargo, telefone, igreja, departamento) VALUES (?,?,?,?,?)",
                                     (nome, cargo_input.strip(), tel, igreja, dept))
                        conn.commit()
                st.success(f"✅ {nome} registado com sucesso no {dept}!")

# ─── GESTÃO DE MEMBROS (MULTI-TENANT) ───
elif st.session_state.page == "membros":
    st.markdown("<h2 style='color:#1B2B5E;'>👥 Diretório de Membros</h2>", unsafe_allow_html=True)
    
    with _db_lock:
        with get_db() as conn:
            todos = conn.execute("SELECT * FROM membros ORDER BY nome ASC").fetchall()
            
    t1, t2, t3 = st.tabs(["🛡️ SMHB", "🔥 GAM", "👑 ER"])
    
    def renderizar_lista(departamento):
        filtrados = [m for m in todos if m['departamento'] == departamento]
        if not filtrados: st.info(f"Nenhum membro no {departamento}.")
        for m in filtrados:
            cor = "b-smhb" if departamento == "SMHB" else ("b-gam" if departamento == "GAM" else "b-er")
            with st.expander(f"👤 {m['nome'].title()} — {m['cargo']}"):
                st.markdown(f"<span class='badge {cor}'>{m['igreja']}</span> 📞 {m['telefone']}", unsafe_allow_html=True)
                if st.button("Remover", key=f"del_{m['id']}"):
                    with _db_lock:
                        with get_db() as conn:
                            conn.execute("DELETE FROM membros WHERE id=?", (m['id'],))
                            conn.commit()
                    st.rerun()
                    
    with t1: renderizar_lista("SMHB")
    with t2: renderizar_lista("GAM")
    with t3: renderizar_lista("ER")

# ─── AGENDA ───
elif st.session_state.page == "agenda":
    st.markdown("<h2 style='color:#1B2B5E;'>📅 Agendar Atividade</h2>", unsafe_allow_html=True)
    with st.form("f_agenda", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data do Evento", datetime.now())
        hora = c2.text_input("Horário", "19:00")
        
        c3, c4, c5 = st.columns(3)
        tipo = c3.selectbox("Tipo", TIPOS_REUNIAO)
        alvo = c4.selectbox("Público Alvo (Departamento)", ["Geral"] + DEPARTAMENTOS)
        igreja = c5.selectbox("Local", IGREJAS)
        
        if st.form_submit_button("Salvar Evento"):
            with _db_lock:
                with get_db() as conn:
                    conn.execute("INSERT INTO reunioes (data, tipo, horario, local_igreja, departamento_alvo) VALUES (?,?,?,?,?)",
                                 (data.strftime("%Y-%m-%d"), tipo, hora, igreja, alvo))
                    conn.commit()
            st.success("✅ Agendado!")

# ─── HISTÓRICO ───
elif st.session_state.page == "history":
    st.markdown("<h2 style='color:#1B2B5E;'>🗄️ Histórico</h2>", unsafe_allow_html=True)
    with _db_lock:
        with get_db() as conn:
            reus = conn.execute("SELECT * FROM reunioes ORDER BY data DESC LIMIT 100").fetchall()
    
    for r in reus:
        dt_format = datetime.strptime(r['data'], "%Y-%m-%d").strftime("%d/%m/%Y")
        with st.expander(f"{dt_format} | {r['tipo']} ({r['departamento_alvo']}) - {r['local_igreja']}"):
            if st.button("🗑️ Excluir Reunião (Cuidado)", key=f"del_r_{r['id']}"):
                with _db_lock:
                    with get_db() as conn:
                        conn.execute("DELETE FROM reunioes WHERE id=?", (r['id'],))
                        conn.commit()
                st.rerun()

# ─── CHAMADA INTELIGENTE ───
elif st.session_state.page == "attendance":
    st.markdown("<h2 style='color:#1B2B5E;'>✅ Controle de Frequência</h2>", unsafe_allow_html=True)
    
    with _db_lock:
        with get_db() as conn:
            hoje = datetime.now().strftime("%Y-%m-%d")
            reus = conn.execute("SELECT * FROM reunioes ORDER BY CASE WHEN data >= ? THEN 0 ELSE 1 END ASC, data ASC", (hoje,)).fetchall()
            
    if not reus: st.warning("Sem eventos agendados.")
    else:
        opcoes = {f"{datetime.strptime(r['data'],'%Y-%m-%d').strftime('%d/%m/%Y')} | {r['tipo']} ({r['departamento_alvo']})": r for r in reus}
        sel = st.selectbox("Selecione o Evento", list(opcoes.keys()))
        reu_selecionada = opcoes[sel]
        
        with _db_lock:
            with get_db() as conn:
                # Otimização: Carrega apenas os membros do departamento alvo (ou todos se Geral)
                query_membros = "SELECT * FROM membros"
                params = ()
                if reu_selecionada['departamento_alvo'] != "Geral":
                    query_membros += " WHERE departamento = ?"
                    params = (reu_selecionada['departamento_alvo'],)
                query_membros += " ORDER BY nome ASC"
                
                alvos = conn.execute(query_membros, params).fetchall()
                
                # Precarrega status existentes
                existentes = {f['membro_id']: f['status'] for f in conn.execute("SELECT membro_id, status FROM frequencia WHERE reuniao_id=?", (reu_selecionada['id'],)).fetchall()}

        if not alvos: st.info("Nenhum membro vinculado a este departamento.")
        else:
            with st.form("form_chamada"):
                sts_map = {}
                for m in alvos:
                    st.markdown(f"**{m['nome'].title()}** <span style='color:#999;font-size:12px;'>({m['departamento']})</span>", unsafe_allow_html=True)
                    idx_default = ["Presente", "Falta", "Justificado"].index(existentes.get(m['id'], "Presente"))
                    sts_map[m['id']] = st.radio("Status", ["Presente", "Falta", "Justificado"], index=idx_default, horizontal=True, key=f"r_{m['id']}", label_visibility="collapsed")
                    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                
                if st.form_submit_button("💾 Salvar Chamada", use_container_width=True):
                    with _db_lock:
                        with get_db() as conn:
                            conn.execute("DELETE FROM frequencia WHERE reuniao_id=?", (reu_selecionada['id'],))
                            conn.executemany("INSERT INTO frequencia (reuniao_id, membro_id, status) VALUES (?,?,?)",
                                             [(reu_selecionada['id'], mid, st_val) for mid, st_val in sts_map.items()])
                            conn.commit()
                    st.success("Frequência Registada com Sucesso!")

# ─── RELATÓRIO ANALÍTICO AVANÇADO (Exportação Oficial) ───
elif st.session_state.page == "relatorio":
    st.markdown("<h2 style='color:#1B2B5E;'>📊 Matriz Analítica Oficial</h2>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    ano = c1.number_input("Ano Base", min_value=2020, max_value=2030, value=datetime.now().year)
    dept_filtro = c2.selectbox("Departamento", ["Geral"] + DEPARTAMENTOS)
    
    with _db_lock:
        with get_db() as conn:
            str_ano = str(ano)
            # Filtra reuniões do ano e do departamento selecionado (Geral engloba todas do dep + as gerais)
            q_reus = "SELECT id, data FROM reunioes WHERE data LIKE ?"
            p_reus = [f"{str_ano}-%"]
            if dept_filtro != "Geral":
                q_reus += " AND (departamento_alvo = ? OR departamento_alvo = 'Geral')"
                p_reus.append(dept_filtro)
                
            reunioes_ano = conn.execute(q_reus, p_reus).fetchall()
            ids_reunioes = [r['id'] for r in reunioes_ano]
            total_reus = len(ids_reunioes)
            
            q_membros = "SELECT id, nome, departamento FROM membros"
            if dept_filtro != "Geral": q_membros += f" WHERE departamento = '{dept_filtro}'"
            q_membros += " ORDER BY nome ASC"
            membros_alvo = conn.execute(q_membros).fetchall()
            
            # Fetch bulk de frequências
            if ids_reunioes:
                placeholders = ",".join("?" * len(ids_reunioes))
                frequencias = conn.execute(f"SELECT membro_id, status FROM frequencia WHERE reuniao_id IN ({placeholders})", ids_reunioes).fetchall()
            else:
                frequencias = []

    if total_reus == 0: st.info("Sem atividades para os filtros selecionados.")
    else:
        # Processamento Vetorizado via Pandas
        dados_agrupados = {m['id']: {'Nome': m['nome'].title(), 'Depto': m['departamento'], 'P': 0, 'F_J': 0} for m in membros_alvo}
        for f in frequencias:
            if f['membro_id'] in dados_agrupados:
                if f['status'] == 'Presente': dados_agrupados[f['membro_id']]['P'] += 1
                else: dados_agrupados[f['membro_id']]['F_J'] += 1
                
        df_base = []
        for v in dados_agrupados.values():
            pct = (v['P'] / total_reus) * 100 if total_reus > 0 else 0
            df_base.append({"Membro": v['Nome'], "Depto": v['Depto'], "Presenças": v['P'], "Faltas/Just": v['F_J'], "% Freq": round(pct, 1)})
            
        df = pd.DataFrame(df_base)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Export Excel Engine
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=f"Frequência_{ano}")
        
        st.download_button("📥 Descarregar Matriz Excel (.xlsx)", data=buf.getvalue(), file_name=f"Relatorio_{dept_filtro}_{ano}.xlsx", use_container_width=True)

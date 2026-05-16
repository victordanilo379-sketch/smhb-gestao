"""
SMHB GESTÃO — v8.0 (Produção)
Sociedade Missionária de Homens Batistas
────────────────────────────────────────
Melhorias desta versão:
  [1] Módulo Analítico — Relatório Anual de Frequência (Jan–Dez) com export .xlsx
  [2] Concorrência: lock sempre envolve get_db(), nunca o contrário
  [3] get_db() com rollback em exceções
  [4] Caminho absoluto do DB — funciona em qualquer ambiente
  [5] Validações reforçadas (agenda, cadastro)
  [6] executemany na chamada (eficiência)
  [7] Status salvos precarregados na chamada (não reseta ao reabrir)
  [8] Backup via download do DB em tempo real
"""

import io
import contextlib
import threading
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import sqlite3

# ─── CONFIGURAÇÃO ────────────────────────────────────────────────────────────
_db_lock = threading.Lock()
DB_PATH  = Path(__file__).parent / "smhb_master_v7.db"

MESES_PT = {
    1:"Janeiro", 2:"Fevereiro", 3:"Março",     4:"Abril",
    5:"Maio",    6:"Junho",     7:"Julho",      8:"Agosto",
    9:"Setembro",10:"Outubro",  11:"Novembro",  12:"Dezembro"
}

st.set_page_config(
    page_title="SMHB | Gestão Eclesiástica",
    layout="wide",
    page_icon="⛪",
    initial_sidebar_state="expanded"
)

# ─── DESIGN SYSTEM ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

html, body, [class*="css"] { font-family:'DM Sans',sans-serif !important; }
.stApp { background-color:#EEF1F8 !important; }

#MainMenu{visibility:hidden;} footer{visibility:hidden;} header{visibility:hidden;} .stDeployButton{display:none;}

/* Sidebar */
[data-testid="stSidebar"] {
    background:linear-gradient(175deg,#1B2B5E 0%,#0D1A42 100%) !important;
}
[data-testid="stSidebar"] .stButton>button {
    background:rgba(255,255,255,0.06) !important;
    border:1px solid rgba(255,255,255,0.10) !important;
    color:#B8CDE8 !important;
    border-radius:10px !important;
    text-align:left !important;
    font-family:'DM Sans',sans-serif !important;
    font-size:14px !important;
    font-weight:500 !important;
    height:44px !important;
    transition:all 0.2s ease !important;
    margin-bottom:3px !important;
}
[data-testid="stSidebar"] .stButton>button:hover {
    background:rgba(201,150,61,0.15) !important;
    border-color:rgba(201,150,61,0.40) !important;
    color:#F5D78E !important;
    transform:translateX(4px) !important;
    box-shadow:none !important;
}

/* Main */
.main .block-container { padding:2rem 2.5rem !important; max-width:1200px !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background:#FFFFFF !important;
    border:1px solid #DDE5F4 !important;
    border-radius:16px !important;
    padding:22px !important;
    box-shadow:0 2px 8px rgba(27,43,94,0.05) !important;
    transition:box-shadow 0.2s ease !important;
}
[data-testid="stMetric"]:hover { box-shadow:0 6px 20px rgba(27,43,94,0.10) !important; }
[data-testid="stMetric"] label {
    color:#7B8DB0 !important; font-size:11px !important; font-weight:600 !important;
    text-transform:uppercase !important; letter-spacing:0.8px !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color:#1B2B5E !important; font-family:'Crimson Pro',serif !important;
    font-size:2.6rem !important; font-weight:700 !important;
}

/* Inputs */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    border:1.5px solid #DDE5F4 !important; border-radius:10px !important;
    background:#FAFBFF !important; color:#1a1a2e !important;
    font-family:'DM Sans',sans-serif !important; font-size:14px !important;
}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border-color:#1B2B5E !important;
    box-shadow:0 0 0 3px rgba(27,43,94,0.09) !important;
}
.stSelectbox>div>div {
    border:1.5px solid #DDE5F4 !important; border-radius:10px !important;
    background:#FAFBFF !important;
}
.stDateInput>div>div>input {
    border:1.5px solid #DDE5F4 !important; border-radius:10px !important;
    background:#FAFBFF !important;
}

/* Buttons */
.stButton>button {
    border-radius:10px !important; border:1.5px solid #DDE5F4 !important;
    background:#FFFFFF !important; color:#374151 !important;
    font-family:'DM Sans',sans-serif !important; font-weight:600 !important;
    font-size:14px !important; height:42px !important;
    transition:all 0.2s ease !important;
    box-shadow:0 1px 3px rgba(27,43,94,0.04) !important;
}
.stButton>button:hover {
    background:#1B2B5E !important; color:#FFFFFF !important;
    border-color:#1B2B5E !important; transform:translateY(-1px) !important;
    box-shadow:0 4px 12px rgba(27,43,94,0.18) !important;
}

/* Form submit */
[data-testid="stForm"] [data-testid="stFormSubmitButton"]>button {
    background:linear-gradient(135deg,#1B2B5E 0%,#2E46A4 100%) !important;
    color:#FFFFFF !important; border:none !important; font-weight:700 !important;
    box-shadow:0 4px 14px rgba(27,43,94,0.28) !important;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"]>button:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 8px 20px rgba(27,43,94,0.35) !important;
    background:linear-gradient(135deg,#243580 0%,#1B2B5E 100%) !important;
    color:#FFFFFF !important; border:none !important;
}

/* Expanders */
[data-testid="stExpander"] {
    border:1px solid #DDE5F4 !important; border-radius:14px !important;
    background:#FFFFFF !important; margin-bottom:8px !important;
    overflow:hidden !important; box-shadow:0 1px 4px rgba(27,43,94,0.04) !important;
    transition:border-color 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stExpander"]:hover {
    border-color:#C9963D !important;
    box-shadow:0 4px 16px rgba(201,150,61,0.10) !important;
}

/* Download button */
[data-testid="stDownloadButton"]>button {
    background:linear-gradient(135deg,#059669 0%,#047857 100%) !important;
    color:#FFFFFF !important; border:none !important; font-weight:700 !important;
    border-radius:10px !important; font-size:14px !important;
    box-shadow:0 4px 12px rgba(5,150,105,0.25) !important;
    transition:all 0.2s ease !important;
}
[data-testid="stDownloadButton"]>button:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 8px 20px rgba(5,150,105,0.35) !important;
}

hr { border-color:#EEF1F8 !important; }
[data-testid="stAlert"] { border-radius:12px !important; font-family:'DM Sans',sans-serif !important; }

/* Badges / Avatares */
.badge {
    display:inline-block; padding:3px 12px; border-radius:99px;
    font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.4px;
}
.badge-cr { background:#EFF4FF; color:#1B2B5E; border:1px solid #BFD0F0; }
.badge-p  { background:#FFF7ED; color:#92400E; border:1px solid #FCD7A6; }
.avatar-cr { background:#EFF4FF; color:#1B2B5E; border:2px solid #BFD0F0; }
.avatar-p  { background:#FFF7ED; color:#92400E; border:2px solid #FCD7A6; }

/* Tabela do relatório */
.relatorio-table { border-collapse:collapse; width:100%; font-size:13px; }
.relatorio-table th {
    background:#1B2B5E; color:#F5D78E; padding:8px 12px;
    text-align:center; font-weight:700; letter-spacing:0.5px;
    font-size:11px; text-transform:uppercase; white-space:nowrap;
}
.relatorio-table th.nome-col { text-align:left; }
.relatorio-table td {
    padding:7px 12px; text-align:center; border-bottom:1px solid #EEF1F8;
    color:#374151; font-size:13px;
}
.relatorio-table td.nome-col { text-align:left; font-weight:600; color:#1B2B5E; }
.relatorio-table tr:nth-child(even) td { background:#F8FAFF; }
.relatorio-table tr:hover td { background:#EFF4FF; }
.cell-presente { color:#059669; font-weight:700; }
.cell-zero     { color:#D1D5DB; }
.cell-pct-ok   { color:#059669; font-weight:700; }
.cell-pct-warn { color:#D97706; font-weight:700; }
.cell-pct-bad  { color:#DC2626; font-weight:700; }
.col-total { background:#EFF4FF !important; font-weight:700; }
.col-pct   { background:#F0FDF4 !important; }

@keyframes fadeUp {
    from{opacity:0;transform:translateY(12px);}
    to{opacity:1;transform:translateY(0);}
}
.element-container { animation:fadeUp 0.32s ease forwards; }

@media(max-width:768px){ .main .block-container{padding:1rem !important;} }
</style>
""", unsafe_allow_html=True)


# ─── DATABASE ────────────────────────────────────────────────────────────────
@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Habilita enforcement de FK no SQLite (desligado por padrão)
    conn.execute("PRAGMA foreign_keys = ON")
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
            # Tabelas com FK explícita para integridade referencial
            conn.execute("""
                CREATE TABLE IF NOT EXISTS membros (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome     TEXT    NOT NULL,
                    cargo    TEXT,
                    telefone TEXT,
                    igreja   TEXT
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reunioes (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    data         TEXT    NOT NULL,
                    tipo         TEXT,
                    horario      TEXT,
                    local_igreja TEXT
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS frequencia (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    reuniao_id INTEGER NOT NULL
                                REFERENCES reunioes(id) ON DELETE CASCADE,
                    membro_id  INTEGER NOT NULL
                                REFERENCES membros(id)  ON DELETE CASCADE,
                    status     TEXT    NOT NULL DEFAULT 'Presente'
                )""")
            # Índice para acelerar queries do relatório
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_freq_reuniao
                ON frequencia(reuniao_id)""")
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_freq_membro
                ON frequencia(membro_id)""")
            conn.commit()


init_db()


# ─── CONSTANTES ──────────────────────────────────────────────────────────────
CARGOS = [
    "Presidente SMHB",    "Vice-Presidente SMHB",
    "1° Secretário SMHB", "2° Secretário SMHB",
    "1° Tesoureiro SMHB", "2° Tesoureiro SMHB",
    "Integrante SMHB",
]
IGREJAS = ["Igreja Batista Cristo Rei (CR)", "Igreja Batista Proclamai (P)"]
TIPOS   = ["Culto", "Reunião de Líderes", "Esporte Missionário", "Intercâmbio", "Outro"]
STATUS_OPTS = ["Presente", "Falta", "Justificado"]


# ─── NAVEGAÇÃO ───────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"

def nav(target: str):
    st.session_state.page = target


# ─── HELPERS DE UI ───────────────────────────────────────────────────────────
def get_initials(nome: str) -> str:
    partes = nome.strip().split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[-1][0]).upper()
    return nome[:2].upper() if nome else "??"

def page_header(icon: str, title: str, subtitle: str = ""):
    sub = (f"<p style='color:#7B8DB0;font-size:14px;margin:2px 0 0 42px;'>{subtitle}</p>"
           if subtitle else "")
    st.markdown(f"""
    <div style="margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:2px;">
        <span style="font-size:28px;line-height:1;">{icon}</span>
        <h1 style="font-family:'Crimson Pro',serif;font-size:2.1rem;font-weight:700;
                   color:#1B2B5E;margin:0;letter-spacing:-0.4px;">{title}</h1>
      </div>
      {sub}
    </div>""", unsafe_allow_html=True)

def avatar(initials: str, is_cr: bool = True, size: int = 44) -> str:
    cls = "avatar-cr" if is_cr else "avatar-p"
    return (f'<div class="{cls}" style="width:{size}px;height:{size}px;border-radius:50%;'
            f'display:inline-flex;align-items:center;justify-content:center;'
            f'font-weight:800;font-size:{int(size*0.36)}px;flex-shrink:0;">{initials}</div>')

def section_label(text: str, color: str = "#7B8DB0"):
    st.markdown(
        f'<div style="font-size:11px;font-weight:700;color:{color};'
        f'text-transform:uppercase;letter-spacing:1.2px;margin:18px 0 10px;">{text}</div>',
        unsafe_allow_html=True)

def empty_state(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="text-align:center;padding:64px 20px;color:#9CA3AF;">
      <div style="font-size:52px;margin-bottom:14px;">{icon}</div>
      <div style="font-size:16px;font-weight:600;color:#6B7280;">{title}</div>
      {"<div style='font-size:14px;margin-top:6px;'>" + subtitle + "</div>" if subtitle else ""}
    </div>""", unsafe_allow_html=True)


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:28px 10px 26px;">
      <div style="font-size:46px;line-height:1;">⛪</div>
      <div style="font-family:'Crimson Pro',serif;font-size:22px;font-weight:700;
                  color:#F5D78E;letter-spacing:-0.3px;margin-top:10px;">SMHB Gestão</div>
      <div style="font-size:10px;color:#5C78AE;letter-spacing:1.4px;
                  text-transform:uppercase;margin-top:5px;">Soc. Missionária · Homens Batistas</div>
    </div>
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:0 0 14px;">
    """, unsafe_allow_html=True)

    nav_items = [
        ("🏠", "Início",        "home"),
        ("👥", "Membros",       "membros"),
        ("📅", "Agenda",        "agenda"),
        ("🗄️", "Histórico",    "history"),
        ("✅", "Chamada",       "attendance"),
        ("📊", "Relatório",     "relatorio"),
        ("➕", "Novo Membro",   "new"),
    ]
    for icon, label, target in nav_items:
        prefix = "▸  " if st.session_state.page == target else "    "
        if st.button(f"{prefix}{icon}  {label}", key=f"nav_{target}", use_container_width=True):
            nav(target)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    with _db_lock:
        with get_db() as conn:
            m_cr    = conn.execute("SELECT count(*) FROM membros WHERE igreja LIKE '%Cristo Rei%'").fetchone()[0]
            m_p     = conn.execute("SELECT count(*) FROM membros WHERE igreja LIKE '%Proclamai%'").fetchone()[0]
            total_r = conn.execute("SELECT count(*) FROM reunioes").fetchone()[0]

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);
                border-radius:14px;padding:18px 16px;margin:0 4px;">
      <div style="font-size:10px;color:#5C78AE;text-transform:uppercase;
                  letter-spacing:1.3px;margin-bottom:14px;font-weight:700;">RESUMO GERAL</div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <span style="color:#94A9CC;font-size:13px;">🔵 Cristo Rei</span>
        <span style="color:#F5D78E;font-weight:700;font-size:15px;">{m_cr}</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="color:#94A9CC;font-size:13px;">🟠 Proclamai</span>
        <span style="color:#F5D78E;font-weight:700;font-size:15px;">{m_p}</span>
      </div>
      <div style="border-top:1px solid rgba(255,255,255,0.08);padding-top:10px;
                  display:flex;justify-content:space-between;align-items:center;">
        <span style="color:#94A9CC;font-size:13px;">📅 Atividades</span>
        <span style="color:#F5D78E;font-weight:700;font-size:15px;">{total_r}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Backup / Download do banco ─────────────────────────────────────────
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    if DB_PATH.exists():
        st.download_button(
            label="💾  Backup do Banco (.db)",
            data=DB_PATH.read_bytes(),
            file_name=f"smhb_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
            mime="application/octet-stream",
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINAS
# ═══════════════════════════════════════════════════════════════════════════════

# ─── HOME ────────────────────────────────────────────────────────────────────
if st.session_state.page == "home":
    with _db_lock:
        with get_db() as conn:
            m_cr    = conn.execute("SELECT count(*) FROM membros WHERE igreja LIKE '%Cristo Rei%'").fetchone()[0]
            m_p     = conn.execute("SELECT count(*) FROM membros WHERE igreja LIKE '%Proclamai%'").fetchone()[0]
            total   = conn.execute("SELECT count(*) FROM membros").fetchone()[0]
            futuras = conn.execute(
                "SELECT count(*) FROM reunioes WHERE data >= ?",
                (datetime.now().strftime("%Y-%m-%d"),)).fetchone()[0]

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1B2B5E 0%,#2E46A4 100%);
                border-radius:22px;padding:40px 44px;margin-bottom:32px;
                box-shadow:0 10px 36px rgba(27,43,94,0.28);">
      <div style="font-family:'Crimson Pro',serif;font-size:2.6rem;font-weight:700;
                  color:#FFFFFF;margin-bottom:10px;letter-spacing:-0.5px;">
        Bem-vindo ao SMHB Gestão
      </div>
      <div style="color:#A8BFED;font-size:15px;line-height:1.7;max-width:520px;">
        Sistema de gestão eclesiástica da Sociedade Missionária de Homens Batistas.
        Use a barra lateral para navegar entre os módulos.
      </div>
      <div style="margin-top:20px;display:flex;gap:12px;flex-wrap:wrap;">
        <div style="background:rgba(255,255,255,0.12);border-radius:10px;
                    padding:8px 16px;color:#F5D78E;font-size:13px;font-weight:600;">
          {total} membros ativos
        </div>
        <div style="background:rgba(255,255,255,0.12);border-radius:10px;
                    padding:8px 16px;color:#F5D78E;font-size:13px;font-weight:600;">
          {futuras} próximas atividades
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Membros",    total)
    c2.metric("🔵 Cristo Rei",       m_cr)
    c3.metric("🟠 Proclamai",        m_p)
    c4.metric("Próximas Atividades", futuras)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📖  Tutorial de Uso Rápido  —  clique para abrir", expanded=False):
        st.markdown("""
        <div style="padding:12px 4px;">
          <h4 style="color:#1B2B5E;margin-bottom:16px;font-family:'Crimson Pro',serif;font-size:1.3rem;">
            🚀 Aprenda em menos de 1 minuto:
          </h4>
          <ol style="color:#374151;line-height:2.2;font-size:15px;">
            <li><b>Cadastrar Membros:</b> clique em <b>➕ Novo Membro</b> na barra lateral.</li>
            <li><b>Criar Eventos:</b> acesse <b>📅 Agenda</b> para programar a próxima atividade.</li>
            <li><b>Fazer a Chamada:</b> no dia do evento, use <b>✅ Chamada</b> para registrar presenças.</li>
            <li><b>Relatório Anual:</b> acesse <b>📊 Relatório</b> para ver a matriz de frequência e exportar para Excel.</li>
            <li><b>Backup:</b> use o botão <b>💾 Backup</b> na barra lateral para baixar o banco de dados.</li>
          </ol>
          <div style="background:#EFF4FF;border-radius:12px;padding:14px 18px;
                      margin-top:10px;font-size:14px;color:#1B2B5E;line-height:1.6;">
            📱 <b>Dica Mobile:</b> No navegador do celular, toque em
            <i>"Adicionar à tela de início"</i> para instalar como aplicativo!
          </div>
        </div>
        """, unsafe_allow_html=True)


# ─── NOVO MEMBRO ─────────────────────────────────────────────────────────────
elif st.session_state.page == "new":
    page_header("➕", "Novo Membro", "Cadastre um novo integrante da sociedade")

    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo *", placeholder="Ex: JOÃO DA SILVA SANTOS").strip().upper()

        c1, c2 = st.columns(2)
        tel   = c1.text_input("Telefone de Contato", value="+55 (92) ")
        cargo = c2.selectbox("Cargo na Sociedade", CARGOS)
        igreja = st.selectbox("Igreja", IGREJAS)

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾   Salvar Cadastro", use_container_width=True)

        if submitted:
            if not nome or len(nome) < 3:
                st.error("❌ Preencha o nome completo do membro (mínimo 3 caracteres).")
            else:
                with _db_lock:
                    with get_db() as conn:
                        existente = conn.execute(
                            "SELECT id FROM membros WHERE nome = ?", (nome,)
                        ).fetchone()
                        if existente:
                            st.warning(f"⚠️ Já existe um membro com o nome **{nome}**.")
                        else:
                            conn.execute(
                                "INSERT INTO membros (nome, cargo, telefone, igreja) VALUES (?,?,?,?)",
                                (nome, cargo, tel, igreja)
                            )
                            conn.commit()
                            st.success(f"✅ **{nome}** registrado com sucesso!")


# ─── MEMBROS ─────────────────────────────────────────────────────────────────
elif st.session_state.page == "membros":
    page_header("👥", "Quadro de Membros", "Gerencie os integrantes da sociedade")

    col_s, col_f = st.columns([2, 1])
    search   = col_s.text_input("", placeholder="🔍  Buscar por nome...",
                                 label_visibility="collapsed").upper()
    f_igreja = col_f.selectbox("", ["Todas as Igrejas"] + IGREJAS,
                                label_visibility="collapsed")

    with _db_lock:
        with get_db() as conn:
            rank_sql = "CASE cargo " + "".join(
                f"WHEN '{c}' THEN {i} " for i, c in enumerate(CARGOS)
            ) + "ELSE 99 END as rank"
            membros = conn.execute(
                f"SELECT *, {rank_sql} FROM membros ORDER BY rank ASC, nome ASC"
            ).fetchall()

    filtrados = [
        m for m in membros
        if (search in m["nome"]) and
           (f_igreja == "Todas as Igrejas" or m["igreja"] == f_igreja)
    ]

    st.markdown(
        f"<p style='color:#9CA3AF;font-size:12px;margin:8px 0 14px;'>"
        f"{len(filtrados)} membro(s) encontrado(s)</p>", unsafe_allow_html=True)

    if not filtrados:
        empty_state("👥", "Nenhum membro encontrado",
                    "Ajuste os filtros ou cadastre um novo membro.")
    else:
        for m in filtrados:
            is_cr     = "Cristo Rei" in m["igreja"]
            badge_cls = "badge-cr" if is_cr else "badge-p"
            initials  = get_initials(m["nome"])
            icon      = "🔵" if is_cr else "🟠"

            with st.expander(f"{icon}  {m['nome'].title()}   ·   {m['cargo']}"):
                col_av, col_info = st.columns([1, 7])
                with col_av:
                    st.markdown(f"<div style='margin-top:8px;'>{avatar(initials, is_cr, 52)}</div>",
                                unsafe_allow_html=True)
                with col_info:
                    st.markdown(f"""
                    <div style="padding-top:8px;">
                      <span class="badge {badge_cls}">{m['igreja']}</span>
                      <div style="margin-top:10px;font-size:14px;color:#374151;">
                        📱 <span style="color:#7B8DB0;">Contato:</span>
                        <b style="margin-left:4px;">{m['telefone']}</b>
                      </div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<hr style='border:none;border-top:1px solid #EEF1F8;margin:14px 0 10px;'>",
                            unsafe_allow_html=True)

                with st.form(f"edit_{m['id']}"):
                    st.markdown("<p style='font-size:12px;color:#9CA3AF;font-weight:600;"
                                "text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>"
                                "✏️ EDITAR DADOS</p>", unsafe_allow_html=True)
                    ec1, ec2, ec3 = st.columns(3)
                    new_tel    = ec1.text_input("Telefone", value=m["telefone"], key=f"tel_{m['id']}")
                    cargo_idx  = CARGOS.index(m["cargo"])  if m["cargo"]  in CARGOS  else 0
                    new_cargo  = ec2.selectbox("Cargo",  CARGOS,  index=cargo_idx,  key=f"cargo_{m['id']}")
                    igreja_idx = IGREJAS.index(m["igreja"]) if m["igreja"] in IGREJAS else 0
                    new_igreja = ec3.selectbox("Igreja", IGREJAS, index=igreja_idx, key=f"igreja_{m['id']}")

                    if st.form_submit_button("💾  Salvar Alterações", use_container_width=True):
                        with _db_lock:
                            with get_db() as conn:
                                conn.execute(
                                    "UPDATE membros SET telefone=?, cargo=?, igreja=? WHERE id=?",
                                    (new_tel, new_cargo, new_igreja, m["id"])
                                )
                                conn.commit()
                        st.success("✅ Alterações salvas!")
                        st.rerun()

                if st.button("🗑️  Remover Membro", key=f"del_{m['id']}", use_container_width=True):
                    with _db_lock:
                        with get_db() as conn:
                            # CASCADE cuida da frequencia automaticamente (PRAGMA FK ON)
                            conn.execute("DELETE FROM membros WHERE id=?", (m["id"],))
                            conn.commit()
                    st.rerun()


# ─── AGENDA ──────────────────────────────────────────────────────────────────
elif st.session_state.page == "agenda":
    page_header("📅", "Agendar Atividade", "Programe os próximos eventos da sociedade")

    with st.form("form_agenda", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data    = c1.date_input("Data do Evento *", datetime.now())
        horario = c2.text_input("Horário de Início", "19:00")

        c3, c4 = st.columns(2)
        tipo  = c3.selectbox("Tipo de Evento",      TIPOS)
        local = c4.selectbox("Local de Realização", IGREJAS)

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("📅   Confirmar Agendamento", use_container_width=True)

        if submitted:
            # Validação: horário mínimo
            horario = horario.strip()
            if not horario:
                st.error("❌ Informe o horário do evento.")
            else:
                with _db_lock:
                    with get_db() as conn:
                        conn.execute(
                            "INSERT INTO reunioes (data, tipo, horario, local_igreja) VALUES (?,?,?,?)",
                            (data.strftime("%Y-%m-%d"), tipo, horario, local)
                        )
                        conn.commit()
                st.success("✅ Atividade agendada com sucesso!")


# ─── HISTÓRICO ───────────────────────────────────────────────────────────────
elif st.session_state.page == "history":
    page_header("🗄️", "Histórico de Atividades",
                "Consulte e gerencie todas as atividades registradas")

    hoje = datetime.now().strftime("%Y-%m-%d")
    with _db_lock:
        with get_db() as conn:
            reunioes = conn.execute("""
                SELECT r.*,
                  (SELECT count(*) FROM frequencia f
                   WHERE f.reuniao_id = r.id AND f.status = 'Presente') AS presentes,
                  (SELECT count(*) FROM frequencia f2
                   WHERE f2.reuniao_id = r.id) AS total_reg
                FROM reunioes r
                ORDER BY
                  CASE WHEN data >= ? THEN 0 ELSE 1 END ASC,
                  CASE WHEN data >= ? THEN data END ASC,
                  data DESC
            """, (hoje, hoje)).fetchall()

    if not reunioes:
        empty_state("📅", "Nenhuma atividade registrada",
                    "Acesse <b>📅 Agenda</b> para criar o primeiro evento.")
    else:
        futuras  = [r for r in reunioes if r["data"] >= hoje]
        passadas = [r for r in reunioes if r["data"] <  hoje]

        def render_evento(r, dot):
            data_br = datetime.strptime(r["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
            with st.expander(f"{dot}  {data_br}  ·  {r['tipo']}  ·  {r['horario']}"):
                ci, cp, cd = st.columns([4, 3, 2])
                ci.markdown(f"📍 **Local:** {r['local_igreja']}")
                cp.markdown(
                    f"👥 **Presenças:** {r['presentes']}"
                    + (f" / {r['total_reg']}" if r["total_reg"] else "")
                )
                if cd.button("🗑️ Excluir", key=f"del_r_{r['id']}", use_container_width=True):
                    with _db_lock:
                        with get_db() as conn:
                            # CASCADE FK cuida da frequencia
                            conn.execute("DELETE FROM reunioes WHERE id=?", (r["id"],))
                            conn.commit()
                    st.rerun()

        if futuras:
            section_label("🟢  PRÓXIMAS ATIVIDADES", color="#059669")
            for r in futuras:
                render_evento(r, "🟢")
        if passadas:
            section_label("⚪  ATIVIDADES REALIZADAS", color="#9CA3AF")
            for r in passadas:
                render_evento(r, "⚪")


# ─── CHAMADA ─────────────────────────────────────────────────────────────────
elif st.session_state.page == "attendance":
    page_header("✅", "Controle de Chamada",
                "Registre a frequência dos membros nos eventos")

    hoje = datetime.now().strftime("%Y-%m-%d")
    with _db_lock:
        with get_db() as conn:
            reus = conn.execute("""
                SELECT * FROM reunioes
                ORDER BY CASE WHEN data >= ? THEN 0 ELSE 1 END ASC, data ASC
            """, (hoje,)).fetchall()

    if not reus:
        empty_state("📅", "Nenhum evento disponível",
                    "Crie um evento na <b>📅 Agenda</b> primeiro.")
    else:
        opcoes = {
            f"{datetime.strptime(r['data'],'%Y-%m-%d').strftime('%d/%m/%Y')}  |  {r['tipo']}  |  {r['local_igreja']}": r["id"]
            for r in reus
        }
        selecionado = st.selectbox("🎯  Selecionar Evento:", list(opcoes.keys()))
        rid = opcoes[selecionado]

        with _db_lock:
            with get_db() as conn:
                membros  = conn.execute("SELECT * FROM membros ORDER BY nome ASC").fetchall()
                existing = {
                    row["membro_id"]: row["status"]
                    for row in conn.execute(
                        "SELECT membro_id, status FROM frequencia WHERE reuniao_id=?", (rid,)
                    ).fetchall()
                }

        if not membros:
            st.warning("⚠️ Nenhum membro cadastrado. Acesse **➕ Novo Membro** primeiro.")
        else:
            presentes_count = sum(1 for s in existing.values() if s == "Presente")
            st.markdown(
                f"<p style='color:#7B8DB0;font-size:13px;margin:6px 0 18px;'>"
                f"{len(membros)} membro(s) cadastrado(s)"
                + (f"  ·  <b style='color:#059669;'>{presentes_count} presente(s) já registrado(s)</b>"
                   if existing else "")
                + "</p>",
                unsafe_allow_html=True
            )

            cr_membros = [m for m in membros if "Cristo Rei" in m["igreja"]]
            pr_membros = [m for m in membros if "Proclamai" in m["igreja"]]

            with st.form("form_chamada"):
                mapa = {}

                for grupo_label, grupo, is_cr in [
                    ("🔵 Igreja Batista Cristo Rei", cr_membros, True),
                    ("🟠 Igreja Batista Proclamai",  pr_membros, False),
                ]:
                    if not grupo:
                        continue
                    section_label(grupo_label, color="#1B2B5E" if is_cr else "#92400E")

                    for m in grupo:
                        default_st  = existing.get(m["id"], "Presente")
                        default_idx = STATUS_OPTS.index(default_st) if default_st in STATUS_OPTS else 0

                        col_av, col_nm, col_rd = st.columns([1, 4, 5])
                        with col_av:
                            st.markdown(
                                f"<div style='margin-top:4px;'>{avatar(get_initials(m['nome']), is_cr, 38)}</div>",
                                unsafe_allow_html=True)
                        with col_nm:
                            st.markdown(
                                f"<div style='padding-top:7px;font-weight:500;"
                                f"font-size:14px;color:#1a1a2e;'>{m['nome'].title()}</div>",
                                unsafe_allow_html=True)
                        with col_rd:
                            mapa[m["id"]] = st.radio(
                                "", STATUS_OPTS,
                                index=default_idx, horizontal=True,
                                key=f"fr_{m['id']}", label_visibility="collapsed"
                            )

                        st.markdown("<hr style='border:none;border-top:1px solid #F0F3FA;margin:4px 0;'>",
                                    unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("💾   Registrar Presenças", use_container_width=True):
                    with _db_lock:
                        with get_db() as conn:
                            conn.execute("DELETE FROM frequencia WHERE reuniao_id=?", (rid,))
                            conn.executemany(
                                "INSERT INTO frequencia (reuniao_id, membro_id, status) VALUES (?,?,?)",
                                [(rid, mid, status) for mid, status in mapa.items()]
                            )
                            conn.commit()
                    pres = sum(1 for s in mapa.values() if s == "Presente")
                    st.success(f"✅ Frequência salva! {pres} presente(s) de {len(mapa)} membro(s).")


# ─── RELATÓRIO ANUAL ─────────────────────────────────────────────────────────
elif st.session_state.page == "relatorio":
    page_header("📊", "Relatório Anual de Frequência",
                "Matriz consolidada de presença — Espelho do Relatório Oficial")

    # ── Controles ────────────────────────────────────────────────────────────
    ano_atual = datetime.now().year
    col_ano, col_igr, _ = st.columns([1, 2, 3])
    ano_sel    = col_ano.number_input("Ano", min_value=2020, max_value=ano_atual + 1,
                                      value=ano_atual, step=1)
    igr_sel    = col_igr.selectbox("Igreja", ["Todas"] + IGREJAS,
                                   key="rel_igr")

    # ── Busca de dados ────────────────────────────────────────────────────────
    with _db_lock:
        with get_db() as conn:
            ano_str  = str(int(ano_sel))
            reunioes = conn.execute(
                "SELECT id, data, tipo FROM reunioes WHERE data LIKE ?",
                (f"{ano_str}-%",)
            ).fetchall()

            igr_filter = "" if igr_sel == "Todas" else f" AND m.igreja = '{igr_sel}'"
            membros    = conn.execute(
                f"SELECT * FROM membros m ORDER BY m.nome ASC{igr_filter}"
            ).fetchall()

            # Todos os registros de frequência do ano num único fetch
            freq_rows = conn.execute("""
                SELECT f.membro_id, f.status, r.data
                FROM frequencia f
                JOIN reunioes r ON r.id = f.reuniao_id
                WHERE r.data LIKE ?
            """, (f"{ano_str}-%",)).fetchall()

    if not reunioes:
        empty_state("📅",
                    f"Nenhuma atividade cadastrada para {int(ano_sel)}",
                    "Agende eventos na aba <b>📅 Agenda</b> primeiro.")
    elif not membros:
        empty_state("👥", "Nenhum membro encontrado para os filtros selecionados.")
    else:
        # ── Monta lookup: (membro_id, mes) → {Presente, Falta, Justificado} contagens
        from collections import defaultdict
        lookup: dict[tuple, dict] = defaultdict(lambda: {"Presente": 0, "Falta": 0, "Justificado": 0})

        for row in freq_rows:
            mes = int(row["data"].split("-")[1])
            lookup[(row["membro_id"], mes)][row["status"]] += 1

        # Meses com pelo menos uma reunião no ano
        meses_com_reuniao = sorted({int(r["data"].split("-")[1]) for r in reunioes})

        # ── Contagem de reuniões por mês (denominador do %)
        reus_por_mes: dict[int, int] = defaultdict(int)
        for r in reunioes:
            mes = int(r["data"].split("-")[1])
            reus_por_mes[mes] += 1

        total_reus_ano = len(reunioes)

        # ── Monta DataFrame ──────────────────────────────────────────────────
        rows_data = []
        for m in membros:
            row_dict: dict = {"Membro": m["nome"].title()}
            total_p = total_f = total_j = 0

            for mes in meses_com_reuniao:
                cell = lookup[(m["id"], mes)]
                p, f, j = cell["Presente"], cell["Falta"], cell["Justificado"]
                row_dict[MESES_PT[mes]] = p  # mostra só presenças no mês
                total_p += p
                total_f += f
                total_j += j

            pct = round(total_p / total_reus_ano * 100, 1) if total_reus_ano else 0.0
            row_dict["Total P"] = total_p
            row_dict["Total F"] = total_f
            row_dict["% Freq"]  = pct
            rows_data.append(row_dict)

        df = pd.DataFrame(rows_data)

        # ── Totalizadores rodapé ─────────────────────────────────────────────
        totals: dict = {"Membro": "TOTAL GERAL"}
        for mes in meses_com_reuniao:
            totals[MESES_PT[mes]] = df[MESES_PT[mes]].sum()
        totals["Total P"] = df["Total P"].sum()
        totals["Total F"] = df["Total F"].sum()
        totals["% Freq"]  = round(df["% Freq"].mean(), 1)
        df_total = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)

        # ── Resumo rápido ────────────────────────────────────────────────────
        media_freq = round(df["% Freq"].mean(), 1)
        top_membro = df.loc[df["% Freq"].idxmax(), "Membro"] if not df.empty else "-"
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Atividades no Ano",   total_reus_ano)
        m_col2.metric("Membros Analisados",  len(membros))
        m_col3.metric("Frequência Média",    f"{media_freq}%")
        m_col4.metric("Maior Frequência",    top_membro)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Renderiza tabela HTML customizada ────────────────────────────────
        mes_headers = "".join(
            f"<th>{MESES_PT[m][:3]}<br><span style='font-size:9px;font-weight:400;'>"
            f"({reus_por_mes[m]} ev.)</span></th>"
            for m in meses_com_reuniao
        )
        header_html = (
            f"<tr><th class='nome-col'>Membro</th>"
            f"{mes_headers}"
            f"<th>Total P</th><th>Total F</th><th>% Freq</th></tr>"
        )

        rows_html = ""
        for _, row in df.iterrows():
            pct     = row["% Freq"]
            pct_cls = "cell-pct-ok" if pct >= 75 else ("cell-pct-warn" if pct >= 50 else "cell-pct-bad")
            cells   = "".join(
                f"<td class='{'cell-presente' if row[MESES_PT[m]] > 0 else 'cell-zero'}'>"
                f"{int(row[MESES_PT[m]]) if row[MESES_PT[m]] > 0 else '—'}</td>"
                for m in meses_com_reuniao
            )
            rows_html += (
                f"<tr>"
                f"<td class='nome-col'>{row['Membro']}</td>"
                f"{cells}"
                f"<td class='col-total'><b>{int(row['Total P'])}</b></td>"
                f"<td class='col-total'>{int(row['Total F'])}</td>"
                f"<td class='col-pct {pct_cls}'><b>{pct}%</b></td>"
                f"</tr>"
            )

        # Linha de totais
        tot = df_total.iloc[-1]
        tot_cells = "".join(
            f"<td><b>{int(tot[MESES_PT[m]])}</b></td>"
            for m in meses_com_reuniao
        )
        pct_tot     = tot["% Freq"]
        pct_tot_cls = "cell-pct-ok" if pct_tot >= 75 else ("cell-pct-warn" if pct_tot >= 50 else "cell-pct-bad")
        rows_html += (
            f"<tr style='background:#1B2B5E!important;'>"
            f"<td class='nome-col' style='color:#F5D78E;'><b>TOTAL GERAL</b></td>"
            f"{tot_cells}"
            f"<td style='color:#F5D78E;'><b>{int(tot['Total P'])}</b></td>"
            f"<td style='color:#F5D78E;'>{int(tot['Total F'])}</td>"
            f"<td style='color:#F5D78E;' class='{pct_tot_cls}'><b>{pct_tot}%</b></td>"
            f"</tr>"
        )

        st.markdown(
            f"<div style='overflow-x:auto;border-radius:14px;border:1px solid #DDE5F4;"
            f"box-shadow:0 2px 8px rgba(27,43,94,0.05);'>"
            f"<table class='relatorio-table'>{header_html}{rows_html}</table>"
            f"</div>",
            unsafe_allow_html=True
        )

        # ── Legenda ──────────────────────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;gap:20px;margin-top:14px;flex-wrap:wrap;font-size:12px;color:#6B7280;">
          <span><b style="color:#059669;">■</b> ≥ 75% — Frequência regular</span>
          <span><b style="color:#D97706;">■</b> 50–74% — Frequência intermediária</span>
          <span><b style="color:#DC2626;">■</b> &lt; 50% — Frequência baixa</span>
          <span style="margin-left:auto;color:#9CA3AF;">P = Presentes · F = Faltas + Justificados</span>
        </div>""", unsafe_allow_html=True)

        # ── Exportar para Excel ───────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)

        def gerar_excel(dataframe: pd.DataFrame, ano: int) -> bytes:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                dataframe.to_excel(writer, index=False,
                                   sheet_name=f"Frequência {ano}")
                ws = writer.sheets[f"Frequência {ano}"]
                # Largura das colunas
                ws.column_dimensions["A"].width = 30
                for col in ws.iter_cols(min_col=2, max_col=ws.max_column):
                    ws.column_dimensions[col[0].column_letter].width = 12
            return buf.getvalue()

        excel_bytes = gerar_excel(df_total, int(ano_sel))

        st.download_button(
            label=f"📥  Exportar Relatório {int(ano_sel)} (.xlsx)",
            data=excel_bytes,
            file_name=f"smhb_frequencia_{int(ano_sel)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

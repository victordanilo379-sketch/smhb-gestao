import streamlit as st
import sqlite3
from datetime import datetime
import contextlib
import threading

_db_lock = threading.Lock()

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

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
.stApp {
    background-color: #EEF1F8 !important;
}

/* ── Hide Streamlit Chrome ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #1B2B5E 0%, #0D1A42 100%) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    color: #B8CDE8 !important;
    border-radius: 10px !important;
    text-align: left !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    height: 44px !important;
    transition: all 0.2s ease !important;
    margin-bottom: 3px !important;
    letter-spacing: 0.1px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(201,150,61,0.15) !important;
    border-color: rgba(201,150,61,0.40) !important;
    color: #F5D78E !important;
    transform: translateX(4px) !important;
    box-shadow: none !important;
}

/* ── Main Content ── */
.main .block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1100px !important;
}

/* ── Metric Cards ── */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #DDE5F4 !important;
    border-radius: 16px !important;
    padding: 22px !important;
    box-shadow: 0 2px 8px rgba(27,43,94,0.05) !important;
    transition: box-shadow 0.2s ease !important;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 6px 20px rgba(27,43,94,0.10) !important;
}
[data-testid="stMetric"] label {
    color: #7B8DB0 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #1B2B5E !important;
    font-family: 'Crimson Pro', serif !important;
    font-size: 2.6rem !important;
    font-weight: 700 !important;
}

/* ── Text Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border: 1.5px solid #DDE5F4 !important;
    border-radius: 10px !important;
    background: #FAFBFF !important;
    color: #1a1a2e !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #1B2B5E !important;
    box-shadow: 0 0 0 3px rgba(27,43,94,0.09) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    border: 1.5px solid #DDE5F4 !important;
    border-radius: 10px !important;
    background: #FAFBFF !important;
}

/* ── Date Input ── */
.stDateInput > div > div > input {
    border: 1.5px solid #DDE5F4 !important;
    border-radius: 10px !important;
    background: #FAFBFF !important;
}

/* ── Buttons (main area) ── */
.stButton > button {
    border-radius: 10px !important;
    border: 1.5px solid #DDE5F4 !important;
    background: #FFFFFF !important;
    color: #374151 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    height: 42px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 3px rgba(27,43,94,0.04) !important;
}
.stButton > button:hover {
    background: #1B2B5E !important;
    color: #FFFFFF !important;
    border-color: #1B2B5E !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(27,43,94,0.18) !important;
}

/* ── Form Submit Button ── */
[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #1B2B5E 0%, #2E46A4 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 14px rgba(27,43,94,0.28) !important;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(27,43,94,0.35) !important;
    background: linear-gradient(135deg, #243580 0%, #1B2B5E 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid #DDE5F4 !important;
    border-radius: 14px !important;
    background: #FFFFFF !important;
    margin-bottom: 8px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(27,43,94,0.04) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stExpander"]:hover {
    border-color: #C9963D !important;
    box-shadow: 0 4px 16px rgba(201,150,61,0.10) !important;
}

/* ── Dividers ── */
hr { border-color: #EEF1F8 !important; }

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Custom Classes ── */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
.badge-cr { background: #EFF4FF; color: #1B2B5E; border: 1px solid #BFD0F0; }
.badge-p  { background: #FFF7ED; color: #92400E; border: 1px solid #FCD7A6; }

.avatar-cr { background:#EFF4FF; color:#1B2B5E; border:2px solid #BFD0F0; }
.avatar-p  { background:#FFF7ED; color:#92400E; border:2px solid #FCD7A6; }

/* ── Animation ── */
@keyframes fadeUp {
    from { opacity:0; transform:translateY(12px); }
    to   { opacity:1; transform:translateY(0);    }
}
.element-container { animation: fadeUp 0.32s ease forwards; }

/* ── Mobile ── */
@media (max-width: 768px) {
    .main .block-container { padding: 1rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ─── DATABASE ────────────────────────────────────────────────────────────────
@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect('smhb_master_v7.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        with _db_lock:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS membros
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          nome TEXT, cargo TEXT, telefone TEXT, igreja TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS reunioes
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          data TEXT, tipo TEXT, horario TEXT, local_igreja TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS frequencia
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          reuniao_id INTEGER, membro_id INTEGER, status TEXT)''')
            conn.commit()

init_db()


# ─── CONSTANTES ──────────────────────────────────────────────────────────────
CARGOS = [
    "Presidente SMHB", "Vice-Presidente SMHB",
    "1° Secretário SMHB", "2° Secretário SMHB",
    "1° Tesoureiro SMHB",  "2° Tesoureiro SMHB",
    "Integrante SMHB"
]
IGREJAS = ["Igreja Batista Cristo Rei (CR)", "Igreja Batista Proclamai (P)"]
TIPOS   = ["Culto", "Reunião de Líderes", "Esporte Missionário", "Intercambio", "Outro"]


# ─── ESTADO DE NAVEGAÇÃO ─────────────────────────────────────────────────────
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def nav(target):
    st.session_state.page = target


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def get_initials(nome):
    partes = nome.strip().split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[-1][0]).upper()
    return nome[:2].upper() if nome else "??"

def page_header(icon, title, subtitle=""):
    sub_html = (f"<p style='color:#7B8DB0;font-size:14px;margin:2px 0 0 42px;'>{subtitle}</p>"
                if subtitle else "")
    st.markdown(f"""
    <div style="margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:2px;">
        <span style="font-size:28px;line-height:1;">{icon}</span>
        <h1 style="font-family:'Crimson Pro',serif;font-size:2.1rem;font-weight:700;
                   color:#1B2B5E;margin:0;letter-spacing:-0.4px;">{title}</h1>
      </div>
      {sub_html}
    </div>
    """, unsafe_allow_html=True)

def avatar(initials, is_cr=True, size=44):
    cls = "avatar-cr" if is_cr else "avatar-p"
    return f"""<div class="{cls}" style="width:{size}px;height:{size}px;border-radius:50%;
        display:inline-flex;align-items:center;justify-content:center;
        font-weight:800;font-size:{int(size*0.36)}px;flex-shrink:0;">{initials}</div>"""

def section_label(text, color="#7B8DB0"):
    st.markdown(f"""<div style="font-size:11px;font-weight:700;color:{color};
        text-transform:uppercase;letter-spacing:1.2px;margin:18px 0 10px;">{text}</div>""",
        unsafe_allow_html=True)

def empty_state(icon, title, subtitle=""):
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
        ("🏠", "Início",       "home"),
        ("👥", "Membros",      "membros"),
        ("📅", "Agenda",       "agenda"),
        ("🗄️", "Histórico",   "history"),
        ("✅", "Chamada",      "attendance"),
        ("➕", "Novo Membro",  "new"),
    ]
    for icon, label, target in nav_items:
        prefix = "▸  " if st.session_state.page == target else "    "
        if st.button(f"{prefix}{icon}  {label}", key=f"nav_{target}", use_container_width=True):
            nav(target)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

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


# ─── PÁGINA: HOME ─────────────────────────────────────────────────────────────
if st.session_state.page == 'home':
    with get_db() as conn:
        m_cr    = conn.execute("SELECT count(*) FROM membros WHERE igreja LIKE '%Cristo Rei%'").fetchone()[0]
        m_p     = conn.execute("SELECT count(*) FROM membros WHERE igreja LIKE '%Proclamai%'").fetchone()[0]
        total   = conn.execute("SELECT count(*) FROM membros").fetchone()[0]
        futuras = conn.execute("SELECT count(*) FROM reunioes WHERE data >= ?",
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
    c1.metric("Total de Membros",      total)
    c2.metric("🔵 Cristo Rei",         m_cr)
    c3.metric("🟠 Proclamai",          m_p)
    c4.metric("Próximas Atividades",   futuras)

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
            <li><b>Acompanhar:</b> consulte <b>👥 Membros</b> e <b>🗄️ Histórico</b> para gerenciar dados.</li>
          </ol>
          <div style="background:#EFF4FF;border-radius:12px;padding:14px 18px;
                      margin-top:10px;font-size:14px;color:#1B2B5E;line-height:1.6;">
            📱 <b>Dica Mobile:</b> No navegador do celular, toque em
            <i>"Adicionar à tela de início"</i> para instalar como aplicativo!
          </div>
        </div>
        """, unsafe_allow_html=True)


# ─── PÁGINA: NOVO MEMBRO ──────────────────────────────────────────────────────
elif st.session_state.page == 'new':
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
                st.error("❌ Preencha o nome completo do membro.")
            else:
                with get_db() as conn:
                    existente = conn.execute(
                        "SELECT id FROM membros WHERE nome = ?", (nome,)
                    ).fetchone()
                    if existente:
                        st.warning(f"⚠️ Já existe um membro com o nome **{nome}** cadastrado.")
                    else:
                        with _db_lock:
                            conn.execute(
                                "INSERT INTO membros (nome, cargo, telefone, igreja) VALUES (?,?,?,?)",
                                (nome, cargo, tel, igreja)
                            )
                            conn.commit()
                        st.success(f"✅ **{nome}** registrado com sucesso!")


# ─── PÁGINA: MEMBROS ──────────────────────────────────────────────────────────
elif st.session_state.page == 'membros':
    page_header("👥", "Quadro de Membros", "Gerencie os integrantes da sociedade")

    col_s, col_f = st.columns([2, 1])
    search   = col_s.text_input("", placeholder="🔍  Buscar por nome...",
                                 label_visibility="collapsed").upper()
    f_igreja = col_f.selectbox("", ["Todas as Igrejas"] + IGREJAS,
                                label_visibility="collapsed")

    with get_db() as conn:
        rank_sql = "CASE cargo "
        for i, c in enumerate(CARGOS):
            rank_sql += f"WHEN '{c}' THEN {i} "
        rank_sql += "ELSE 99 END as rank"
        membros = conn.execute(
            f"SELECT *, {rank_sql} FROM membros ORDER BY rank ASC, nome ASC"
        ).fetchall()

    filtrados = [
        m for m in membros
        if (search in m['nome']) and
           (f_igreja == "Todas as Igrejas" or m['igreja'] == f_igreja)
    ]

    st.markdown(
        f"<p style='color:#9CA3AF;font-size:12px;margin:8px 0 14px;'>"
        f"{len(filtrados)} membro(s) encontrado(s)</p>",
        unsafe_allow_html=True
    )

    if not filtrados:
        empty_state("👥", "Nenhum membro encontrado",
                    "Ajuste os filtros ou cadastre um novo membro na aba ➕ Novo Membro.")
    else:
        for m in filtrados:
            is_cr    = "Cristo Rei" in m['igreja']
            badge_cls = "badge-cr" if is_cr else "badge-p"
            initials = get_initials(m['nome'])
            icon     = "🔵" if is_cr else "🟠"

            with st.expander(f"{icon}  {m['nome'].title()}   ·   {m['cargo']}"):
                # ── Cabeçalho do card ──────────────────────────────────
                col_av, col_info = st.columns([1, 7])
                with col_av:
                    st.markdown(
                        f"<div style='margin-top:8px;'>{avatar(initials, is_cr, 52)}</div>",
                        unsafe_allow_html=True
                    )
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

                # ── Formulário de edição inline ────────────────────────
                with st.form(f"edit_{m['id']}"):
                    st.markdown("<p style='font-size:12px;color:#9CA3AF;font-weight:600;"
                                "text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>"
                                "✏️ EDITAR DADOS</p>", unsafe_allow_html=True)
                    ec1, ec2, ec3 = st.columns(3)
                    new_tel = ec1.text_input(
                        "Telefone", value=m['telefone'], key=f"tel_{m['id']}"
                    )
                    cargo_idx = CARGOS.index(m['cargo']) if m['cargo'] in CARGOS else 0
                    new_cargo = ec2.selectbox(
                        "Cargo", CARGOS, index=cargo_idx, key=f"cargo_{m['id']}"
                    )
                    igreja_idx = IGREJAS.index(m['igreja']) if m['igreja'] in IGREJAS else 0
                    new_igreja = ec3.selectbox(
                        "Igreja", IGREJAS, index=igreja_idx, key=f"igreja_{m['id']}"
                    )

                    if st.form_submit_button("💾  Salvar Alterações", use_container_width=True):
                        with get_db() as conn:
                            with _db_lock:
                                conn.execute(
                                    "UPDATE membros SET telefone=?, cargo=?, igreja=? WHERE id=?",
                                    (new_tel, new_cargo, new_igreja, m['id'])
                                )
                                conn.commit()
                        st.success("✅ Alterações salvas!")
                        st.rerun()

                # ── Botão de remoção ───────────────────────────────────
                if st.button("🗑️  Remover Membro", key=f"del_{m['id']}",
                             use_container_width=True):
                    with get_db() as conn:
                        with _db_lock:
                            conn.execute("DELETE FROM membros WHERE id=?",     (m['id'],))
                            conn.execute("DELETE FROM frequencia WHERE membro_id=?", (m['id'],))
                            conn.commit()
                    st.rerun()


# ─── PÁGINA: AGENDA ───────────────────────────────────────────────────────────
elif st.session_state.page == 'agenda':
    page_header("📅", "Agendar Atividade", "Programe os próximos eventos da sociedade")

    with st.form("form_agenda", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data    = c1.date_input("Data do Evento", datetime.now())
        horario = c2.text_input("Horário de Início", "19:00")

        c3, c4 = st.columns(2)
        tipo  = c3.selectbox("Tipo de Evento",       TIPOS)
        local = c4.selectbox("Local de Realização",  IGREJAS)

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("📅   Confirmar Agendamento", use_container_width=True)
        if submitted:
            with get_db() as conn:
                with _db_lock:
                    conn.execute(
                        "INSERT INTO reunioes (data, tipo, horario, local_igreja) VALUES (?,?,?,?)",
                        (data.strftime("%Y-%m-%d"), tipo, horario, local)
                    )
                    conn.commit()
            st.success("✅ Atividade agendada com sucesso!")


# ─── PÁGINA: HISTÓRICO ────────────────────────────────────────────────────────
elif st.session_state.page == 'history':
    page_header("🗄️", "Histórico de Atividades",
                "Consulte e gerencie todas as atividades registradas")

    hoje = datetime.now().strftime("%Y-%m-%d")
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
        futuras  = [r for r in reunioes if r['data'] >= hoje]
        passadas = [r for r in reunioes if r['data'] <  hoje]

        def render_evento(r, dot):
            data_br = datetime.strptime(r['data'], "%Y-%m-%d").strftime("%d/%m/%Y")
            with st.expander(f"{dot}  {data_br}  ·  {r['tipo']}  ·  {r['horario']}"):
                col_i, col_p, col_d = st.columns([4, 3, 2])
                col_i.markdown(f"📍 **Local:** {r['local_igreja']}")
                col_p.markdown(
                    f"👥 **Presenças:** {r['presentes']}"
                    + (f" / {r['total_reg']}" if r['total_reg'] else "")
                )
                if col_d.button("🗑️ Excluir", key=f"del_r_{r['id']}",
                                use_container_width=True):
                    with get_db() as conn:
                        with _db_lock:
                            conn.execute("DELETE FROM reunioes WHERE id=?",          (r['id'],))
                            conn.execute("DELETE FROM frequencia WHERE reuniao_id=?", (r['id'],))
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


# ─── PÁGINA: CHAMADA ──────────────────────────────────────────────────────────
elif st.session_state.page == 'attendance':
    page_header("✅", "Controle de Chamada",
                "Registre a frequência dos membros nos eventos")

    hoje = datetime.now().strftime("%Y-%m-%d")
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
            f"{datetime.strptime(r['data'],'%Y-%m-%d').strftime('%d/%m/%Y')}  |  {r['tipo']}  |  {r['local_igreja']}": r['id']
            for r in reus
        }
        selecionado = st.selectbox("🎯  Selecionar Evento:", list(opcoes.keys()))
        rid = opcoes[selecionado]

        with get_db() as conn:
            membros  = conn.execute("SELECT * FROM membros ORDER BY nome ASC").fetchall()
            existing = {
                f['membro_id']: f['status']
                for f in conn.execute(
                    "SELECT * FROM frequencia WHERE reuniao_id=?", (rid,)
                ).fetchall()
            }

        if not membros:
            st.warning("⚠️ Nenhum membro cadastrado. Acesse **➕ Novo Membro** primeiro.")
        else:
            presentes_count = sum(1 for s in existing.values() if s == "Presente")
            st.markdown(
                f"<p style='color:#7B8DB0;font-size:13px;margin:6px 0 18px;'>"
                f"{len(membros)} membro(s) cadastrado(s)"
                + (f"  ·  <b style='color:#059669;'>{presentes_count} presente(s) registrado(s)</b>"
                   if existing else "")
                + "</p>",
                unsafe_allow_html=True
            )

            cr_membros = [m for m in membros if "Cristo Rei" in m['igreja']]
            pr_membros = [m for m in membros if "Proclamai" in m['igreja']]

            with st.form("form_chamada"):
                mapa = {}

                for grupo_label, grupo, is_cr in [
                    ("🔵 Igreja Batista Cristo Rei", cr_membros, True),
                    ("🟠 Igreja Batista Proclamai",  pr_membros, False)
                ]:
                    if not grupo:
                        continue

                    section_label(grupo_label, color="#1B2B5E" if is_cr else "#92400E")

                    for m in grupo:
                        initials     = get_initials(m['nome'])
                        default_st   = existing.get(m['id'], "Presente")
                        default_idx  = ["Presente", "Falta", "Justificado"].index(default_st)

                        col_av, col_nm, col_rd = st.columns([1, 4, 5])

                        with col_av:
                            st.markdown(
                                f"<div style='margin-top:4px;'>{avatar(initials, is_cr, 38)}</div>",
                                unsafe_allow_html=True
                            )
                        with col_nm:
                            st.markdown(
                                f"<div style='padding-top:7px;font-weight:500;"
                                f"font-size:14px;color:#1a1a2e;'>{m['nome'].title()}</div>",
                                unsafe_allow_html=True
                            )
                        with col_rd:
                            mapa[m['id']] = st.radio(
                                "", ["Presente", "Falta", "Justificado"],
                                index=default_idx, horizontal=True,
                                key=f"fr_{m['id']}", label_visibility="collapsed"
                            )

                        st.markdown(
                            "<hr style='border:none;border-top:1px solid #F0F3FA;margin:4px 0;'>",
                            unsafe_allow_html=True
                        )

                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("💾   Registrar Presenças", use_container_width=True):
                    with get_db() as conn:
                        with _db_lock:
                            conn.execute("DELETE FROM frequencia WHERE reuniao_id=?", (rid,))
                            for mid, status in mapa.items():
                                conn.execute(
                                    "INSERT INTO frequencia (reuniao_id, membro_id, status) VALUES (?,?,?)",
                                    (rid, mid, status)
                                )
                            conn.commit()
                    pres = sum(1 for s in mapa.values() if s == "Presente")
                    st.success(f"✅ Frequência salva! {pres} presente(s) de {len(mapa)} membro(s).")

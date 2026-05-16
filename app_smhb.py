import streamlit as st
import sqlite3
from datetime import datetime
import contextlib
import threading

# 1. ARQUITETURA DE SEGURANÇA MÁXIMA
_db_lock = threading.Lock()

st.set_page_config(
    page_title="SMHB | Gestão Eclesiástica",
    layout="wide",
    page_icon="⛪",
    initial_sidebar_state="collapsed"
)

# 2. FRAMEWORK VISUAL ADAPTATIVO (DESKTOP/MOBILE/TABLET)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
        }

        .stButton>button {
            width: 100%;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            background: #ffffff;
            color: #475569;
            padding: 10px 15px;
            font-weight: 600;
            transition: all 0.25s ease;
            height: 3.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }

        .stButton>button:hover {
            border-color: #2563eb;
            color: #2563eb;
            background: #f0f6ff;
            transform: translateY(-1px);
        }

        [data-testid="stMetric"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            padding: 20px !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02) !important;
        }

        .tutorial-box {
            background: linear-gradient(135deg, #eff6ff, #dbeafe);
            border-left: 6px solid #2563eb;
            padding: 20px;
            border-radius: 14px;
            margin-top: 15px;
            margin-bottom: 20px;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 99px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge-cr { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .badge-p { background: #ffedd5; color: #9a3412; border: 1px solid #fed7aa; }

        @media (max-width: 768px) {
            .stButton>button { height: 3.8rem; font-size: 15px; }
            .stRadio>div { gap: 15px !important; }
        }
    </style>
""", unsafe_allow_html=True)

# 3. GERENCIAMENTO DE TRANSAÇÕES DO BANCO DE DADOS
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
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cargo TEXT, telefone TEXT, igreja TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS reunioes 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, tipo TEXT, horario TEXT, local_igreja TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS frequencia 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, reuniao_id INTEGER, membro_id INTEGER, status TEXT)''')
            conn.commit()

init_db()

# 4. GESTÃO DE ESTADO DE NAVEGAÇÃO
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def nav(target_page):
    st.session_state.page = target_page

# --- CABEÇALHO DO SISTEMA ---
st.markdown("<h1 style='text-align: center; color: #0f172a; font-weight: 800; margin-bottom:0px;'>⛪ SMHB GESTÃO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 25px;'>Sociedade Missionária de Homens Batistas</p>", unsafe_allow_html=True)

# Barra de Menu Superior Responsiva
m_cols = st.columns(6)
menu_options = [
    ("🏠 Início", "home"), ("👥 Membros", "membros"), ("📅 Agenda", "agenda"),
    ("🗄️ Histórico", "history"), ("✅ Chamada", "attendance"), ("➕ Novo", "new")
]

for idx, (label, target) in enumerate(menu_options):
    if m_cols[idx].button(label, key=f"menu_{target}"):
        nav(target)

st.markdown("<br>", unsafe_allow_html=True)

CARGOS = ["Presidente SMHB", "Vice-Presidente SMHB", "1° Secretário SMHB", "2° Secretário SMHB", "1° Tesoureiro SMHB", "2° Tesoureiro SMHB", "Integrante SMHB"]
IGREJAS = ["Igreja Batista Cristo Rei (CR)", "Igreja Batista Proclamai (P)"]
TIPOS = ["Culto", "Reunião de Líderes", "Esporte Missionário", "Intercambio", "Outro"]

# --- LÓGICA DE EXIBIÇÃO DAS TELAS ---

if st.session_state.page == 'home':
    with get_db() as conn:
        m1 = conn.execute("SELECT count(*) FROM membros WHERE igreja LIKE '%Cristo Rei%'").fetchone()[0]
        m2 = conn.execute("SELECT count(*) FROM membros WHERE igreja LIKE '%Proclamai%'").fetchone()[0]
        r1 = conn.execute("SELECT count(*) FROM reunioes").fetchone()[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Membros Cristo Rei", m1)
    col2.metric("Membros Proclamai", m2)
    col3.metric("Atividades Registradas", r1)
    
    st.markdown("---")
    
    with st.expander("📖 TUTORIAL INTERNO DE USO RÁPIDO (Clique para abrir/fechar)", expanded=False):
        st.markdown("""
        <div class="tutorial-box">
            <h4 style='margin-top:0;'>🚀 Aprenda a usar o sistema em menos de 1 minuto:</h4>
            <ol>
                <li><b>Cadastrar Membros:</b> Vá na aba <b>➕ Novo</b>, preencha os dados e salve.</li>
                <li><b>Criar Eventos:</b> Vá em <b>📅 Agenda</b> para programar o próximo culto ou reunião.</li>
                <li><b>Fazer a Chamada:</b> No dia do evento, clique em <b>✅ Chamada</b>, selecione a atividade e registre a presença.</li>
                <li><b>Acompanhamento:</b> Use as abas <b>👥 Membros</b> e <b>🗄️ Histórico</b> para gerenciar informações.</li>
            </ol>
            <i>📱 <b>Dica Mobile:</b> No navegador do celular, clique em "Adicionar à tela de início" para transformá-lo em App!</i>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.page == 'new':
    st.subheader("👤 Cadastro de Integrante")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo:").strip().upper()
        c1, c2 = st.columns(2)
        tel = c1.text_input("Telefone de Contato:", value="+55 (92) ")
        cargo = c2.selectbox("Cargo:", CARGOS)
        igreja = st.selectbox("Igreja:", IGREJAS)
        
        if st.form_submit_button("💾 Salvar Registro"):
            if nome:
                with get_db() as conn:
                    with _db_lock:
                        conn.execute("INSERT INTO membros (nome, cargo, telefone, igreja) VALUES (?,?,?,?)", (nome, cargo, tel, igreja))
                        conn.commit()
                st.success(f"Membro {nome} registrado com sucesso!")
            else: st.error("O preenchimento do nome é obrigatório.")

elif st.session_state.page == 'membros':
    st.subheader("👥 Quadro Geral de Membros")
    col_f1, col_f2 = st.columns([2, 1])
    search = col_f1.text_input("🔍 Filtrar por Nome:").upper()
    f_igreja = col_f2.selectbox("⛪ Filtrar por Igreja:", ["Todas"] + IGREJAS)
    
    with get_db() as conn:
        h_sql = "CASE cargo "
        for i, c in enumerate(CARGOS): h_sql += f"WHEN '{c}' THEN {i} "
        h_sql += "ELSE 99 END as rank"
        membros = conn.execute(f"SELECT *, {h_sql} FROM membros ORDER BY rank ASC, nome ASC").fetchall()
    
    filtrados = [m for m in membros if (search in m['nome']) and (f_igreja == "Todas" or m['igreja'] == f_igreja)]
    
    if not filtrados:
        st.info("Nenhum membro corresponde aos filtros.")
    else:
        for m in filtrados:
            cor_tag = "badge-cr" if "Cristo Rei" in m['igreja'] else "badge-p"
            marcador = "🔵" if "Cristo Rei" in m['igreja'] else "🟠"
            with st.expander(f"{marcador} {m['nome']} — {m['cargo']}"):
                col_i, col_d = st.columns([3, 1])
                with col_i:
                    st.markdown(f"<span class='badge {cor_tag}'>{m['igreja']}</span>", unsafe_allow_html=True)
                    st.write(f"**Contato:** {m['telefone']}")
                with col_d:
                    if st.button("Remover Membro", key=f"del_m_{m['id']}"):
                        with get_db() as conn:
                            with _db_lock:
                                conn.execute("DELETE FROM membros WHERE id=?", (m['id'],))
                                conn.execute("DELETE FROM frequencia WHERE membro_id=?", (m['id'],))
                                conn.commit()
                        st.rerun()

elif st.session_state.page == 'agenda':
    st.subheader("📅 Agendamento de Atividade")
    with st.form("form_agenda", clear_on_submit=True):
        data = st.date_input("Data do Evento:", datetime.now())
        horario = st.text_input("Horário de Início:", "19:00")
        tipo = st.selectbox("Tipo de Evento:", TIPOS)
        local = st.selectbox("Local de Realização:", IGREJAS)
        
        if st.form_submit_button("💾 Confirmar Agendamento"):
            with get_db() as conn:
                with _db_lock:
                    conn.execute("INSERT INTO reunioes (data, tipo, horario, local_igreja) VALUES (?,?,?,?)", 
                                 (data.strftime("%Y-%m-%d"), tipo, horario, local))
                    conn.commit()
            st.success("Atividade agendada com sucesso!")

elif st.session_state.page == 'history':
    st.subheader("🗄️ Histórico de Atividades")
    hoje = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        reunioes = conn.execute("""
            SELECT * FROM reunioes 
            ORDER BY CASE WHEN data >= ? THEN 0 ELSE 1 END ASC,
                     CASE WHEN data >= ? THEN data END ASC,
                     data DESC
        """, (hoje, hoje)).fetchall()
    
    if not reunioes:
        st.info("Nenhuma atividade registrada.")
    else:
        for r in reunioes:
            is_futuro = r['data'] >= hoje
            status_cor = "🟢" if is_futuro else "⚪"
            data_br = datetime.strptime(r['data'], "%Y-%m-%d").strftime("%d/%m/%Y")
            with st.expander(f"{status_cor} {data_br} — {r['tipo']} ({r['horario']})"):
                st.write(f"**Local:** {r['local_igreja']}")
                if st.button("Excluir Evento", key=f"del_r_{r['id']}"):
                    with get_db() as conn:
                        with _db_lock:
                            conn.execute("DELETE FROM reunioes WHERE id=?", (r['id'],))
                            conn.execute("DELETE FROM frequencia WHERE reuniao_id=?", (r['id'],))
                            conn.commit()
                    st.rerun()

elif st.session_state.page == 'attendance':
    st.subheader("✅ Controle de Frequência")
    hoje = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        reus = conn.execute("SELECT * FROM reunioes ORDER BY CASE WHEN data >= ? THEN 0 ELSE 1 END ASC, data ASC", (hoje,)).fetchall()
    
    if not reus:
        st.warning("Crie um evento na aba Agenda primeiro.")
    else:
        opcoes_chamada = {f"{datetime.strptime(r['data'], '%Y-%m-%d').strftime('%d/%m/%Y')} | {r['tipo']}": r['id'] for r in reus}
        selecionado = st.selectbox("Selecione o Evento:", list(opcoes_chamada.keys()))
        rid = opcoes_chamada[selecionado]
        
        with get_db() as conn:
            membros_chamada = conn.execute("SELECT * FROM membros ORDER BY nome ASC").fetchall()
        
        with st.form("form_chamada"):
            mapa_presenca = {}
            for m in membros_chamada:
                st.markdown(f"**{m['nome']}**")
                mapa_presenca[m['id']] = st.radio(f"Status_{m['id']}", ["Presente", "Falta", "Justificado"], 
                                           horizontal=True, key=f"freg_{m['id']}", label_visibility="collapsed")
                st.markdown("---")
            
            if st.form_submit_button("💾 Registrar Presenças"):
                with get_db() as conn:
                    with _db_lock:
                        conn.execute("DELETE FROM frequencia WHERE reuniao_id=?", (rid,))
                        for mid, status in mapa_presenca.items():
                            conn.execute("INSERT INTO frequencia (reuniao_id, membro_id, status) VALUES (?,?,?)", (rid, mid, status))
                        conn.commit()
                st.success("Dados de presença salvos!")

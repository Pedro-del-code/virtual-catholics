import streamlit as st
from groq import Groq
import json
import os
import base64
import hashlib
from datetime import datetime

st.set_page_config(
    page_title="Virtual Catholics",
    page_icon="https://i.imgur.com/ilafAhJ.png",
    layout="wide"
)

def get_logo_base64():
    logo_path = os.path.join(os.path.dirname(__file__), "logo.jpeg")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_base64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;"/>' if logo_b64 else '<img src="https://i.imgur.com/ilafAhJ.png" style="width:40px;height:40px;border-radius:50%;object-fit:cover;"/>'

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background-color: #212121; color: #ececec; }
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] {
    background-color: #171717;
    border-right: 1px solid #2e2e2e;
    width: 270px !important;
}
section[data-testid="stSidebar"] .block-container { padding: 1.2rem 0.8rem; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.chat-wrapper { max-width: 700px; margin: 0 auto; padding: 2rem 1rem 10rem 1rem; }
.msg-user { display: flex; justify-content: flex-end; margin: 1rem 0; }
.bubble-user {
    background-color: #2f2f2f; color: #ececec;
    padding: 0.8rem 1.2rem; border-radius: 18px 18px 4px 18px;
    max-width: 80%; font-size: 0.95rem; line-height: 1.6;
}
.msg-bot { display: flex; justify-content: flex-start; gap: 0.8rem; margin: 1rem 0; align-items: flex-start; }
.bubble-bot { color: #ececec; font-size: 0.95rem; line-height: 1.7; max-width: 85%; }
.sidebar-header { display: flex; align-items: center; gap: 0.7rem; padding-bottom: 1.2rem; border-bottom: 1px solid #2e2e2e; margin-bottom: 1rem; }
.sidebar-title { color: #ececec; font-size: 0.95rem; font-weight: 600; }
.sidebar-subtitle { color: #c8a96e; font-size: 0.7rem; }
.section-label { color: #555; font-size: 0.7rem; font-weight: 600; letter-spacing: 1px; padding: 0.5rem 0.3rem 0.3rem 0.3rem; text-transform: uppercase; }
.welcome { text-align: center; padding: 4rem 0 2rem 0; }
.welcome h2 { color: #ececec; font-size: 1.8rem; font-weight: 600; margin-bottom: 0.5rem; }
.welcome p { color: #888; font-size: 0.95rem; }
.auth-wrapper { max-width: 400px; margin: 4rem auto; text-align: center; }
.auth-wrapper h2 { color: #ececec; margin-bottom: 0.3rem; }
.auth-wrapper p { color: #888; font-size: 0.9rem; margin-bottom: 1.5rem; }
.error-msg { color: #ff6b6b; font-size: 0.85rem; text-align: center; margin-top: 0.5rem; }
.success-msg { color: #6bff9e; font-size: 0.85rem; text-align: center; margin-top: 0.5rem; }
.stTextInput > div > div > input {
    background: #2f2f2f !important; border: 1px solid #3e3e3e !important;
    border-radius: 12px !important; color: #ececec !important;
    font-size: 0.95rem !important; padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input:focus { border-color: #555 !important; box-shadow: none !important; }
.stTextInput > div > div > input::placeholder { color: #666 !important; }
.stButton > button {
    background: #2f2f2f !important; border: 1px solid #3e3e3e !important;
    color: #ececec !important; border-radius: 12px !important;
    padding: 0.6rem 1rem !important; font-size: 0.9rem !important;
    width: 100% !important; transition: background 0.2s !important;
}
.stButton > button:hover { background: #3e3e3e !important; }
</style>
""", unsafe_allow_html=True)

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
USUARIOS_ARQUIVO = "usuarios.json"

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_usuarios():
    if os.path.exists(USUARIOS_ARQUIVO):
        with open(USUARIOS_ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_usuarios(usuarios):
    with open(USUARIOS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)

def arquivo_usuario(username, tipo):
    return f"user_{username}_{tipo}.json"

def carregar_memoria(username):
    arq = arquivo_usuario(username, "memoria")
    if os.path.exists(arq):
        with open(arq, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"nome": username, "fatos": []}

def salvar_memoria(username, memoria):
    with open(arquivo_usuario(username, "memoria"), "w", encoding="utf-8") as f:
        json.dump(memoria, f, ensure_ascii=False, indent=2)

def carregar_chats(username):
    arq = arquivo_usuario(username, "chats")
    if os.path.exists(arq):
        with open(arq, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_chats(username, chats):
    with open(arquivo_usuario(username, "chats"), "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)

def novo_chat_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

# ── Session state ─────────────────────────────────────────────────────────────
if "logado" not in st.session_state:
    st.session_state.logado = False
if "username" not in st.session_state:
    st.session_state.username = None
if "tela" not in st.session_state:
    st.session_state.tela = "login"
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = None
if "cliente" not in st.session_state:
    st.session_state.cliente = Groq(api_key=API_KEY)
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "pendente" not in st.session_state:
    st.session_state.pendente = None

# ── Tela de login/cadastro ────────────────────────────────────────────────────
if not st.session_state.logado:
    st.markdown(f"""
    <div class="auth-wrapper">
        <div style="margin-bottom:1rem;">{logo_html}</div>
        <h2>Virtual Catholics</h2>
        <p>✝️ Assistente Católico</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba = st.radio("", ["Entrar", "Criar conta"], horizontal=True, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)

        if aba == "Entrar":
            usuario_input = st.text_input("", placeholder="Usuário", key="login_user", label_visibility="collapsed")
            senha_input = st.text_input("", placeholder="Senha", type="password", key="login_senha", label_visibility="collapsed")
            if st.button("Entrar →"):
                usuarios = carregar_usuarios()
                if usuario_input in usuarios and usuarios[usuario_input] == hash_senha(senha_input):
                    st.session_state.logado = True
                    st.session_state.username = usuario_input
                    st.session_state.chats = carregar_chats(usuario_input)
                    st.rerun()
                else:
                    st.markdown('<p class="error-msg">Usuário ou senha incorretos!</p>', unsafe_allow_html=True)

        else:
            nome_novo = st.text_input("", placeholder="Seu nome", key="reg_nome", label_visibility="collapsed")
            usuario_novo = st.text_input("", placeholder="Escolha um usuário", key="reg_user", label_visibility="collapsed")
            senha_nova = st.text_input("", placeholder="Escolha uma senha", type="password", key="reg_senha", label_visibility="collapsed")
            if st.button("Criar conta →"):
                if nome_novo.strip() and usuario_novo.strip() and senha_nova.strip():
                    usuarios = carregar_usuarios()
                    if usuario_novo in usuarios:
                        st.markdown('<p class="error-msg">Usuário já existe!</p>', unsafe_allow_html=True)
                    else:
                        usuarios[usuario_novo] = hash_senha(senha_nova)
                        salvar_usuarios(usuarios)
                        memoria = {"nome": nome_novo.strip(), "fatos": []}
                        salvar_memoria(usuario_novo, memoria)
                        st.session_state.logado = True
                        st.session_state.username = usuario_novo
                        st.session_state.chats = {}
                        st.rerun()
                else:
                    st.markdown('<p class="error-msg">Preencha todos os campos!</p>', unsafe_allow_html=True)

else:
    username = st.session_state.username
    memoria = carregar_memoria(username)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-header">
            {logo_html}
            <div>
                <div class="sidebar-title">Virtual Catholics</div>
                <div class="sidebar-subtitle">✝️ {memoria['nome']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✏️  Novo chat"):
            chat_id = novo_chat_id()
            st.session_state.chats[chat_id] = {"titulo": "Nova conversa", "historico": []}
            salvar_chats(username, st.session_state.chats)
            st.session_state.chat_atual = chat_id
            st.session_state.input_key += 1
            st.rerun()

        st.markdown('<div class="section-label">Conversas</div>', unsafe_allow_html=True)

        for chat_id in sorted(st.session_state.chats.keys(), reverse=True):
            titulo = st.session_state.chats[chat_id]["titulo"]
            if st.button(f"💬  {titulo}", key=f"chat_{chat_id}"):
                st.session_state.chat_atual = chat_id
                st.session_state.input_key += 1
                st.rerun()

        if st.session_state.chat_atual and st.session_state.chat_atual in st.session_state.chats:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️  Deletar conversa"):
                del st.session_state.chats[st.session_state.chat_atual]
                salvar_chats(username, st.session_state.chats)
                st.session_state.chat_atual = None
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪  Sair"):
            st.session_state.logado = False
            st.session_state.username = None
            st.session_state.chats = {}
            st.session_state.chat_atual = None
            st.rerun()

    # ── System prompt ─────────────────────────────────────────────────────────
    fatos_str = "\n".join(memoria["fatos"]) if memoria["fatos"] else "Nenhum ainda."
    system_prompt = f"""Você é o Virtual Catholics, uma IA católica criada por Pedro.
Você tem fé católica profunda e responde sempre com base nos ensinamentos da Igreja Católica.
Você é engraçado, divertido e acolhedor, mas sempre fiel à fé.
Responda sempre em português brasileiro.
O nome do usuário é: {memoria['nome']}.
Fatos que você já sabe sobre ele:
{fatos_str}

Quando o usuário revelar algo importante sobre si (hobby, profissão, preferência, etc),
inclua no final da sua resposta uma linha assim:
[LEMBRAR: fato importante aqui]
"""

    if not st.session_state.chat_atual or st.session_state.chat_atual not in st.session_state.chats:
        st.markdown(f"""
        <div class="chat-wrapper">
            <div class="welcome">
                <div style="margin-bottom:1rem;">{logo_html}</div>
                <h2>Olá, {memoria['nome']}! 🙏</h2>
                <p>Clique em <b>Novo chat</b> para começar.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        chat_id = st.session_state.chat_atual
        historico = st.session_state.chats[chat_id]["historico"]

        if st.session_state.pendente:
            st.session_state.pendente = None
            resposta = st.session_state.cliente.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}, *historico]
            )
            mensagem = resposta.choices[0].message.content
            if "[LEMBRAR:" in mensagem:
                for linha in mensagem.split("\n"):
                    if "[LEMBRAR:" in linha:
                        fato = linha.replace("[LEMBRAR:", "").replace("]", "").strip()
                        if fato not in memoria["fatos"]:
                            memoria["fatos"].append(fato)
                            salvar_memoria(username, memoria)
                mensagem = "\n".join([l for l in mensagem.split("\n") if "[LEMBRAR:" not in l])
            historico.append({"role": "assistant", "content": mensagem})
            if len(historico) == 2:
                primeira = historico[0]["content"]
                titulo = primeira[:35] + "..." if len(primeira) > 35 else primeira
                st.session_state.chats[chat_id]["titulo"] = titulo
            salvar_chats(username, st.session_state.chats)
            st.rerun()

        chat_html = '<div class="chat-wrapper">'
        if not historico:
            chat_html += '<div class="welcome"><h2>Nova conversa 🙏</h2><p>Como posso te ajudar?</p></div>'
        else:
            for msg in historico:
                if msg["role"] == "user":
                    chat_html += f'<div class="msg-user"><div class="bubble-user">{msg["content"]}</div></div>'
                else:
                    chat_html += f'<div class="msg-bot"><div style="flex-shrink:0;margin-top:2px;">{logo_html}</div><div class="bubble-bot">{msg["content"]}</div></div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

        col1, col2 = st.columns([10, 1])
        with col1:
            user_input = st.text_input("", placeholder="Manda uma mensagem...", key=f"input_{st.session_state.input_key}", label_visibility="collapsed")
        with col2:
            enviar = st.button("➤")

        if (enviar or user_input) and user_input.strip():
            historico.append({"role": "user", "content": user_input.strip()})
            st.session_state.chats[chat_id]["historico"] = historico
            salvar_chats(username, st.session_state.chats)
            st.session_state.pendente = user_input.strip()
            st.session_state.input_key += 1
            st.rerun()

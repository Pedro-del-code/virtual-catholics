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
    layout="centered"
)

def get_logo_base64():
    logo_path = os.path.join(os.path.dirname(__file__), "logo.jpeg")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_base64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;"/>' if logo_b64 else '<img src="https://i.imgur.com/ilafAhJ.png" style="width:36px;height:36px;border-radius:50%;object-fit:cover;"/>'

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background-color: #212121; color: #ececec; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1rem 1rem 160px 1rem !important; max-width: 700px !important; }

.msg-user { display: flex; justify-content: flex-end; margin: 0.8rem 0; }
.bubble-user {
    background-color: #2f2f2f; color: #ececec;
    padding: 0.75rem 1rem; border-radius: 18px 18px 4px 18px;
    max-width: 85%; font-size: 0.95rem; line-height: 1.6; word-break: break-word;
}
.msg-bot { display: flex; justify-content: flex-start; gap: 0.6rem; margin: 0.8rem 0; align-items: flex-start; }
.bubble-bot { color: #ececec; font-size: 0.95rem; line-height: 1.7; max-width: 85%; word-break: break-word; }

.welcome { text-align: center; padding: 3rem 1rem 2rem 1rem; }
.welcome h2 { color: #ececec; font-size: 1.6rem; font-weight: 600; margin-bottom: 0.5rem; }
.welcome p { color: #888; font-size: 0.9rem; }

.auth-wrapper { max-width: 360px; margin: 4rem auto; padding: 0 1rem; text-align: center; }
.auth-wrapper h2 { color: #ececec; margin-bottom: 0.3rem; font-size: 1.4rem; }
.auth-wrapper p { color: #888; font-size: 0.85rem; margin-bottom: 1.5rem; }
.error-msg { color: #ff6b6b; font-size: 0.85rem; margin-top: 0.5rem; }

.stTextInput > div > div > input {
    background: #2f2f2f !important; border: 1px solid #3e3e3e !important;
    border-radius: 12px !important; color: #ececec !important;
    font-size: 1rem !important; padding: 0.8rem 1rem !important;
}
.stTextInput > div > div > input:focus { border-color: #555 !important; box-shadow: none !important; }
.stTextInput > div > div > input::placeholder { color: #666 !important; }

.stButton > button {
    background: #2f2f2f !important; border: 1px solid #3e3e3e !important;
    color: #ececec !important; border-radius: 12px !important;
    padding: 0.75rem 1rem !important; font-size: 0.95rem !important;
    width: 100% !important; min-height: 48px !important;
    transition: background 0.2s !important;
}
.stButton > button:hover { background: #3e3e3e !important; }

/* Barra fixa de input no fundo */
.input-bar {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: #212121;
    border-top: 1px solid #2e2e2e;
    padding: 0.8rem 1rem;
    z-index: 999;
    display: flex;
    gap: 0.5rem;
    align-items: center;
}
.input-bar input {
    flex: 1;
    background: #2f2f2f;
    border: 1px solid #3e3e3e;
    border-radius: 24px;
    color: #ececec;
    font-size: 1rem;
    padding: 0.75rem 1.2rem;
    outline: none;
    font-family: 'Inter', sans-serif;
}
.input-bar input::placeholder { color: #666; }
.send-btn {
    background: #3e3e3e;
    border: none;
    border-radius: 50%;
    width: 44px; height: 44px;
    color: #ececec;
    font-size: 1.1rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.streamlit-expanderHeader {
    background: #2f2f2f !important;
    border-radius: 12px !important;
    color: #ececec !important;
    border: 1px solid #3e3e3e !important;
    min-height: 48px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Config ─────────────────────────────────────────────────────────────────
API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
USUARIOS_ARQUIVO = "usuarios.json"

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_usuarios():
    if os.path.exists(USUARIOS_ARQUIVO):
        with open(USUARIOS_ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_usuarios(u):
    with open(USUARIOS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(u, f, ensure_ascii=False, indent=2)

def carregar_memoria(username):
    arq = f"user_{username}_memoria.json"
    if os.path.exists(arq):
        with open(arq, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"nome": username, "fatos": []}

def salvar_memoria(username, memoria):
    with open(f"user_{username}_memoria.json", "w", encoding="utf-8") as f:
        json.dump(memoria, f, ensure_ascii=False, indent=2)

def carregar_chats(username):
    arq = f"user_{username}_chats.json"
    if os.path.exists(arq):
        with open(arq, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_chats(username, chats):
    with open(f"user_{username}_chats.json", "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)

def novo_chat_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

for key, val in [("logado", False), ("username", None), ("chats", {}),
                  ("chat_atual", None), ("input_key", 0), ("pendente", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

if "cliente" not in st.session_state:
    st.session_state.cliente = Groq(api_key=API_KEY)

# ── Login ──────────────────────────────────────────────────────────────────
if not st.session_state.logado:
    st.markdown(f"""
    <div class="auth-wrapper">
        <div style="margin-bottom:1rem;">{logo_html}</div>
        <h2>Virtual Catholics</h2>
        <p>✝️ Assistente Católico</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        aba = st.radio("", ["Entrar", "Criar conta"], horizontal=True, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)

        if aba == "Entrar":
            u = st.text_input("", placeholder="Usuário", key="lu", label_visibility="collapsed")
            s = st.text_input("", placeholder="Senha", type="password", key="ls", label_visibility="collapsed")
            if st.button("Entrar →"):
                usuarios = carregar_usuarios()
                if u in usuarios and usuarios[u] == hash_senha(s):
                    st.session_state.logado = True
                    st.session_state.username = u
                    st.session_state.chats = carregar_chats(u)
                    st.rerun()
                else:
                    st.markdown('<p class="error-msg">Usuário ou senha incorretos!</p>', unsafe_allow_html=True)
        else:
            nome_n = st.text_input("", placeholder="Seu nome", key="rn", label_visibility="collapsed")
            user_n = st.text_input("", placeholder="Escolha um usuário", key="ru", label_visibility="collapsed")
            senha_n = st.text_input("", placeholder="Escolha uma senha", type="password", key="rs", label_visibility="collapsed")
            if st.button("Criar conta →"):
                if nome_n.strip() and user_n.strip() and senha_n.strip():
                    usuarios = carregar_usuarios()
                    if user_n in usuarios:
                        st.markdown('<p class="error-msg">Usuário já existe!</p>', unsafe_allow_html=True)
                    else:
                        usuarios[user_n] = hash_senha(senha_n)
                        salvar_usuarios(usuarios)
                        salvar_memoria(user_n, {"nome": nome_n.strip(), "fatos": []})
                        st.session_state.logado = True
                        st.session_state.username = user_n
                        st.session_state.chats = {}
                        st.rerun()
                else:
                    st.markdown('<p class="error-msg">Preencha todos os campos!</p>', unsafe_allow_html=True)

else:
    username = st.session_state.username
    memoria = carregar_memoria(username)

    fatos_str = "\n".join(memoria["fatos"]) if memoria["fatos"] else "Nenhum ainda."
    system_prompt = f"""Você é o Virtual Catholics, uma IA católica criada por Pedro.
Você tem fé católica profunda e responde com base nos ensinamentos da Igreja Católica.
Você é engraçado, divertido e acolhedor, mas sempre fiel à fé.
Responda sempre em português brasileiro.
O nome do usuário é: {memoria['nome']}.
Fatos que você já sabe sobre ele: {fatos_str}
Quando o usuário revelar algo importante, inclua: [LEMBRAR: fato aqui]
"""

    # Menu conversas
    with st.expander(f"💬 Conversas — {memoria['nome']}"):
        if st.button("✏️ Novo chat"):
            chat_id = novo_chat_id()
            st.session_state.chats[chat_id] = {"titulo": "Nova conversa", "historico": []}
            salvar_chats(username, st.session_state.chats)
            st.session_state.chat_atual = chat_id
            st.session_state.input_key += 1
            st.rerun()

        for chat_id in sorted(st.session_state.chats.keys(), reverse=True):
            titulo = st.session_state.chats[chat_id]["titulo"]
            if st.button(f"💬 {titulo}", key=f"c_{chat_id}"):
                st.session_state.chat_atual = chat_id
                st.session_state.input_key += 1
                st.rerun()

        if st.session_state.chat_atual and st.session_state.chat_atual in st.session_state.chats:
            if st.button("🗑️ Deletar conversa"):
                del st.session_state.chats[st.session_state.chat_atual]
                salvar_chats(username, st.session_state.chats)
                st.session_state.chat_atual = None
                st.rerun()

        if st.button("🚪 Sair"):
            for k in ["logado", "username", "chats", "chat_atual"]:
                st.session_state[k] = False if k == "logado" else None if k != "chats" else {}
            st.rerun()

    # Chat
    if not st.session_state.chat_atual or st.session_state.chat_atual not in st.session_state.chats:
        st.markdown(f"""
        <div class="welcome">
            <div style="margin-bottom:1rem;">{logo_html}</div>
            <h2>Olá, {memoria['nome']}! 🙏</h2>
            <p>Abra <b>Conversas</b> e clique em <b>Novo chat</b>.</p>
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
                st.session_state.chats[chat_id]["titulo"] = primeira[:35] + ("..." if len(primeira) > 35 else "")
            salvar_chats(username, st.session_state.chats)
            st.rerun()

        chat_html = ""
        if not historico:
            chat_html = '<div class="welcome"><h2>Nova conversa 🙏</h2><p>Como posso te ajudar?</p></div>'
        else:
            for msg in historico:
                if msg["role"] == "user":
                    chat_html += f'<div class="msg-user"><div class="bubble-user">{msg["content"]}</div></div>'
                else:
                    chat_html += f'<div class="msg-bot"><div style="flex-shrink:0;margin-top:2px;">{logo_html}</div><div class="bubble-bot">{msg["content"]}</div></div>'
        st.markdown(chat_html, unsafe_allow_html=True)

    # Input
    col1, col2 = st.columns([9, 1])
    with col1:
        user_input = st.text_input("", placeholder="Manda uma mensagem...", key=f"inp_{st.session_state.input_key}", label_visibility="collapsed")
    with col2:
        enviar = st.button("➤")

    if (enviar or user_input) and user_input.strip():
        if st.session_state.chat_atual and st.session_state.chat_atual in st.session_state.chats:
            historico = st.session_state.chats[st.session_state.chat_atual]["historico"]
            historico.append({"role": "user", "content": user_input.strip()})
            st.session_state.chats[st.session_state.chat_atual]["historico"] = historico
            salvar_chats(username, st.session_state.chats)
            st.session_state.pendente = user_input.strip()
            st.session_state.input_key += 1
            st.rerun()

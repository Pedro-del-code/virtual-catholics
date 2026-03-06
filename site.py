import streamlit as st
from groq import Groq
import json
import os
import base64
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
.sidebar-title { color: #ececec; font-size: 0.95rem; font-weight: 600; line-height: 1.2; }
.sidebar-subtitle { color: #c8a96e; font-size: 0.7rem; }
.section-label { color: #555; font-size: 0.7rem; font-weight: 600; letter-spacing: 1px; padding: 0.5rem 0.3rem 0.3rem 0.3rem; text-transform: uppercase; }
.welcome { text-align: center; padding: 4rem 0 2rem 0; }
.welcome h2 { color: #ececec; font-size: 1.8rem; font-weight: 600; margin-bottom: 0.5rem; }
.welcome p { color: #888; font-size: 0.95rem; }
.nome-wrapper { max-width: 400px; margin: 6rem auto; text-align: center; }
.nome-wrapper h2 { color: #ececec; margin-bottom: 0.5rem; }
.nome-wrapper p { color: #888; font-size: 0.9rem; margin-bottom: 2rem; }
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
    width: 100% !important; transition: background 0.2s !important; text-align: left !important;
}
.stButton > button:hover { background: #3e3e3e !important; }
</style>
""", unsafe_allow_html=True)

# Config
API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
MEMORIA_ARQUIVO = "memoria.json"
CHATS_ARQUIVO = "chats.json"

def carregar_memoria():
    if os.path.exists(MEMORIA_ARQUIVO):
        with open(MEMORIA_ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"nome": None, "fatos": []}

def salvar_memoria(memoria):
    with open(MEMORIA_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(memoria, f, ensure_ascii=False, indent=2)

def carregar_chats():
    if os.path.exists(CHATS_ARQUIVO):
        with open(CHATS_ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_chats(chats):
    with open(CHATS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)

def novo_chat_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

if "memoria" not in st.session_state:
    st.session_state.memoria = carregar_memoria()
if "chats" not in st.session_state:
    st.session_state.chats = carregar_chats()
if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = None
if "cliente" not in st.session_state:
    st.session_state.cliente = Groq(api_key=API_KEY)
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "pendente" not in st.session_state:
    st.session_state.pendente = None

memoria = st.session_state.memoria

if not memoria["nome"]:
    st.markdown(f"""
    <div class="nome-wrapper">
        <div style="margin-bottom:1rem;">{logo_html}</div>
        <h2>Bem-vindo! 🙏</h2>
        <p>Qual é o seu nome?</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        nome = st.text_input("", placeholder="Digite seu nome...", label_visibility="collapsed")
        if st.button("Entrar →") and nome.strip():
            memoria["nome"] = nome.strip()
            salvar_memoria(memoria)
            st.rerun()
else:
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-header">
            {logo_html}
            <div>
                <div class="sidebar-title">Virtual Catholics</div>
                <div class="sidebar-subtitle">✝️ Assistente Católico</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✏️  Novo chat"):
            chat_id = novo_chat_id()
            st.session_state.chats[chat_id] = {"titulo": "Nova conversa", "historico": []}
            salvar_chats(st.session_state.chats)
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
                salvar_chats(st.session_state.chats)
                st.session_state.chat_atual = None
                st.rerun()

    fatos_str = "\n".join(memoria["fatos"]) if memoria["fatos"] else "Nenhum ainda."
    system_prompt = f"""Você é o Virtual Catholics, uma IA católica criada por Pedro.
Você tem fé católica profunda e responde sempre com base nos ensinamentos da Igreja Católica.
Você é engraçado, divertido e acolhedor, mas sempre fiel à fé.
Responda sempre em português brasileiro.
O nome do seu criador e usuário é: {memoria['nome']}.
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
                            salvar_memoria(memoria)
                mensagem = "\n".join([l for l in mensagem.split("\n") if "[LEMBRAR:" not in l])
            historico.append({"role": "assistant", "content": mensagem})
            if len(historico) == 2:
                primeira = historico[0]["content"]
                titulo = primeira[:35] + "..." if len(primeira) > 35 else primeira
                st.session_state.chats[chat_id]["titulo"] = titulo
            salvar_chats(st.session_state.chats)
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
            salvar_chats(st.session_state.chats)
            st.session_state.pendente = user_input.strip()
            st.session_state.input_key += 1
            st.rerun()

import streamlit as st
from groq import Groq
import json
import os
import hashlib
from datetime import datetime
import requests

st.set_page_config(
    page_title="Virtual Catholics",
    page_icon="https://i.imgur.com/ilafAhJ.png",
    layout="centered"
)

LOGO = "https://i.imgur.com/ilafAhJ.png"
NOSSA_SENHORA = "https://i.imgur.com/8OWNsBk.png"
SAGRADA_FAMILIA = "https://i.imgur.com/yZngD9v.png"
logo_html = f'<img src="{LOGO}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;"/>'

SUPABASE_URL = "https://aqvqjdljhtzyxocwtrmg.supabase.co"
SUPABASE_KEY = "sb_publishable_-3y6uD4Q_DtayUz0naWfCA_c3dFAofy"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

def sb_get(table, filters=""):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?{filters}", headers=HEADERS)
    return r.json()

def sb_post(table, data):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers={**HEADERS, "Prefer": "return=representation"}, json=data)
    return r.json()

def sb_patch(table, filters, data):
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{table}?{filters}", headers={**HEADERS, "Prefer": "return=representation"}, json=data)
    return r.json()

def hash_senha(s): return hashlib.sha256(s.encode()).hexdigest()

def carregar_usuario(username):
    r = sb_get("usuarios", f"username=eq.{username}&select=*")
    return r[0] if r and isinstance(r, list) and len(r) > 0 else None

def criar_usuario(username, nome, senha):
    return sb_post("usuarios", {"username": username, "nome": nome, "senha_hash": hash_senha(senha)})

def carregar_memoria(username):
    r = sb_get("memoria", f"username=eq.{username}&select=*")
    if r and isinstance(r, list) and len(r) > 0:
        return r[0]
    sb_post("memoria", {"username": username, "fatos": []})
    return {"username": username, "fatos": []}

def salvar_memoria(username, fatos):
    r = sb_get("memoria", f"username=eq.{username}&select=id")
    if r and isinstance(r, list) and len(r) > 0:
        sb_patch("memoria", f"username=eq.{username}", {"fatos": fatos})
    else:
        sb_post("memoria", {"username": username, "fatos": fatos})

def carregar_chats(username):
    r = sb_get("chats", f"username=eq.{username}&select=*&order=chat_id.desc")
    if not r or not isinstance(r, list): return {}
    return {c["chat_id"]: {"titulo": c["titulo"], "historico": c["historico"]} for c in r}

def salvar_chat(username, chat_id, titulo, historico):
    r = sb_get("chats", f"username=eq.{username}&chat_id=eq.{chat_id}&select=id")
    if r and isinstance(r, list) and len(r) > 0:
        sb_patch("chats", f"username=eq.{username}&chat_id=eq.{chat_id}", {"titulo": titulo, "historico": historico})
    else:
        sb_post("chats", {"username": username, "chat_id": chat_id, "titulo": titulo, "historico": historico})

def deletar_chat(username, chat_id):
    requests.delete(f"{SUPABASE_URL}/rest/v1/chats?username=eq.{username}&chat_id=eq.{chat_id}", headers=HEADERS)

def novo_chat_id(): return datetime.now().strftime("%Y%m%d%H%M%S")

ORACOES = {
    "Pai Nosso": "Pai nosso que estais no ceu,\nsantificado seja o vosso nome,\nvenha a nos o vosso reino,\nseja feita a vossa vontade,\nassim na terra como no ceu.\nO pao nosso de cada dia nos dai hoje,\nperdoai as nossas ofensas,\nassim como nos perdoamos\na quem nos tem ofendido,\ne nao nos deixeis cair em tentacao,\nmas livrai-nos do mal.\nAmem.",
    "Ave Maria": "Ave Maria, cheia de graca,\no Senhor e convosco,\nbendita sois vos entre as mulheres,\ne bendito e o fruto do vosso ventre, Jesus.\nSanta Maria, Mae de Deus,\nrogai por nos pecadores,\nagora e na hora de nossa morte.\nAmem.",
    "Gloria ao Pai": "Gloria ao Pai,\nao Filho\ne ao Espirito Santo.\nComo era no principio,\nagora e sempre,\npelos seculos dos seculos.\nAmem.",
    "Creio em Deus Pai": "Creio em Deus Pai todo-poderoso,\ncriador do ceu e da terra;\ne em Jesus Cristo, seu unico Filho, nosso Senhor;\nque foi concebido pelo poder do Espirito Santo;\nnasceu da Virgem Maria;\npadeceu sob Poncio Pilatos;\nfoi crucificado, morto e sepultado;\ndesceu a mansao dos mortos;\nressuscitou ao terceiro dia;\nsubiu aos ceus;\nesta sentado a direita de Deus Pai todo-poderoso;\ndonde ha de vir a julgar os vivos e os mortos.\nCreio no Espirito Santo;\nna Santa Igreja Catolica;\nna comunhao dos santos;\nna remissao dos pecados;\nna ressurreicao da carne;\nna vida eterna.\nAmem."
}

if "aba_login" not in st.session_state:
    st.session_state.aba_login = "entrar"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* {{ font-family: 'Inter', sans-serif; box-sizing: border-box; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 1rem 1rem 160px 1rem !important; max-width: 700px !important; }}

.stApp {{
    background-color: #ffffff;
    color-scheme: light !important;
    background-image: url('{NOSSA_SENHORA}');
    background-size: 100% 100% !important;
    background-position: center center !important;
    background-repeat: no-repeat !important;
    background-attachment: scroll !important;
    min-height: 100vh !important;
}}

:root {{ color-scheme: light !important; }}
input, textarea, select {{ color-scheme: light !important; background-color: white !important; color: black !important; }}

.stTextInput > div > div > input {{
    background: rgba(255,255,255,0.95) !important;
    border: 1.5px solid #d4c5a0 !important;
    color: #1a1a1a !important;
    border-radius: 12px !important;
    padding: 0.8rem 1rem !important;
    font-size: 1rem !important;
    -webkit-text-fill-color: #1a1a1a !important;
    color-scheme: light !important;
}}
.stTextInput > div > div > input::placeholder {{ color: #999 !important; }}

div[data-testid="stForm"] {{
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}}

.stFormSubmitButton > button {{
    background: linear-gradient(135deg, #c8a96e, #a07840) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #fff !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.9rem !important;
    box-shadow: 0 4px 15px rgba(200,169,110,0.4) !important;
}}

.msg-user {{ display: flex; justify-content: flex-end; margin: 0.8rem 0; }}
.bubble-user {{
    background-color: #c8a96e; color: #fff;
    padding: 0.75rem 1rem; border-radius: 18px 18px 4px 18px;
    max-width: 85%; font-size: 0.95rem; line-height: 1.6; word-break: break-word;
}}
.msg-bot {{ display: flex; gap: 0.6rem; margin: 0.8rem 0; align-items: flex-start; }}
.bubble-bot {{ font-size: 0.95rem; line-height: 1.7; max-width: 85%; word-break: break-word; }}

.typing {{ display: flex; align-items: center; gap: 4px; padding: 0.5rem 0; }}
.typing span {{ width: 8px; height: 8px; background: #888; border-radius: 50%; animation: bounce 1.2s infinite; }}
.typing span:nth-child(2) {{ animation-delay: 0.2s; }}
.typing span:nth-child(3) {{ animation-delay: 0.4s; }}
@keyframes bounce {{
    0%, 80%, 100% {{ transform: scale(0.7); opacity: 0.4; }}
    40% {{ transform: scale(1); opacity: 1; }}
}}

.welcome {{ text-align: center; padding: 3rem 1rem 2rem 1rem; }}
.welcome h2 {{ font-size: 1.6rem; font-weight: 600; margin-bottom: 0.5rem; }}
.welcome p {{ font-size: 0.9rem; }}

.stButton > button {{
    background: #2f2f2f !important; border: 1px solid #3e3e3e !important;
    color: #ececec !important; border-radius: 12px !important;
    padding: 0.75rem 1rem !important; font-size: 0.95rem !important;
    width: 100% !important; min-height: 48px !important;
}}
.stButton > button:hover {{ background: #3e3e3e !important; }}
.streamlit-expanderHeader {{
    background: #2f2f2f !important; border-radius: 12px !important;
    color: #ececec !important; border: 1px solid #3e3e3e !important;
    min-height: 48px !important;
}}
</style>
""", unsafe_allow_html=True)

API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))

for key, val in [("logado", False), ("username", None), ("chats", {}),
                  ("chat_atual", None), ("input_key", 0), ("pendente", None), ("nome_usuario", ""),
                  ("aba_chat", "chat"), ("oracao_aberta", None)]:
    if key not in st.session_state: st.session_state[key] = val

if "cliente" not in st.session_state:
    st.session_state.cliente = Groq(api_key=API_KEY)

# ── LOGIN ─────────────────────────────────────────────────────────────────────
if not st.session_state.logado:
    st.markdown('''
    <meta name="color-scheme" content="light only">
    <script>
    const obs = new MutationObserver(() => {
        document.querySelectorAll("input").forEach(el => {
            el.style.backgroundColor = "rgba(245,240,232,1)";
            el.style.color = "#1a1a1a";
            el.style.webkitTextFillColor = "#1a1a1a";
        });
    });
    obs.observe(document.body, { childList: true, subtree: true });
    </script>
    ''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align:center; padding: 3rem 0 1.5rem 0;">
            <img src="{LOGO}" style="width:70px;height:70px;border-radius:50%;object-fit:cover;box-shadow:0 4px 20px rgba(200,169,110,0.3);"/>
            <div style="font-size:1.8rem;font-weight:700;color:#1a1a1a;margin:0.7rem 0 0.2rem 0;">Virtual Catholics</div>
            <div style="color:#c8a96e;font-size:0.8rem;letter-spacing:1.5px;font-weight:500;">✝️ ASSISTENTE CATÓLICO</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.aba_login == "entrar":
            with st.form("form_login"):
                u = st.text_input("", placeholder="👤  Usuário", label_visibility="collapsed")
                s = st.text_input("", placeholder="🔒  Senha", type="password", label_visibility="collapsed")
                submitted = st.form_submit_button("Entrar")
                if submitted:
                    usuario = carregar_usuario(u)
                    if usuario and usuario["senha_hash"] == hash_senha(s):
                        st.session_state.logado = True
                        st.session_state.username = u
                        st.session_state.nome_usuario = usuario["nome"]
                        st.session_state.chats = carregar_chats(u)
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos!")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✏️ Criar conta"):
                    st.session_state.aba_login = "criar"
                    st.rerun()
        else:
            with st.form("form_criar"):
                nome_n = st.text_input("", placeholder="👤  Seu nome", label_visibility="collapsed")
                user_n = st.text_input("", placeholder="🔑  Escolha um usuário", label_visibility="collapsed")
                senha_n = st.text_input("", placeholder="🔒  Escolha uma senha", type="password", label_visibility="collapsed")
                submitted = st.form_submit_button("Criar conta")
                if submitted:
                    if nome_n.strip() and user_n.strip() and senha_n.strip():
                        if carregar_usuario(user_n):
                            st.error("Usuário já existe!")
                        else:
                            criar_usuario(user_n, nome_n.strip(), senha_n)
                            st.session_state.logado = True
                            st.session_state.username = user_n
                            st.session_state.nome_usuario = nome_n.strip()
                            st.session_state.chats = {}
                            st.rerun()
                    else:
                        st.error("Preencha todos os campos!")

            if st.button("← Voltar para login"):
                st.session_state.aba_login = "entrar"
                st.rerun()

# ── CHAT ──────────────────────────────────────────────────────────────────────
else:
    st.markdown(f'''<style>
    .stApp {{
        background-color: #ffffff !important;
        background-image: url("{SAGRADA_FAMILIA}") !important;
        background-size: cover !important;
        background-position: center center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(255, 255, 255, 0.80);
        z-index: 0;
        pointer-events: none;
    }}
    .block-container {{ position: relative; z-index: 1; }}
    </style>''', unsafe_allow_html=True)

    username = st.session_state.username
    nome = st.session_state.nome_usuario
    memoria = carregar_memoria(username)
    fatos = memoria.get("fatos", [])
    fatos_str = "\n".join(fatos) if fatos else "Nenhum ainda."

    system_prompt = f"""Você é o Virtual Catholics, uma IA católica criada por Pedro.
Você tem fé católica profunda e responde com base nos ensinamentos da Igreja Católica.
Você é engraçado, divertido e acolhedor, mas sempre fiel à fé.
Responda sempre em português brasileiro.
O nome do usuário é: {nome}.
Fatos que você já sabe sobre ele: {fatos_str}
Quando o usuário revelar algo importante, inclua: [LEMBRAR: fato aqui]
"""

    with st.expander("📋 Menu"):
        # ── CHATS ──
        st.markdown("<p style='color:#c8a96e;font-weight:700;margin:0.5rem 0 0.3rem 0;'>💬 CHATS</p>", unsafe_allow_html=True)
        if st.button("➕ Novo chat", use_container_width=True):
            chat_id = novo_chat_id()
            st.session_state.chats[chat_id] = {"titulo": "Nova conversa", "historico": []}
            salvar_chat(username, chat_id, "Nova conversa", [])
            st.session_state.chat_atual = chat_id
            st.session_state.aba_chat = "chat"
            st.session_state.input_key += 1
            st.rerun()
        for chat_id in sorted(st.session_state.chats.keys(), reverse=True):
            titulo = st.session_state.chats[chat_id]["titulo"]
            if st.button(f"💬 {titulo}", key=f"c_{chat_id}", use_container_width=True):
                st.session_state.chat_atual = chat_id
                st.session_state.aba_chat = "chat"
                st.session_state.input_key += 1
                st.rerun()
        if st.session_state.chat_atual and st.session_state.chat_atual in st.session_state.chats:
            if st.button("🗑️ Deletar conversa", use_container_width=True):
                deletar_chat(username, st.session_state.chat_atual)
                del st.session_state.chats[st.session_state.chat_atual]
                st.session_state.chat_atual = None
                st.rerun()

        st.markdown("<hr style='border-color:#3e3e3e;margin:0.8rem 0;'>", unsafe_allow_html=True)

        # ── ORAÇÕES / BÍBLIA ──
        st.markdown("<p style='color:#c8a96e;font-weight:700;margin:0.3rem 0;'>🙏 RECURSOS</p>", unsafe_allow_html=True)
        if st.button("🙏 Orações", use_container_width=True, key="btn_oracoes"):
            st.session_state.aba_chat = "oracoes"
            st.session_state.oracao_aberta = None
            st.rerun()
        if st.button("📖 Bíblia", use_container_width=True, key="btn_biblia"):
            st.session_state.aba_chat = "biblia"
            st.rerun()

        st.markdown("<hr style='border-color:#3e3e3e;margin:0.8rem 0;'>", unsafe_allow_html=True)

        # ── CONTA ──
        st.markdown("<p style='color:#c8a96e;font-weight:700;margin:0.3rem 0;'>👤 CONTA</p>", unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True):
            for k in ["logado", "username", "chats", "chat_atual", "nome_usuario"]:
                st.session_state[k] = False if k == "logado" else None if k != "chats" else {}
            st.rerun()

    # ── ABA ORAÇÕES ──
    if st.session_state.aba_chat == "oracoes":
        if st.session_state.oracao_aberta:
            titulo_o = st.session_state.oracao_aberta
            texto_o = ORACOES[titulo_o].replace("\n", "<br>")
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;">
                <h3 style="color:#c8a96e;margin-bottom:1rem;">🙏 {titulo_o}</h3>
                <p style="color:#1a1a1a;line-height:2.2;font-size:1.05rem;">{texto_o}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("← Voltar"):
                st.session_state.oracao_aberta = None
                st.rerun()
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            for nome_oracao in ORACOES:
                if st.button(f"🙏 {nome_oracao}", use_container_width=True, key=f"o_{nome_oracao}"):
                    st.session_state.oracao_aberta = nome_oracao
                    st.rerun()
        st.stop()

    # ── ABA BÍBLIA ──
    if st.session_state.aba_chat == "biblia":
        st.markdown("<br>", unsafe_allow_html=True)
        livros = ["genesis","exodo","levitico","numeros","deuteronomio","josue","juizes","rute","1samuel","2samuel","1reis","2reis","1cronicas","2cronicas","esdras","neemias","ester","jo","salmos","proverbios","eclesiastes","cantares","isaias","jeremias","lamentacoes","ezequiel","daniel","oseias","joel","amos","abdias","jonas","miqueias","naum","habacuque","sofonias","ageu","zacarias","malaquias","mateus","marcos","lucas","joao","atos","romanos","1corintios","2corintios","galatas","efesios","filipenses","colossenses","1tessalonicenses","2tessalonicenses","1timoteo","2timoteo","tito","filemom","hebreus","tiago","1pedro","2pedro","1joao","2joao","3joao","judas","apocalipse"]
        livros_display = [l.replace("1","1 ").replace("2","2 ").replace("3","3 ").title() for l in livros]

        col_b1, col_b2 = st.columns([3,1])
        with col_b1:
            livro_sel = st.selectbox("Livro", livros_display, label_visibility="collapsed")
        with col_b2:
            cap_sel = st.number_input("Cap", min_value=1, max_value=150, value=1, label_visibility="collapsed")

        livro_api = livros[livros_display.index(livro_sel)]

        if st.button("📖 Ler", use_container_width=True):
            import requests as req
            try:
                url = f"https://bible-api.com/{livro_api}+{cap_sel}?translation=almeida"
                r = req.get(url, timeout=10)
                data = r.json()
                if "verses" in data:
                    versiculos = ""
                    for v in data["verses"]:
                        versiculos += f'<p style="margin:0.4rem 0;color:#1a1a1a;"><b style="color:#c8a96e;">{v["verse"]}</b> {v["text"]}</p>'
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;max-height:60vh;overflow-y:auto;">
                        <h3 style="color:#c8a96e;margin-bottom:1rem;">📖 {livro_sel} {cap_sel}</h3>
                        {versiculos}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Capítulo não encontrado!")
            except:
                st.error("Erro ao carregar a Bíblia. Tente novamente!")
        st.stop()



    if not st.session_state.chat_atual or st.session_state.chat_atual not in st.session_state.chats:
        st.markdown(f"""
        <div class="welcome">
            <div style="margin-bottom:1rem;">{logo_html}</div>
            <h2 style="color:#1a1a1a!important;-webkit-text-fill-color:#1a1a1a;">Olá, {nome}! 🙏</h2>
            <p style="color:#333!important;">Abra <b>Conversas</b> e clique em <b>Novo chat</b>.</p>
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
                        if fato not in fatos:
                            fatos.append(fato)
                            salvar_memoria(username, fatos)
                mensagem = "\n".join([l for l in mensagem.split("\n") if "[LEMBRAR:" not in l])
            historico.append({"role": "assistant", "content": mensagem})
            if len(historico) == 2:
                primeira = historico[0]["content"]
                titulo = primeira[:35] + ("..." if len(primeira) > 35 else "")
                st.session_state.chats[chat_id]["titulo"] = titulo
                salvar_chat(username, chat_id, titulo, historico)
            else:
                salvar_chat(username, chat_id, st.session_state.chats[chat_id]["titulo"], historico)
            st.rerun()

        chat_html = ""
        if not historico:
            chat_html = '<div class="welcome"><h2 style="color:#1a1a1a!important;">Nova conversa 🙏</h2><p style="color:#333!important;">Como posso te ajudar?</p></div>'
        else:
            for msg in historico:
                if msg["role"] == "user":
                    chat_html += f'<div class="msg-user"><div class="bubble-user">{msg["content"]}</div></div>'
                else:
                    chat_html += f'<div class="msg-bot"><div style="flex-shrink:0;margin-top:2px;">{logo_html}</div><div class="bubble-bot" style="color:#1a1a1a!important;background:rgba(255,255,255,0.85);padding:0.7rem 1rem;border-radius:0 16px 16px 16px;">{msg["content"]}</div></div>'

        if st.session_state.pendente:
            chat_html += f'<div class="msg-bot"><div style="flex-shrink:0;margin-top:2px;">{logo_html}</div><div class="typing"><span></span><span></span><span></span></div></div>'

        st.markdown(chat_html, unsafe_allow_html=True)

        user_input = st.text_input("", placeholder="Manda uma mensagem...", key=f"inp_{st.session_state.input_key}", label_visibility="collapsed")
        if user_input and user_input.strip():
            historico.append({"role": "user", "content": user_input.strip()})
            st.session_state.chats[chat_id]["historico"] = historico
            st.session_state.pendente = user_input.strip()
            st.session_state.input_key += 1
            st.rerun()

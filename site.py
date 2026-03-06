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

TERCOS = {
    "Misterios Gozosos (Segundas e Sabados)": [
        ("1 - Anunciacao do anjo a Nossa Senhora", "Mae da Divina Graca, dai-nos a virtude da total entrega, num sim sempre constante a Vontade de Deus Pai. Amem."),
        ("2 - Visita de Nossa Senhora a Santa Isabel", "Mae amada, dai-nos a virtude de servir sempre, com amor, simplicidade e de louvarmos a Deus, como glorificastes, em Vosso Magnificat, ao nosso Pai e Criador, com todo coracao. Amem."),
        ("3 - Nascimento de Jesus", "Mae e Rainha nossa, dai-nos um coracao humilde e acolhedor como a gruta de Belem, para que Jesus possa nascer e viver sempre dentro de nosso coracao. Amem."),
        ("4 - Apresentacao de Jesus no Templo", "Mae nossa e Medianeira de todas as gracas, apresentamos ao altar do Senhor, tudo o que somos e temos, nossa familia, trabalho, lagrimas, sofrimentos e alegrias, para que o Senhor possa transformar em santidade o que e culpavel em nos. Amem."),
        ("5 - Perda e reencontro de Jesus no Templo", "Mae amada, que nao deixemos a fe, a presenca de Jesus Cristo em nossa vida. Concedei-nos tambem o espirito do apostolado, nao somente por palavras, mas sobretudo pelos testemunhos de nossa vida. Amem.")
    ],
    "Misterios Dolorosos (Tercas e Sextas)": [
        ("1 - Agonia de Jesus no Horto das Oliveiras", "Senhor, que sofrestes a dor profunda da agonia, sendo inocente e o mais santo entre todos os homens, concedei-nos a Vossa forca em nossas dores e que saibamos pagar sempre o mal com o bem. Amem."),
        ("2 - Flagelacao de Jesus", "Senhor, perdoai-me por Vos flagelar quando peco contra meus irmaos, quando nao cumpro os Mandamentos, quando me esqueco do quanto sofrestes por me amar e desejar minha salvacao. Dai-me um coracao novo, fazei de mim uma nova criatura. Amem."),
        ("3 - Jesus e coroado de espinhos", "Senhor, livrai-nos das aflicoes mentais, traumas, pensamentos maus que temos; dai-nos cura interior para que possamos ser instrumentos muito mais eficazes da Vossa Vontade. Amem."),
        ("4 - Jesus carregando a Cruz", "Senhor, Vos que carregastes uma cruz tao pesada, rumo ao Calvario, sabendo o quanto haverieis de sofrer por meus pecados, fazei com que eu carregue todo fardo de meus dias com amor, paciencia e esperanca. E, que oferecendo tudo pelos meus pecados, pelas almas que sofrem no purgatorio, pelos que estejam sofrendo no mundo inteiro, jamais esbraveje e sim Vos louve em todo o tempo. Amem."),
        ("5 - Crucificacao de Jesus", "Senhor, Vos que do alto da cruz pedistes, em Vosso Santissimo amor, que o Pai perdoasse a Vossos algozes, por que nao sabiam o que faziam, dai-me o dom do mais perfeito perdao. Dai-me a capacidade de amar e perdoar com perfeicao e rezar por todos aqueles que me persigam ou facam o mal contra mim. Amem.")
    ],
    "Misterios Gloriosos (Quartas e Domingos)": [
        ("1 - A Ressurreicao de Jesus", "Senhor, Vos que gloriosamente ressuscitastes, vencendo a morte, glorificado pelo Pai, concedei-nos a graca de crer em santidade, segundo a Vossa Vontade, para que um dia possa estar convosco na Gloria eterna. Amem."),
        ("2 - A Ascensao de Jesus aos Ceus", "Senhor, que cada dia de minha vida se torne um passo na ascensao a Vos. Que nada me faca retroceder no caminho em minha ascese. Quero viver em conformidade a Vossa Santissima Vontade hoje e sempre. Amem."),
        ("3 - A Vinda do Espirito Santo (Pentecostes)", "Glorioso Jesus, que enviastes o Espirito Santo sobre os apostolos, antes ignorantes e medrosos, tornando-os destemidos, vem sobre mim e sobre a humanidade inteira, a fim de que pelo mesmo Espirito, possamos ser salvos e testemunhas do Vosso santo amor. Amem."),
        ("4 - A Assuncao de Nossa Senhora aos Ceus", "Mae de Misericordia, apos terdes sofrido as dores das angustias, paixao e morte de Vosso divinissimo Filho, concedei-nos a graca de olhar a tudo com o Vosso olhar, amar com Vosso coracao, passar pelos sofrimentos com resignacao e coragem, guiados pela fe e pelo amor que temos em Vos. Amem."),
        ("5 - A Coroacao de Nossa Senhora como Rainha dos Ceus", "Mae e Rainha nossa, revestindo-nos com Vossas santas virtudes de obediente e boa maternal bondade, a fim de que possamos atingir esta coroa de Vossa santidade. Depositamos neste altar de meu amor e devocao a Vossos santissimos pes, com total confianca a Vossa maternal e constante protecao. Amem.")
    ],
    "Misterios Luminosos (Somente as quintas)": [
        ("1 - Batismo de Jesus no Jordao", "Senhor, lavai minha alma de todo pecado e rancores, ressentimentos passados. Vinde sobre mim, com Vosso Espirito Santo. Amem."),
        ("2 - Auto-revelacao de Jesus nas Bodas de Cana", "Senhor, assim como transformastes a agua em vinho, por amor a Vossos filhos, transformai tudo o que impede de Vos causar alegria. Transformai o meu coracao no Vosso coracao. A nossa Mae Santissima, advogada dos pobres pecadores que somos, peco que interceda junto a Deus, por mim e por toda a humanidade. Amem."),
        ("3 - Jesus anuncia o Reino de Deus com o convite a conversao", "Senhor, dirijo-me a Vos para, com total confianca e humildade, reconhecer minhas culpas e pedir-Vos perdao. Converte-me inteiramente, a fim de que eu possa ser instrumento de conversao para muitos de Vossos filhos. Amem."),
        ("4 - Transfiguracao de Jesus", "Senhor, que minha vida seja vivida como no Monte Tabor, catasiada com Vossos prodigios e santidade. Reluz em minha face o brilho da Vossa Face e concede-me a graca de viver unicamente para Vos, em todos os momentos de minha vida. Amem."),
        ("5 - Instituicao da Eucaristia", "Senhor, eu Vos dou gracas por terdes permanecido entre nos, em especial na Santa Eucaristia. Vos Dou gracas pelos sacerdotes, pois somente por eles pode ocorrer o sublime milagre da Transfiguracao. Fazei descer o Espirito Santo sobre os sacerdotes do mundo inteiro, sobre todo o clero. Amem.")
    ],
    "Terco da Batalha": [
        ("Inicio", "Credo, Pai Nosso, Ave Maria 3x."),
        ("Nas contas grandes", "Deus do ceu, me de forcas. Jesus Cristo me de o poder de vencer. Nossa Senhora me de coragem para me defender. Sem morrer, sem enlouquecer, serei militante ate o fim. Deus pode, Deus quer; esta batalha eu hei de vencer."),
        ("Nas contas pequenas", "Eu hei de vencer."),
        ("No final", "Salve Rainha. Mae de Jesus e nossa Mae, abencoa-nos e ouvi nossos rogos. A vitoria e nossa pelo sangue de Jesus!")
    ],
    "Terco de Sao Bento": [
        ("Inicio", "Em nome do Pai, do Filho e do Espirito Santo. Amem. Vinde Espirito Santo, enchei nos coracoes dos Vossos fieis e acendei neles o fogo do Vosso Amor. Enviai o Vosso Espirito e tudo sera criado e renovai a face da terra. O Deus Santo, faze que apreciemos, chamando-nos sempre segundo o mesmo Espirito e governemos a face de Vosso Santo Senhor Nosso. Amem."),
        ("Credo e Pai Nosso + Oracao Inicial", "Recite o Credo e um Pai Nosso. ORACAO INICIAL: O Glorioso Sao Bento que sempre demonstrou compromisso com os seus afazeres, atendendo a Vossa chamada a paz e a tranquilidade; que em nossas familias cure a paz e a tranquilidade, que se afastem todas as desgragas, junto corporais como espirituais, especialmente o pecado. Alcancai Sao Bento, do Senhor Deus Onipotente, a graca que necessitamos."),
        ("Nas contas do Pai Nosso", "A Cruz Sagrada seja a minha luz, nao seja o dragao o meu guia. Retira-te, satanas! Nunca me aconselhes coisas vas. E mau o que tu me ofereces, bebe tu mesmo o teu veneno! Sao Bento dai-nos a graca de que, ao terminar nossa vida neste vale de lagrimas, possamos ir louvar a Deus convosco no Paraiso."),
        ("Nas contas da Ave Maria", "Sao Bento, Vos intercedei por nos, libertai-nos do inveja. Sede Vos nossa libertador do mal, libertai-nos do pecado!"),
        ("Ao final", "Em nome do Pai, do Filho e do Espirito Santo. Amem.")
    ],
    "Terco do Louvor": [
        ("Como rezar", "O Terco do Louvor pode ser rezado em qualquer ocasiao ou lugar, usando um Rosario comum. Voce rezara nas contas maiores, onde se reza o Pai Nosso, a seguinte oracao: Senhor, abri meus labios a fim de que minha boca anuncie Vossos louvores (cf. Sl 50,17)"),
        ("Nas contas menores (10 Ave Marias)", "Jesus, te louvo e te bendigo... (Colocando aqui o seu motivo de louvor). Por exemplo: pelo meu marido(a), pela minha esposa, pelo meu filho(a), pela minha saude, por minha situacao, pelo meu emprego, pela minha vida, pelo meu paroco, pela minha familia. Voce pode acrescentar inumeras outras intencoes, rezando o Terco inteiro ou uma intencao em cada dezena."),
        ("Finalizando cada dezena", "Gloria ao Pai, ao Filho e ao Espirito Santo. Como era no principio, agora e sempre. Amem.")
    ],
    "Terco da Paixao": [
        ("No principio", "Pai Nosso, Ave Maria 3x."),
        ("Nas contas grandes", "Divino, porque da Vossa Paixao e Morte..."),
        ("Nas contas pequenas", "...pela misericordia de nos e do mundo inteiro."),
        ("Ao final do Terco, reze 3 vezes", "Tende piedade de nos e do mundo inteiro."),
        ("Encerramento", "Deus Imortal, tende piedade de nos e do mundo inteiro. Amem.")
    ],
    "Terco da Libertacao": [
        ("Apresentacao", "No principio e acao: Se Jesus me liberta, sou verdadeiramente livre! Nas contas grandes e acao: Se Jesus me liberta, liverta-me! Observacao: O Terco pode ser rezado por voce, sua familia, e por outras pessoas."),
        ("Em cada dezena - nas contas grandes", "Chagas abertas, coracao ferido, o sangue de Cristo esta entre (poe-se a intencao) e o perigo."),
        ("Nas contas pequenas", "Jesus, pelas chagas da Vossa coracao ferido, o sangue de Cristo esta entre (poe-se a intencao) e o perigo. Jesus, pelas chagas da Vossa coracao ferido liberte (poe a pessoa ou a intencao)."),
        ("Quinta dezena - Oremos", "Jesus, o Senhor carregou todos as nossas dores e enfermidades, carregou os nossos sofrimentos, pelo Seu sangue redentor, liberta-nos do mal, liberta-nos do pecado. Amem."),
        ("Encerramento", "Deus da misericordia, do amor, medo, falta de perdao, intrigas, brigas, discordias, ciume, divisao e reserva em nos liberta-nos. Saude desuniao, falta de fe, da esperanca e da caridade. Amem.")
    ],
    "Terco do Sagrado Coracao de Jesus": [
        ("Inicio", "No principio: Credo, Pai Nosso, Ave Maria 3x, Gloria ao Pai. Sagrado Coracao, fonte do amor, templo de Deus, amado Jesus, Coracao amante dos homens, Coracao amantissimo de Jesus, Coracao obediente, humilde e brando, Coracao paciente e misericordioso, Coracao delicia de todos os Santos, Coracao desejoso da nossa salvacao, Coracao fonte de toda a santidade."),
        ("Nas contas grandes", "Sagrado Coracao de Jesus, tende piedade de nos."),
        ("Nas contas pequenas", "Sagrado Coracao de Jesus, eu vos amo."),
        ("Graca a alcancar", "Peca a graca que necessita. Em Vos eu confio. Amem."),
        ("Encerramento", "Sagrado Coracao de Jesus, em Vos eu confio. Amem.")
    ],
    "Terco da Vitoria pelas Chagas de Jesus": [
        ("Abertura", "Cura-me, Senhor Jesus, Jesus coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento. Tu podes curar e foi de Tuas maos que superamos o mais grande dos males - foram pregadas na cruz. Maos ensanguentadas de Jesus, maos feridas (poe-se a intencao), vem tocar em mim, vem, Senhor Jesus, vem todas, vem. Reza-se um Pai Nosso, Uma Ave Maria e o Credo."),
        ("Em cada dezena - nas contas grandes", "Chagas abertas, coracao ferido, o sangue de Cristo esta entre (poe-se a intencao) e o perigo."),
        ("Nas contas pequenas", "Jesus, pelas chagas da Vossa coracao ferido, o sangue de Cristo esta entre (poe-se a intencao) e o perigo. Jesus, pelas chagas da Vossa coracao ferido liberte (poe a pessoa ou a intencao)."),
        ("Quinta dezena - Oremos", "Jesus, o Senhor sobre as nossas dores e enfermidades, carregou os nossos sofrimentos, pelo Seu sangue redentor, liberta-nos do nosso corpo, por todas as chagas do Seu corpo, por todas as chagas dos Seus pes liberte (poe a pessoa ou a intencao)."),
        ("Encerramento", "Jesus, o Senhor carregou todos as nossas dores e enfermidades, pelo Seu sangue redentor, liberta-nos do mal, liberta-nos do pecado. Amem.")
    ],
    "Terco pelos Filhos": [
        ("Inicio", "Em nome do Pai, do filho, do Espirito Santo, amem! Creio em Deus Pai... Pai Nosso que estais no ceu... Ave Maria (3 vezes)."),
        ("Para iniciar", "Abro meu coracao, deixo o Espirito Santo entrar. Peco pra Ele mudar toda a minha situacao..."),
        ("Nas Contas Maiores", "Quero de joelhos ver meus filhos de pe! Deus me sustenta e aumenta a minha fe!"),
        ("Nas Contas Pequenas", "Deus, mantenha meu filho de pe! (10 vezes)"),
        ("Para encerrar", "Deus pode tudo, tudo, tudo! (3 vezes)")
    ],
    "Terco do Agradecimento": [
        ("Abertura", "Obrigado Jesus, por mais um dia de vida. Peco-te Senhor que me restaure, me cure, me liberte e me torne um(a) filho(a) obediente e grato e que eu possa a cada minuto Te agradecer por tudo."),
        ("Nas contas", "Obrigado Senhor pela minha vida. Obrigado Senhor pela natureza. Obrigado Senhor pelo pao de cada dia. Obrigado Senhor por... (faca seu agradecimento)"),
        ("Encerramento", "Gloria ao Pai, ao Filho e ao Espirito Santo. Como era no principio, agora e sempre. Amem.")
    ]
}

COMO_REZAR_TERCO = """Como rezar o Terco:

1. Comece com o Credo (Creio em Deus Pai)
2. Reze 1 Pai Nosso
3. Reze 3 Ave Marias (pelas virtudes de fe, esperanca e caridade)
4. Reze 1 Gloria ao Pai
5. Anuncie o 1 misterio e medite
6. Reze 1 Pai Nosso
7. Reze 10 Ave Marias meditando no misterio
8. Reze 1 Gloria ao Pai
9. Repita os passos 5 a 8 para cada misterio
10. Termine com a Salve Rainha"""

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
                  ("aba_chat", "chat"), ("oracao_aberta", None), ("terco_aberto", None), ("terco_misterio", None)]:
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
        if st.button("📿 Terço", use_container_width=True, key="btn_terco"):
            st.session_state.aba_chat = "terco"
            st.session_state.terco_aberto = None
            st.session_state.terco_misterio = None
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

    # ── ABA TERCO ──
    if st.session_state.aba_chat == "terco":
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.terco_misterio is not None:
            nome_t = st.session_state.terco_aberto
            misterios = TERCOS[nome_t]
            idx = st.session_state.terco_misterio
            titulo_m, texto_m = misterios[idx]
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;">
                <p style="color:#c8a96e;font-size:0.8rem;font-weight:700;">{nome_t}</p>
                <h3 style="color:#1a1a1a;margin:0.5rem 0;">📿 {titulo_m}</h3>
                <p style="color:#1a1a1a;line-height:1.9;font-size:1rem;margin-top:1rem;">{texto_m}</p>
                <br>
                <p style="color:#888;font-size:0.85rem;">Reze 1 Pai Nosso + 10 Ave Marias + 1 Gloria ao Pai</p>
            </div>
            """, unsafe_allow_html=True)
            col_ant, col_prox = st.columns(2)
            with col_ant:
                if idx > 0:
                    if st.button("← Anterior", use_container_width=True):
                        st.session_state.terco_misterio -= 1
                        st.rerun()
            with col_prox:
                if idx < 4:
                    if st.button("Próximo →", use_container_width=True):
                        st.session_state.terco_misterio += 1
                        st.rerun()
                else:
                    if st.button("✅ Concluído", use_container_width=True):
                        st.session_state.terco_misterio = None
                        st.session_state.terco_aberto = None
                        st.rerun()
            if st.button("← Voltar ao Terço"):
                st.session_state.terco_misterio = None
                st.rerun()
        elif st.session_state.terco_aberto:
            nome_t = st.session_state.terco_aberto
            como = COMO_REZAR_TERCO.replace("\n", "<br>")
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;">
                <h3 style="color:#c8a96e;margin-bottom:1rem;">📿 {nome_t}</h3>
                <p style="color:#1a1a1a;line-height:1.9;font-size:0.9rem;">{como}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("▶️ Começar os Mistérios", use_container_width=True):
                st.session_state.terco_misterio = 0
                st.rerun()
            if st.button("← Voltar"):
                st.session_state.terco_aberto = None
                st.rerun()
        else:
            for nome_t in TERCOS:
                if st.button(f"📿 {nome_t}", use_container_width=True, key=f"t_{nome_t}"):
                    st.session_state.terco_aberto = nome_t
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

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
    "Pai Nosso": "Pai nossó que estais no ceu,\nsantificado sejá o vossó nome,\nvenha a nós o vossó reino,\nsejá féita a vossa vontade,\nassim na terra como no ceu.\nO pao nossó de cada dia nós dai hoje,\npérdoai as nossas ofénsas,\nassim como nós pérdoamos\na quem nós tem oféndido,\ne não nós deixeis cair em tentação,\nmas livrai-nós do mal.\nAmem.",
    "Ave Maria": "Ave Maria, cheia de graça,\no Senhor e convosco,\nbendita sois vos entre as mulheres,\ne bendito e o fruto do vossó ventre, Jesus.\nSanta Maria, Mãe de Deus,\nrogai por nós péçadores,\nagora e na hora de nossa morte.\nAmem.",
    "Gloria ao Pai": "Gloria ao Pai,\não Filho\ne ao Espírito Santo.\nComo era no principio,\nagora e sempre,\npélos seculos dos seculos.\nAmem.",
    "Creio em Deus Pai": "Creio em Deus Pai todo-poderoso,\ncriador do ceu e da terra;\ne em Jesus Cristo, seu único Filho, nossó Senhor;\nque foi concebido pélo poder do Espírito Santo;\nnasceu da Virgem Maria;\npadeceu sob Poncio Pilatos;\nfoi crucificado, morto e sepultado;\ndesceu a mansao dos mortos;\nressuscitou ao terceiro dia;\nsubiu aos ceus;\nesta sentado a direita de Deus Pai todo-poderoso;\ndonde ha de vir a julgar os vivos e os mortos.\nCreio no Espírito Santo;\nna Santa Igreja Catolica;\nna comunhao dos santos;\nna remissão dos péçados;\nna ressurreição da carne;\nna vida eterna.\nAmem."
,
    "Salve Rainha": "Salve Rainha, Mae de Misericordia,\\nvida, docura e esperanca nossa, salve!\\nA Vos bradamos, os degredados filhos de Eva.\\nA Vos suspiramos, gemendo e chorando neste vale de lagrimas.\\nEia, pois, advogada nossa,\\nessas Vossas misericordias para nos volvei os olhos.\\nE depois deste desterro nos mostrai Jesus,\\nbento fruto do Vosso ventre.\\nO clemente! O piedosa! O doce Virgem Maria!\\nRogai por nos Santa Mae de Deus,\\npara que sejamos dignos das promessas de Cristo. Amem.",
    "Sinal da Santa Cruz": "Pelo sinal da Santa Cruz,\\nlivrai-nos, Deus, nosso Senhor, dos nossos inimigos.\\nEm nome do Pai, do Filho e do Espirito Santo. Amem.",
    "Vinde Espirito Santo": "Vinde, Espirito Santo,\\nenchei os coracoes dos Vossos fieis\\ne acendei neles o fogo do Vosso Amor.\\nEnviai o Vosso Espirito e tudo sera criado\\ne renovareis a face da terra.\\nOremos: O Deus, que iluminastes os coracoes dos Vossos fieis\\ncom a luz do Espirito Santo,\\nfazei que apreciemos retamente todas as coisas,\\nsegundo o mesmo Espirito e gozemos da Vossa consolacao.\\nPor Cristo Senhor Nosso. Amem.",
    "Santo Anjo do Senhor": "Anjo de Deus, que sois minha guarda e protecao,\\nInspirai-me, Defendei-me, Dirigei-me, Governai-me, Protegei-me. Amem.",
    "Consagracao a Nossa Senhora": "O minha Senhora, o minha Mae,\\neu me ofereço todo a Vos,\\ne em prova de minha devocao para convosco,\\neu Vos consagro hoje meus olhos, meus ouvidos,\\nminha boca, meu coracao, inteiramente todo o meu ser.\\nE como assim sou Vosso,\\nconservai-me, guardai-me, como coisa e propriedade Vossa. Amem.",
    "Oracao a Sao Miguel Arcanjo": "Sao Miguel Arcanjo, defendei-nos no combate,\\nSede nosso amparo contra as maldades e ciladas do diabo.\\nDeus o reprima, oramos suplicantes.\\nE Vos, Principe da Milicia Celestial,\\npelo poder divino, aterrai no inferno a Satanas\\ne a outros espiritos malignos\\nque andam pelo mundo para perdicao das almas. Amem.",
    "Oracao a Nossa Senhora Desatadora dos Nos": "Em nome do Pai, do Filho e do Espirito Santo.\\nSanta Maria, Mae de Deus, Virgem cheia de graca,\\nVos sois a nossa desatadora dos nos.\\nCom as Vossas maos cheias do amor de Deus,\\nVos desatais os obstaculos de nosso caminho.\\nDesatai, Virgem e Mae, Santa e admiravel,\\ntodos os nos que criamos por vontade propria,\\ne todos os nos que impedem o nosso caminho.\\nLancai Vossos olhos de luz sobre eles,\\npara que todos os nos se desatem e,\\npara que, cheios de gratidao, possamos,\\npor Vossas maos, solucionar aquilo que nos parece impossivel. Amem.",
    "Oracao a Santa Rita de Cassia": "O poderosa e gloriosa Santa Rita,\\neis a vossos pes uma alma desamparada\\nque necessitando de auxilio, a vos recorre com fe e esperanca,\\nque tens o titulo de Santa dos casos impossiveis.\\nO gloriosa Santa, olhai por minha causa,\\nintercedei junto a Deus para que me consiga\\na graca de que tanto necessito (faca seu pedido).\\nO Santa Rita, advogada dos impossiveis,\\nrogai por mim, rogai por todos nos. Amem!",
    "Oracao para a Familia": "Jesus, Maria e Jose, modelos perfeitos de caridade e uniao,\\nalcancai-nos a graca de vos imitar.\\nLembrai-vos que somos todos vossos.\\nDefendei-nos de todo o perigo, socorrei-nos em nossas necessidades\\na fim de que, servindo-vos fielmente na terra,\\npossamos bendizer-vos eternamente no ceu.\\nAssim seja! Senhor, escutai nossa prece!",
    "Oracao contra Enfermidade": "O querido e doce Menino Jesus,\\neis aqui um pobre enfermo que, movido pela mais viva fe,\\nsinceramente invoca Vossa divina ajuda em favor de sua enfermidade.\\nPonho em Vos toda a minha confianca.\\nSei que tudo podeis e sois muito misericordioso.\\nGrande pequenino, por Vossas divinas virtudes\\ne pelo imenso amor que nutris pelos sofredores,\\nouvi-me, bendizei-me, socorrei-me, consolai-me. Amem.\\nTres Gloria ao Pai.",
    "Oracao a Santa Edwiges": "O Santa Edwiges,\\nvos que na terra fostes o amparo dos pobres,\\na ajuda dos desvalidos e o socorro dos endividados,\\nsuplicante te peco que sejais a minha advogada,\\npara que eu obtenha de Deus o auxilio de que urgentemente preciso (faca o pedido).\\nAlcancai-me tambem a suprema graca da salvacao eterna.\\nSanta Edwiges, rogai por nos. Amem.",
    "Oracao pelas Vocacoes": "Filho de Deus, enviado pelo Pai para junto dos homens de todos os tempos!\\nInvocamos-Vos por meio de Maria, Vossa e nossa Mae;\\nfazei com que na Igreja nao faltem vocacoes,\\nem particular as de especial consagracao ao Vosso Reino.\\nJesus, unico Salvador do mundo!\\nPedimos-Vos pelos nossos irmaos e irmas,\\nque responderam sim ao Vosso apelo ao sacerdocio, a vida consagrada e a missao.\\nSenhor misericordioso e santo,\\ncontinuai a enviar novos trabalhadores para a messe do Vosso Reino!\\nVos, que sois Deus, vivei e reinais com o Pai e o Espirito Santo,\\nnos seculos dos seculos. Amem!",
    "Oracao pelo Trabalhador": "Bom dia meu Deus!\\nAntes que comece este dia, quero falar com o Senhor.\\nDentro de mim existe uma gratidao imensa,\\nporque eu tenho um ganha-pao,\\nenquanto tantas pessoas sofrem com o desemprego e a fome.\\nMuitas vezes, quando chego em casa, sinto o meu corpo cansado,\\nmas ate por esse cansaco eu Lhe agradeco.\\nConceda-me, Senhor, aprender com as pessoas que trabalham comigo.\\nPermita-me ama-las, ainda que nao estejam abertas para o amor.\\nDerrame sobre o meu ambiente de trabalho a Sua paz.\\nQuero crescer com dignidade e respeito.\\nDe-me a coragem para prosseguir\\ne a certeza de que, atraves do meu trabalho,\\npoderei fazer com que um pedacinho do mundo se transforme num lugar melhor. Amem.",
    "Oracao a Sao Bento": "Glorioso Sao Bento, que dedicaste toda sua vida a Cristo e aos irmaos,\\nprotegei-me contra os ataques do mal,\\nlivrai-me das insidias do inimigo,\\nconcedei-me a paz interior e a fortaleza diante das tempestades da vida.\\nO poderoso Sao Bento, defendei-me dos olhares invejosos\\ne ensinai-me a partilhar o amor com todos.\\nQue a Cruz do Senhor me guie pelos caminhos de luz.\\nAfasta de minha vida e de minha familia toda forca do mal. Amem!",
    "Oracao pela Protecao": "Que Deus Pai, Senhor do Universo, Todo Poderoso,\\nnos proteja, nos ilumine e nos guarde.\\nQue os santos derramem sobre nos suas bencaos.\\nQue os anjos estejam sempre conosco, guardando nossas vidas,\\npara que por onde passarmos, a Sua luz chegue primeiro.\\nEm nome do Pai, do Filho e do Espirito Santo. Amem.",
    "Oracao para Dormir": "Meu Pai, agora que as vozes silenciaram,\\naqui ao pe da cama minha alma se eleva a Ti.\\nDeposito nas Tuas maos a fadiga e a luta,\\nas alegrias e desencantos deste dia.\\nSe os nervos me trairam, se dei lugar ao rancor,\\nperdao, Senhor! Tem piedade de mim.\\nNesta noite nao quero entregar-me ao sono\\nsem sentir na minha alma a seguranca da Tua misericordia.\\nEu Te agradeco, meu Pai,\\nporque foste a sombra fresca que me cobriu durante todo este dia.\\nEnvia o anjo da paz a esta casa.\\nRelaxa meus nervos, sossega o meu espirito.\\nVela por mim, Pai querido,\\nenquanto eu me entrego confiante ao sono,\\ncomo uma crianca que dorme feliz em Teus bracos.\\nEm Teu Nome, Senhor, descansarei tranquilo. Amem.",
    "Ato de Fe": "Meus Deus, creio firmemente em todas as verdades\\nque nos revelastes e que nos ensinais por Tua Igreja,\\nporque nao podes enganar nem nos enganar.",
    "Ato de Esperanca": "Meu Deus, espero com firme confianca que me concederas,\\npelos meritos de Jesus Cristo, Tua graca neste mundo\\ne a felicidade eterna no outro,\\nporque assim o prometestes e sempre es fiel a Tuas promessas.",
    "Ato de Caridade": "Meu Deus, amo-Te com todo meu coracao e sobre todas as coisas,\\nporque es infinitamente bom e amavel.\\nPrometo, com Tua graca, amar a meu proximo como a mim mesmo por Teu amor.",
    "Ato de Contricao": "Meu Deus, tenho muita pena de ter pecado,\\npois mereci ser castigado por ter ofendido a Vos,\\nmeu Pai e meu Salvador.\\nPerdoai-me, Senhor. Nao quero mais pecar.",
    "Invocacao ao Anjo da Guarda": "Anjo de Deus, que por Divina piedade,\\nsois minha guarda e protecao.\\nInspirai-me, Defendei-me, Dirigi-me, Governai-me, Protegei-me. Amem.",
    "O Anjo do Senhor": "O anjo do Senhor anunciou a Maria...\\nE Ela concebeu do Espirito Santo.\\n(Reza-se a Ave-Maria 1x)\\nEis aqui a Serva do Senhor. Faca-se em mim segundo a Tua Palavra.\\n(Reza-se a Ave-Maria 1x)\\nE o Verbo se fez carne. E habitou entre nos.\\n(Reza-se a Ave-Maria 1x)\\nOREMOS: Infundi Senhor, nos Vos suplicamos,\\na Vossa graca em nossas almas,\\npara que nos, pela Anunciacao do Anjo,\\nconhecamos a Encarnacao de Jesus Cristo Vosso Filho,\\ne pela Sua Paixao e Morte na Cruz,\\nsejamos conduzidos a gloria na ressurreicao.\\n(Reza-se o Gloria ao Pai 1x). Amem.",
    "Dons do Espirito Santo": "Espirito Santo, concedei-me o dom da sabedoria, a fim de que cada vez mais aprecie as coisas divinas e, abrasado pelo fogo do Vosso amor, prefira com alegria as coisas do ceu a tudo o que e mundano e me una para sempre a Cristo, sofrendo neste mundo por Seu amor.\nEspirito Santo, concedei-me o dom do entendimento, para que, iluminado pela luz celeste da Vossa graca, bem entenda as sublimes verdades da salvacao e da doutrina da santa religiao.\nEspirito Santo, concedei-me o dom do conselho, tao necessario nos melindrosos passos da vida, para que escolha sempre aquilo que mais Vos seja do agrado, siga em tudo Vossa divina graca e saiba socorrer meu proximo com bons conselhos.\nEspirito Santo, concedei-me o dom da fortaleza, para que despreze todo respeito humano, fuja do pecado, pratique a virtude do espirito, o desprezo, o prejuizo, as perseguicoes e a propria morte, antes de renegar por palavras e obras a Cristo.\nEspirito Santo, concedei-me o dom da ciencia, para que conheca cada vez mais minha propria miseria e fraqueza, a beleza da virtude e o valor inestimavel da alma e para que sempre veja claramente as ciladas do demonio, da carne, do mundo, a fim de as evitar.\nEspirito Santo, concedei-me o dom da piedade, que me tornara delicioso o trato e coloquio Convosco na oracao e me fara amar a Deus com intimo amor como a meu Pai, Maria Santissima e a todos os homens como a meus irmaos em Jesus Cristo.\nEspirito Santo, concedei-me o dom do temor de Deus, para que eu me lembre sempre, com suma reverencia e profundo respeito, da Vossa divina presenca, trema como os anjos diante da Vossa divina majestade e nada receie tanto como desagradar Vossos santos olhos!\nVinde, Espirito Santo, ficai comigo e derramai sobre mim Vossas divinas bencaos. Em nome de Jesus Cristo Nosso Senhor.\nAmem."

}

NOVENAS = {
    "Novena ao Sagrado Coração de Jesus": [
        "Senhor Jesus, Coração Sacratissimo, hoje venho a Vos com humildade e confianca. Que o Vossó amor inflame meu coração e me transforme em instrumento da Vossa paz. Amem.",
        "Sagrado Coração de Jesus, que tanto amais os homens, dai-me um coração semelhante ao Vosso, cheio de amor, misericórdia e bondade para com todos. Amem.",
        "Senhor, que o Vossó Coração aberto na Cruz sejá para mim fonte de graça e misericórdia. Lava-me do péçado e purifica-me. Amem.",
        "Coração de Jesus, Rei e centro de todos os coracoes, fazei que o Vossó Reino venha em mim, em minha família e em todo o mundo. Amem.",
        "Senhor Jesus, que prometestés paz as famílias consagradas ao Vossó Sagrado Coração, consagro hoje minha família a Vos. Sede o seu Rei e Senhor. Amem.",
        "Sagrado Coração de Jesus, consolai os que sofrem, fortalecei os que lutam e dai espéranca aos que desespéram. Que ninguem fique sem o Vossó amor. Amem.",
        "Senhor, pélo Vossó Coração traspassado, intercedei pélos que estão longe de Deus. Que Vossó amor os alcance e os traga de volta. Amem.",
        "Coração de Jesus, refugio dos péçadores, que eu nunca pérca a confianca na Vossa misericórdia. Sempre voltarei a Vos, arrepéndido e confiante. Amem.",
        "Sagrado Coração de Jesus, neste ultimo dia de novena, oféreco-Vos minha vida inteira. Que eu viva e morra no Vossó amor. Amem."
    ],
    "Novena a Nossa Senhora Aparecida": [
        "Nossa Senhora Aparecida, Rainha e Mãe do Brasil, hoje inicio esta novena com fé e espéranca. Intercedei por mim junto ao Vossó Filho Jesus. Amem.",
        "Mãe Aparecida, que vos mostrastés humilde e simplés como a imagem de barro, ensinai-me a simplicidade e a humildade no meu dia a dia. Amem.",
        "Nossa Senhora, que iluminastés as aguas escuras do Rio Paraiba com Vossa presenca, iluminai também os momentos escuros da minha vida. Amem.",
        "Mãe do Brasil, povo que tanto vos ama, intercedei por nossa patria. Que Deus abençoe esta terra e este povo. Amem.",
        "Nossa Senhora Aparecida, Mãe dos pobrés e dos simples, lembrai-vos dos que sofrem, dos doentes, dos abandonados. Cobri-os com Vossó manto. Amem.",
        "Mãe Aparecida, que por tantos seculos ouvistés os clamorés do povo brasileiro, ouvi também o meu clamor hoje. (Faca seu pédido com confianca). Amem.",
        "Nossa Senhora, que fostés encontrada pélos péscadorés e realizastés milagres, realizai também o milagre que tanto espéro, se for da Vontade de Deus. Amem.",
        "Mãe Aparecida, ensinai-me a rezar, a confiar, a amar a Deus sobre todas as coisas. Que eu nunca me afaste do Vossó manto protetor. Amem.",
        "Nossa Senhora Aparecida, neste ultimo dia de novena, renovo minha consagraçao a Vos. Sou vossó filho(a) para sempre. Protegei-me e levai-me a Jesus. Amem."
    ],
    "Novena ao Espírito Santo": [
        "Vem, Espírito Santo, enchei os coraçõés dos Vossos fieis e acendei nelés o fogo do Vossó amor. Dai-me a graça da sabedoria para conhecer a Deus. Amem.",
        "Espírito de Deus, dai-me o dom do entendimento, para que eu compreenda as verdadés da fé e as aplique em minha vida. Amem.",
        "Espírito Santo Paraclete, dai-me o dom do conselho, para que eu saiba sempre escolher o bem e evitar o mal em todas as situações. Amem.",
        "Vem, Espírito Santo, dai-me o dom da fortaleza para enfrentar com coragem as dificuldades, tentaçõés e sofrimentos da vida. Amem.",
        "Espírito de sabedoria e de ciencia, iluminai minha mente para que eu conheca cada vez mais a Deus e me aproxime Dele. Amem.",
        "Espírito Santo, dai-me o dom da piedade, para que eu ame a Deus como Pai e traté com bondade todos os meus irmãos. Amem.",
        "Vem, Espírito Santo, dai-me o dom do temor a Deus, para que eu nunca O ofénda e viva sempre em conformidade com a Sua Vontade. Amem.",
        "Espírito Santo, transformai-me em testemunha viva de Cristo. Que minha vida sejá um reflexo do Vossó amor ao mundo. Amem.",
        "Vem, Espírito Santo, no ultimo dia desta novena, vem com toda Vossa plenitude. Renovai em mim os dons recebidos no Batismo e na Crisma. Amem."
    ],
    "Novena a São Jose": [
        "São Jose, Pai adotivo de Jesus e esposó de Maria, intercedei por mim junto a Sagrada Familia. Ensinai-me a fidelidade e o trabalho honesto. Amem.",
        "Gloriosó São Jose, padroeiro dos trabalhadores, intercedei por todos que buscam trabalho digno e pélos que sofrem no trabalho. Amem.",
        "São Jose, modelo de obediencia a Deus, ensinai-me a confiar na Providencia Divina mesmo quando não entendo os caminhos de Deus. Amem.",
        "Gloriosó patriarca São Jose, protegei as famílias. Que cada lar sejá como Nazare: simples, trabalhador, cheio de amor e de Deus. Amem.",
        "São Jose, que guardastés Jesus e Maria em périgo, guardai também minha família de todo o mal, do péçado e do inimigo. Amem.",
        "Gloriosó São Jose, padroeiro da Igreja universal, intercedei pélo Papa, pélos bispos, pélos sacerdotés e por toda a Igreja. Amem.",
        "São Jose, que recebestés de Deus a missão de cuidar do Filho de Deus, ensinai-me a cumprir com amor a missão que Deus me confiou. Amem.",
        "Gloriosó São Jose, padroeiro de uma boa morte, acompanhai-me na hora de minha morte. Que eu morra em paz, na graça de Deus. Amem.",
        "São Jose, neste ultimo dia de novena, confio a Vos minha vida, minha família e meus projetos. Sede meu pai e meu protetor para sempre. Amem."
    ]
    ,
    "Novena das Maos Ensanguentadas de Jesus": [
        "Jesus, coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento.\n(Faca o seu pedido)\nSinto-me completamente sem forcas para prosseguir carregando as minhas cruzes.\nPreciso que a forca e o poder de Tuas maos, que suportaram a mais profunda dor ao serem pregadas na Cruz, me reergam e me curem agora.\nJesus nao peco somente por mim, mas tambem por todos aqueles que mais amo. Nos precisamos desesperadamente de cura, fisica e espiritual, atraves do toque consolador de Tuas maos ensanguentadas e imensamente poderosas. Eu reconheco, apesar de toda a minha limitacao e da infinidade dos meus pecados, que es Deus Onipotente e misericordioso para agir e realizar o impossivel.\nCom fe e total confianca posso dizer:\nMaos ensanguentadas de Jesus, maos feridas la na Cruz! Vem tocar em mim. Vem Senhor Jesus!\nAmem.",
        "Jesus, coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento.\n(Faca o seu pedido)\nSinto-me completamente sem forcas para prosseguir carregando as minhas cruzes.\nPreciso que a forca e o poder de Tuas maos, que suportaram a mais profunda dor ao serem pregadas na Cruz, me reergam e me curem agora.\nJesus nao peco somente por mim, mas tambem por todos aqueles que mais amo. Nos precisamos desesperadamente de cura, fisica e espiritual, atraves do toque consolador de Tuas maos ensanguentadas e imensamente poderosas. Eu reconheco, apesar de toda a minha limitacao e da infinidade dos meus pecados, que es Deus Onipotente e misericordioso para agir e realizar o impossivel.\nCom fe e total confianca posso dizer:\nMaos ensanguentadas de Jesus, maos feridas la na Cruz! Vem tocar em mim. Vem Senhor Jesus!\nAmem.",
        "Jesus, coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento.\n(Faca o seu pedido)\nSinto-me completamente sem forcas para prosseguir carregando as minhas cruzes.\nPreciso que a forca e o poder de Tuas maos, que suportaram a mais profunda dor ao serem pregadas na Cruz, me reergam e me curem agora.\nMaos ensanguentadas de Jesus, maos feridas la na Cruz! Vem tocar em mim. Vem Senhor Jesus!\nAmem.",
        "Jesus, coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento.\n(Faca o seu pedido)\nSinto-me completamente sem forcas para prosseguir carregando as minhas cruzes.\nPreciso que a forca e o poder de Tuas maos, que suportaram a mais profunda dor ao serem pregadas na Cruz, me reergam e me curem agora.\nMaos ensanguentadas de Jesus, maos feridas la na Cruz! Vem tocar em mim. Vem Senhor Jesus!\nAmem.",
        "Jesus, coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento.\n(Faca o seu pedido)\nSinto-me completamente sem forcas para prosseguir carregando as minhas cruzes.\nPreciso que a forca e o poder de Tuas maos, que suportaram a mais profunda dor ao serem pregadas na Cruz, me reergam e me curem agora.\nMaos ensanguentadas de Jesus, maos feridas la na Cruz! Vem tocar em mim. Vem Senhor Jesus!\nAmem.",
        "Jesus, coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento.\n(Faca o seu pedido)\nSinto-me completamente sem forcas para prosseguir carregando as minhas cruzes.\nPreciso que a forca e o poder de Tuas maos, que suportaram a mais profunda dor ao serem pregadas na Cruz, me reergam e me curem agora.\nMaos ensanguentadas de Jesus, maos feridas la na Cruz! Vem tocar em mim. Vem Senhor Jesus!\nAmem.",
        "Jesus, coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento.\n(Faca o seu pedido)\nSinto-me completamente sem forcas para prosseguir carregando as minhas cruzes.\nPreciso que a forca e o poder de Tuas maos, que suportaram a mais profunda dor ao serem pregadas na Cruz, me reergam e me curem agora.\nMaos ensanguentadas de Jesus, maos feridas la na Cruz! Vem tocar em mim. Vem Senhor Jesus!\nAmem.",
        "Jesus, coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento.\n(Faca o seu pedido)\nSinto-me completamente sem forcas para prosseguir carregando as minhas cruzes.\nPreciso que a forca e o poder de Tuas maos, que suportaram a mais profunda dor ao serem pregadas na Cruz, me reergam e me curem agora.\nMaos ensanguentadas de Jesus, maos feridas la na Cruz! Vem tocar em mim. Vem Senhor Jesus!\nAmem.",
        "Jesus, coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento.\nNeste ultimo dia de novena, com fe renovada, faco meu pedido e confio que Tuas maos poderosas, que venceram a morte na Cruz, realizam o impossivel em minha vida.\n(Faca o seu pedido)\nMaos ensanguentadas de Jesus, maos feridas la na Cruz! Vem tocar em mim. Vem Senhor Jesus!\nAmem.",
    ],
    "Novena contra a Depressao": [
        "Ato de Fe:\nEu creio Senhor que sois Deus Pai todo-poderoso, Criador do ceu e da terra. Eu creio em Jesus Cristo Salvador de todo genero humano. Eu creio no Divino Espirito Santo santificador.\nSenhor hoje pedimos a graca da libertacao da depressao por nos e por aqueles cujos nomes neste momento lembramos... (diga os nomes)\nEm nome de Jesus liberta-me Senhor da depressao.\nEm nome de Jesus liberta-me da angustia.\nEm nome de Jesus liberta-me da ansiedade.\nSenhor que o Teu poder libertador liberte o espirito da depressao retirando todas as amarras e todas as formas de manifestacao da angustia. Cure Senhor onde esse mal se instalou, arranque pela raiz esse problema, cure as lembrancas dolorosas, os traumas, ressentimentos e as marcas negativas.\nSenhor Deus, que a alegria transborde profundamente em meu ser. Com Teu poder e em nome de Jesus, refaca minha historia, meu passado e meu presente. Livra-me Senhor de todo o mal, e que nos momentos de solidao, de descaso e de rejeicao, eu seja curado e libertado na Tua presenca.\nEu renuncio no poder libertador de Nosso Senhor Jesus Cristo, ao medo, a incerteza, a desesperanca e me apego em Teu poder Senhor, em Tua graca, em Tua bencao.\nDai-me Senhor a graca da libertacao da depressao.\nDai-me Senhor a graca da libertacao da angustia.\nDai-me Senhor a graca da libertacao da ansiedade.\nAmem.",
        "Ato de Fe:\nEu creio Senhor que sois Deus Pai todo-poderoso, Criador do ceu e da terra. Eu creio em Jesus Cristo Salvador de todo genero humano. Eu creio no Divino Espirito Santo santificador.\nSenhor hoje pedimos a graca da libertacao da depressao por nos e por aqueles cujos nomes neste momento lembramos... (diga os nomes)\nEm nome de Jesus liberta-me Senhor da depressao.\nEm nome de Jesus liberta-me da angustia.\nEm nome de Jesus liberta-me da ansiedade.\nDai-me Senhor a graca da libertacao da depressao.\nDai-me Senhor a graca da libertacao da angustia.\nDai-me Senhor a graca da libertacao da ansiedade.\nAmem.",
        "Ato de Fe:\nEu creio Senhor que sois Deus Pai todo-poderoso, Criador do ceu e da terra. Eu creio em Jesus Cristo Salvador de todo genero humano. Eu creio no Divino Espirito Santo santificador.\nSenhor hoje pedimos a graca da libertacao da depressao por nos e por aqueles cujos nomes neste momento lembramos... (diga os nomes)\nEm nome de Jesus liberta-me Senhor da depressao.\nEm nome de Jesus liberta-me da angustia.\nEm nome de Jesus liberta-me da ansiedade.\nDai-me Senhor a graca da libertacao da depressao.\nDai-me Senhor a graca da libertacao da angustia.\nDai-me Senhor a graca da libertacao da ansiedade.\nAmem.",
        "Ato de Fe:\nEu creio Senhor que sois Deus Pai todo-poderoso, Criador do ceu e da terra. Eu creio em Jesus Cristo Salvador de todo genero humano. Eu creio no Divino Espirito Santo santificador.\nSenhor hoje pedimos a graca da libertacao da depressao por nos e por aqueles cujos nomes neste momento lembramos... (diga os nomes)\nEm nome de Jesus liberta-me Senhor da depressao.\nEm nome de Jesus liberta-me da angustia.\nEm nome de Jesus liberta-me da ansiedade.\nDai-me Senhor a graca da libertacao da depressao.\nDai-me Senhor a graca da libertacao da angustia.\nDai-me Senhor a graca da libertacao da ansiedade.\nAmem.",
        "Ato de Fe:\nEu creio Senhor que sois Deus Pai todo-poderoso, Criador do ceu e da terra. Eu creio em Jesus Cristo Salvador de todo genero humano. Eu creio no Divino Espirito Santo santificador.\nSenhor hoje pedimos a graca da libertacao da depressao por nos e por aqueles cujos nomes neste momento lembramos... (diga os nomes)\nEm nome de Jesus liberta-me Senhor da depressao.\nEm nome de Jesus liberta-me da angustia.\nEm nome de Jesus liberta-me da ansiedade.\nDai-me Senhor a graca da libertacao da depressao.\nDai-me Senhor a graca da libertacao da angustia.\nDai-me Senhor a graca da libertacao da ansiedade.\nAmem.",
        "Ato de Fe:\nEu creio Senhor que sois Deus Pai todo-poderoso, Criador do ceu e da terra. Eu creio em Jesus Cristo Salvador de todo genero humano. Eu creio no Divino Espirito Santo santificador.\nSenhor hoje pedimos a graca da libertacao da depressao por nos e por aqueles cujos nomes neste momento lembramos... (diga os nomes)\nEm nome de Jesus liberta-me Senhor da depressao.\nEm nome de Jesus liberta-me da angustia.\nEm nome de Jesus liberta-me da ansiedade.\nDai-me Senhor a graca da libertacao da depressao.\nDai-me Senhor a graca da libertacao da angustia.\nDai-me Senhor a graca da libertacao da ansiedade.\nAmem.",
        "Ato de Fe:\nEu creio Senhor que sois Deus Pai todo-poderoso, Criador do ceu e da terra. Eu creio em Jesus Cristo Salvador de todo genero humano. Eu creio no Divino Espirito Santo santificador.\nSenhor hoje pedimos a graca da libertacao da depressao por nos e por aqueles cujos nomes neste momento lembramos... (diga os nomes)\nEm nome de Jesus liberta-me Senhor da depressao.\nEm nome de Jesus liberta-me da angustia.\nEm nome de Jesus liberta-me da ansiedade.\nDai-me Senhor a graca da libertacao da depressao.\nDai-me Senhor a graca da libertacao da angustia.\nDai-me Senhor a graca da libertacao da ansiedade.\nAmem.",
        "Ato de Fe:\nEu creio Senhor que sois Deus Pai todo-poderoso, Criador do ceu e da terra. Eu creio em Jesus Cristo Salvador de todo genero humano. Eu creio no Divino Espirito Santo santificador.\nSenhor hoje pedimos a graca da libertacao da depressao por nos e por aqueles cujos nomes neste momento lembramos... (diga os nomes)\nEm nome de Jesus liberta-me Senhor da depressao.\nEm nome de Jesus liberta-me da angustia.\nEm nome de Jesus liberta-me da ansiedade.\nDai-me Senhor a graca da libertacao da depressao.\nDai-me Senhor a graca da libertacao da angustia.\nDai-me Senhor a graca da libertacao da ansiedade.\nAmem.",
        "Ato de Fe:\nEu creio Senhor que sois Deus Pai todo-poderoso, Criador do ceu e da terra. Eu creio em Jesus Cristo Salvador de todo genero humano. Eu creio no Divino Espirito Santo santificador.\nNeste ultimo dia de novena, pedimos com toda a fe a libertacao completa da depressao, da angustia e da ansiedade. (diga os nomes)\nEm nome de Jesus liberta-me Senhor da depressao.\nEm nome de Jesus liberta-me da angustia.\nEm nome de Jesus liberta-me da ansiedade.\nSenhor Deus, que a alegria transborde profundamente em meu ser. Com Teu poder e em nome de Jesus, refaca minha historia, meu passado e meu presente.\nDai-me Senhor a graca da libertacao da depressao.\nDai-me Senhor a graca da libertacao da angustia.\nDai-me Senhor a graca da libertacao da ansiedade.\nAmem.",
    ],
    "Em Deus Espero um Milagre": [
        "Jesus, pelos milagres realizados, obrigado Senhor, pelos que ainda nao vieram, minha hora vai chegar.\nMeu Jesus, em Vos deposito toda a minha confianca. Vos sabeis tudo, sois Senhor do Universo, sois o Rei dos reis.\nJesus, Vos fostes e pontifeces, andai, o morto reviveu, o leproso sarou. Confiando em Vosso poder e em Vossa misericordia, peco que facais esse milagre em minha vida. (Faca a graca)\nAmem.",
        "Divino Jesus, agradeco por tantas gracas alcancadas, tantas maravilhas que fazeis em minha vida. Confiando, que em Vos, a minha hora vai chegar, imploro esta graca com tanto fervor.\n(Repita o pedido com muita fe)\nJesus, eu tenho confianca em Vos. Vos peco, toca em meu coracao e aumenta a minha fe para que eu possa ver e testemunhar as maravilhas do Teu amor.\nAmem.",
        "Jesus, pelos milagres recebidos, obrigado Senhor; pelos que ainda nao recebi, minha hora vai chegar.\nSenhor, eu creio em Vosso poder.\nSenhor, eu creio na Vossa graca.\nSenhor, eu creio na Vossa promessa.\nEm Vos, Senhor, eu espero um milagre.\nEm Deus eu espero um milagre. (3x)\nAmem.",
        "Jesus, pelos milagres realizados, obrigado Senhor, pelos que ainda nao vieram, minha hora vai chegar.\n(Faca o seu pedido)\nSenhor, eu creio em Vosso poder.\nSenhor, eu creio na Vossa graca.\nSenhor, eu creio na Vossa promessa.\nEm Vos, Senhor, eu espero um milagre.\nEm Deus eu espero um milagre. (3x)\nAmem.",
        "Jesus, pelos milagres realizados, obrigado Senhor, pelos que ainda nao vieram, minha hora vai chegar.\n(Faca o seu pedido)\nSenhor, eu creio em Vosso poder.\nSenhor, eu creio na Vossa graca.\nSenhor, eu creio na Vossa promessa.\nEm Vos, Senhor, eu espero um milagre.\nEm Deus eu espero um milagre. (3x)\nAmem.",
        "Jesus, pelos milagres realizados, obrigado Senhor, pelos que ainda nao vieram, minha hora vai chegar.\n(Faca o seu pedido)\nSenhor, eu creio em Vosso poder.\nSenhor, eu creio na Vossa graca.\nSenhor, eu creio na Vossa promessa.\nEm Vos, Senhor, eu espero um milagre.\nEm Deus eu espero um milagre. (3x)\nAmem.",
        "Jesus, pelos milagres realizados, obrigado Senhor, pelos que ainda nao vieram, minha hora vai chegar.\n(Faca o seu pedido)\nSenhor, eu creio em Vosso poder.\nSenhor, eu creio na Vossa graca.\nSenhor, eu creio na Vossa promessa.\nEm Vos, Senhor, eu espero um milagre.\nEm Deus eu espero um milagre. (3x)\nAmem.",
        "Jesus, pelos milagres realizados, obrigado Senhor, pelos que ainda nao vieram, minha hora vai chegar.\n(Faca o seu pedido)\nSenhor, eu creio em Vosso poder.\nSenhor, eu creio na Vossa graca.\nSenhor, eu creio na Vossa promessa.\nEm Vos, Senhor, eu espero um milagre.\nEm Deus eu espero um milagre. (3x)\nAmem.",
        "Jesus, pelos milagres realizados, obrigado Senhor, pelos que ainda nao vieram, minha hora vai chegar.\nNeste ultimo dia de novena, com fe total, faco meu pedido e confio completamente em Vosso poder e amor.\n(Faca o seu pedido)\nSenhor, eu creio em Vosso poder.\nSenhor, eu creio na Vossa graca.\nSenhor, eu creio na Vossa promessa.\nEm Vos, Senhor, eu espero um milagre.\nEm Deus eu espero um milagre. (3x)\nAmem.",
    ],
    "Oficio de Nossa Senhora": [
        "MATINAS (Rezadas de madrugada)\nDeus vos salve Virgem, Filha de Deus Pai!\nDeus vos salve Virgem, Mae de Deus Filho!\nDeus vos salve Virgem, Esposa do Divino Espirito Santo!\nDeus vos salve Virgem, Templo e Sacrario da Santissima Trindade!\nAgora, labios meus, anunciai os grandes louvores da Virgem Mae de Deus.\n\nHINO\nDeus vos salve, Virgem, Senhora do mundo, Rainha dos Anjos, alegre Virgem, Estrela da manha. Deus vos salve, casta por dom, formosa e louca. Dai pressa Senhora, em favor do pecado, pois vos reconhece como defensora. Deus vos nomeou de toda a eternidade, para a Mae do Verbo. Ouvi, Mae de Deus, minha oracao. Toque Vosso peito os clamores meus.\n\nORASCAO\nSanta Maria, Rainha dos ceus, Mae de Nosso Senhor Jesus Cristo, que a nenhum pecador desamparais nem desprezais; alcancai-me de Vosso amado Filho o perdao de todos os meus pecados. Amem.\n\nSede em meu favor, Virgem soberana, livrai-me do inimigo com o Vosso valor. Gloria seja ao Pai, ao Filho e ao Amor tambem, que e um so Deus em tres Pessoas, agora e para sempre. Amem.",
        "PRIMA (Rezadas as 6h)\nSede em meu favor, etc.\nGloria seja ao Pai, etc.\n\nHINO\nDeus vos salve, mesa para Deus ornada, coluna sagrada, de grande firmeza; casa dedicada a Deus sempiterno, sempre preservada Virgem do pecado. Antes que nascida, foste, Virgem, Santa, no ventre ditoso de Ana concebida. Sois Mae criadora dos mortais viventes. Sois dos Santos porta, dos Anjos Senhora. Sois forte esquadrao contra o inimigo, refugio do cristao.\nOuvi, Mae de Deus, minha oracao.\nToque Vosso peito os clamores meus.\n\nOrasao: Santa Maria, Rainha dos ceus, etc. Amem.",
        "TERCA (Rezadas as 9h)\nSede em meu favor, etc.\nGloria seja ao Pai, etc.\n\nHINO\nDeus Vos salve, trono do grao Salomao, arca de concerto, velo de Gedeao; Iris do ceu clara, sarca de visao, favo de Sansao, florescente vara; a qual escolheu para ser Mae sua, e de Vos nasceu o Filho de Deus. Assim Vos livrou da culpa original, nenhum pecado ha em Vos sinal. Vos, que habitais la nessas alturas, e tendes Vosso Trono sobre as nuvens puras.\nOuvi, Mae de Deus, minha oracao.\nToque em Vosso peito os clamores meus.\n\nOrasao: Santa Maria, Rainha dos ceus, etc. Amem.",
        "SEXTA (Rezadas as 12h)\nSede em meu favor, etc.\nGloria seja ao Pai, etc.\n\nHINO\nDeus Vos salve, Virgem de trindade templo, alegria dos anjos, da pureza exemplo; que alegrais os tristes, com vossa clemencia, horto de deleite, palma da paciencia. Sois terra bendita e sacerdotal. Sois de castidade simbolo real. Cidade do Altissimo, porta oriental; sois a mesma graca, Virgem singular. Qual lirio cheiroso, entre espinhos duros, tal sois Vos, Senhora entre as criaturas.\nOuvi, Mae de Deus, minha oracao.\nToque em Vosso peito os clamores meus.\n\nOrasao: Santa Maria, Rainha dos ceus, etc. Amem.",
        "NONA (Rezadas as 15h)\nSede em meu favor, etc.\nGloria seja ao Pai, etc.\n\nHINO\nDeus vos salve, cidade de torres guarnecida de Deus, com que bem fortalecida. De santa castidade sempre armada. A mulher tao forte! Que Vos alcantastes o santo Davi. Do Egito o castelo, do qual nasceu do mundo o Salvador, Maria no-lo deu. Santissima minha companheira, nela nao ha macula sombra nenhuma.\nOuvi, Mae de Deus, minha oracao.\nToque em Vosso peito os clamores meus.\n\nOrasao: Santa Maria, Rainha dos ceus, etc. Amem.",
        "VESPERAS (Rezadas as 17h)\nSede em meu favor, etc.\nGloria seja ao Pai, etc.\n\nHINO\nDeus vos salve, relogio que, andando atrasado, serviu de sinal ao Verbo Encarnado. Para que o homem suba as sumas alturas, desce Deus dos ceus para as criaturas. Com os raios claros do Sol da Justica, resplandece a Virgem. Sois lirio formoso que cheiro respira entre os espinhos. Da serpente a ira Vos a quebrantais com o vosso poder. Os cegos errados Vos alumiais.\nOuvi, Mae de Deus, minha oracao.\nToque em Vosso peito os clamores meus.\n\nOrasao: Santa Maria, Rainha dos ceus, etc. Amem.",
        "COMPLETA (Oracao da Noite)\nRogai a Deus, Vos, Virgem dos corentes, que vos torneis em nos piadosa Mae.\nSede em meu favor, etc. Gloria seja ao Pai, etc.\n\nHINO\nDeus Vos salve, Virgem Imaculada, Rainha de clemencia estrelas coroada. Vos sobre os Anjos sois purificada de Deus. A Vossa direita estais de ouro ornada. Por Vos, Mae de amor, podemos ver a Deus nas alturas. Guia do mar e saude certa, e porta que estais para o dia aberta. Ouvi, Mae de Deus, minha oracao. Toque em Vosso peito os clamores meus.\n\nOrasao: Santa Maria, Rainha dos ceus, etc. Amem.\n\nOFERECIMENTO\nHumildes oferecemos a Vos, Virgem pia, estas oracoes. Que em Vossa guia, yades Vos adiante. E na agonia, Vos sejais a nossa guia. Amem.",
        "REPETICAO - Dia 8\nReze todas as horas do Oficio de Nossa Senhora: Matinas, Prima, Terca, Sexta, Nona, Vesperas e Completa.\nOferecendo cada hora como ato de amor e devolcao a Nossa Senhora.\n\nOuvi, Mae de Deus, minha oracao.\nToque em Vosso peito os clamores meus.\nAmem.",
        "REPETICAO - Dia 9 (ultimo dia)\nReze todas as horas do Oficio de Nossa Senhora, renovando sua consagracao.\n\nMaria, Rainha dos ceus e da terra, recebei este Oficio que vos oferecemos com amor e devolcao. Intercedei por nos junto a vosso Filho Jesus Cristo.\nOuvi, Mae de Deus, minha oracao.\nToque em Vosso peito os clamores meus.\nAmem.",
    ]

}
TERCOS = {
    "Misterios Gozosos (Segundas e Sabados)": [
        ("1 - Anunciação do anjo a Nossa Senhora", "Mãe da Divina Graca, dai-nós a virtude da total entrega, num sim sempre constante a Vontade de Deus Pai. Amem."),
        ("2 - Visita de Nossa Senhora a Santa Isabel", "Mãe amada, dai-nós a virtude de servir sempre, com amor, simplicidade e de louvarmos a Deus, como glorificastes, em Vossó Magnificat, ao nossó Pai e Criador, com todo coração. Amem."),
        ("3 - Nascimento de Jesus", "Mãe e Rainha nossa, dai-nós um coração humilde e acolhedor como a gruta de Belem, para que Jesus possa nascer e viver sempre dentro de nossó coração. Amem."),
        ("4 - Apresentação de Jesus no Templo", "Mãe nossa e Medianeira de todas as graças, apresentamos ao altar do Senhor, tudo o que somos e temos, nossa família, trabalho, lágrimas, sofrimentos e alegrias, para que o Senhor possa transformar em santidade o que e culpavel em nos. Amem."),
        ("5 - Perda e reencontro de Jesus no Templo", "Mãe amada, que não deixemos a fé, a presenca de Jesus Cristo em nossa vida. Concedei-nós também o espírito do apóstolado, não somente por palavras, mas sobretudo pélos testemunhos de nossa vida. Amem.")
    ],
    "Misterios Dolorosos (Tercas e Sextas)": [
        ("1 - Agonia de Jesus no Horto das Oliveiras", "Senhor, que sofrestés a dor profunda da agonia, sendo inocente e o mais santo entre todos os homens, concedei-nós a Vossa força em nossas dorés e que saibamos pagar sempre o mal com o bem. Amem."),
        ("2 - Flagelação de Jesus", "Senhor, pérdoai-me por Vos flagelar quando péco contra meus irmãos, quando não cumpro os Mandamentos, quando me esqueco do quanto sofrestés por me amar e desejar minha salvação. Dai-me um coração novo, fazei de mim uma nova criatura. Amem."),
        ("3 - Jesus e coroado de espinhos", "Senhor, livrai-nós das aflicoés mentais, traumas, pénsamentos maus que temos; dai-nós cura interior para que possamos ser instrumentos muito mais eficazés da Vossa Vontade. Amem."),
        ("4 - Jesus carregando a Cruz", "Senhor, Vos que carregastés uma cruz tão pésada, rumo ao Calvario, sabendo o quanto haverieis de sofrer por meus péçados, fazei com que eu carregue todo fardo de meus dias com amor, paciencia e espéranca. E, que oférecendo tudo pélos meus péçados, pélas almas que sofrem no purgatorio, pélos que estejam sofrendo no mundo inteiro, jamais esbraveje e sim Vos louve em todo o tempo. Amem."),
        ("5 - Crucificação de Jesus", "Senhor, Vos que do alto da cruz pédistes, em Vossó Santíssimo amor, que o Pai pérdoasse a Vossos algozes, por que não sabiam o que faziam, dai-me o dom do mais pérféito pérdao. Dai-me a capacidade de amar e pérdoar com pérféicao e rezar por todos aquelés que me pérsigam ou facam o mal contra mim. Amem.")
    ],
    "Misterios Gloriosos (Quartas e Domingos)": [
        ("1 - A Ressurreição de Jesus", "Senhor, Vos que gloriosamente ressuscitastes, vencendo a morte, glorificado pélo Pai, concedei-nós a graça de crer em santidade, segundo a Vossa Vontade, para que um dia possa estar convosco na Gloria eterna. Amem."),
        ("2 - A Ascensao de Jesus aos Ceus", "Senhor, que cada dia de minha vida se torne um passó na ascensao a Vos. Que nada me faca retroceder no caminho em minha ascese. Quero viver em conformidade a Vossa Santíssima Vontade hoje e sempre. Amem."),
        ("3 - A Vinda do Espírito Santo (Pentecostes)", "Gloriosó Jesus, que enviastés o Espírito Santo sobre os apóstolos, antés ignorantés e medrosos, tornando-os destemidos, vem sobre mim e sobre a humanidade inteira, a fim de que pélo mesmo Espírito, possamos ser salvos e testemunhas do Vossó santo amor. Amem."),
        ("4 - A Assunção de Nossa Senhora aos Ceus", "Mãe de Misericórdia, após terdés sofrido as dorés das angustias, paixao e morte de Vossó divinissimo Filho, concedei-nós a graça de olhar a tudo com o Vossó olhar, amar com Vossó coração, passar pélos sofrimentos com resignação e coragem, guiados pélá fé e pélo amor que temos em Vos. Amem."),
        ("5 - A Coroação de Nossa Senhora como Rainha dos Ceus", "Mãe e Rainha nossa, revestindo-nós com Vossas santas virtudés de obediente e boa maternal bondade, a fim de que possamos atingir esta coroa de Vossa santidade. Depositamos neste altar de meu amor e devocao a Vossos santíssimos pés, com total confianca a Vossa maternal e constante protecao. Amem.")
    ],
    "Misterios Luminosos (Somente as quintas)": [
        ("1 - Batismo de Jesus no Jordao", "Senhor, lavai minha alma de todo péçado e rancores, ressentimentos passados. Vinde sobre mim, com Vossó Espírito Santo. Amem."),
        ("2 - Auto-revelação de Jesus nas Bodas de Cana", "Senhor, assim como transformastés a agua em vinho, por amor a Vossos filhos, transformai tudo o que impéde de Vos causar alegria. Transformai o meu coração no Vossó coração. A nossa Mãe Santíssima, advogada dos pobrés péçadorés que somos, péco que interceda junto a Deus, por mim e por toda a humanidade. Amem."),
        ("3 - Jesus anuncia o Reino de Deus com o convite a conversão", "Senhor, dirijo-me a Vos para, com total confianca e humildade, reconhecer minhas culpas e pédir-Vos pérdao. Converte-me inteiramente, a fim de que eu possa ser instrumento de conversão para muitos de Vossos filhos. Amem."),
        ("4 - Transfiguração de Jesus", "Senhor, que minha vida sejá vivida como no Monte Tabor, catasiada com Vossos prodigios e santidade. Reluz em minha face o brilho da Vossa Face e concede-me a graça de viver unicamente para Vos, em todos os momentos de minha vida. Amem."),
        ("5 - Instituicao da Eucaristia", "Senhor, eu Vos dou graças por terdés pérmanecido entre nos, em espécial na Santa Eucaristia. Vos Dou graças pélos sacerdotes, pois somente por elés pode ocorrer o sublime milagre da Transfiguração. Fazei descer o Espírito Santo sobre os sacerdotés do mundo inteiro, sobre todo o clero. Amem.")
    ],
    "Terco da Batalha": [
        ("Inicio", "Credo, Pai Nosso, Ave Maria 3x."),
        ("Nas contas grandes", "Deus do ceu, me de forças. Jesus Cristo me de o poder de vencer. Nossa Senhora me de coragem para me defénder. Sem morrer, sem enlouquecer, serei militante até o fim. Deus pode, Deus quer; esta batalha eu hei de vencer."),
        ("Nas contas péquenas", "Eu hei de vencer."),
        ("No final", "Salve Rainha. Mãe de Jesus e nossa Mãe, abençoa-nós e ouvi nossos rogos. A vitória e nossa pélo sangue de Jesus!")
    ],
    "Terco de São Bento": [
        ("Inicio", "Em nome do Pai, do Filho e do Espírito Santo. Amem. Vinde Espírito Santo, enchei nós coraçõés dos Vossos fieis e acendei nelés o fogo do Vossó Amor. Enviai o Vossó Espírito e tudo sera criado e renovai a face da terra. O Deus Santo, faze que apreciemos, chamando-nós sempre segundo o mesmo Espírito e governemos a face de Vossó Santo Senhor Nosso. Amem."),
        ("Credo e Pai Nosso + Oração Inicial", "Recite o Credo e um Pai Nosso. ORACAO INICIAL: O Gloriosó São Bento que sempre demonstrou compromissó com os seus afazeres, atendendo a Vossa chamada a paz e a tranquilidade; que em nossas famílias cure a paz e a tranquilidade, que se afastem todas as desgragas, junto corporais como espirituais, espécialmente o péçado. Alcancai São Bento, do Senhor Deus Onipotente, a graça que necessitamos."),
        ("Nas contas do Pai Nosso", "A Cruz Sagrada sejá a minha luz, não sejá o dragao o meu guia. Retira-te, satanas! Nunca me aconselhés coisas vas. E mau o que tu me oféreces, bebe tu mesmo o teu veneno! São Bento dai-nós a graça de que, ao terminar nossa vida neste vale de lágrimas, possamos ir louvar a Deus convosco no Paraiso."),
        ("Nas contas da Ave Maria", "São Bento, Vos intercedei por nos, libertai-nós do inveja. Sede Vos nossa libertador do mal, libertai-nós do péçado!"),
        ("Ao final", "Em nome do Pai, do Filho e do Espírito Santo. Amem.")
    ],
    "Terco do Louvor": [
        ("Como rezar", "O Terco do Louvor pode ser rezado em qualquer ocasiao ou lugar, usando um Rosario comum. Você rezara nas contas maiores, onde se reza o Pai Nosso, a seguinte oração: Senhor, abri meus labios a fim de que minha boca anuncie Vossos louvorés (cf. Sl 50,17)"),
        ("Nas contas menorés (10 Ave Marias)", "Jesus, te louvo e te bendigo... (Colocando aqui o seu motivo de louvor). Por exemplo: pélo meu marido(a), pélá minha esposa, pélo meu filho(a), pélá minha saúde, por minha situação, pélo meu emprego, pélá minha vida, pélo meu paroco, pélá minha família. Você pode acrescentar inumeras outras intencoes, rezando o Terco inteiro ou uma intencao em cada dezena."),
        ("Finalizando cada dezena", "Gloria ao Pai, ao Filho e ao Espírito Santo. Como era no principio, agora e sempre. Amem.")
    ],
    "Terco da Paixao": [
        ("No principio", "Pai Nosso, Ave Maria 3x."),
        ("Nas contas grandes", "Divino, porque da Vossa Paixao e Morte..."),
        ("Nas contas péquenas", "...pélá misericórdia de nós e do mundo inteiro."),
        ("Ao final do Terco, reze 3 vezes", "Tende piedade de nós e do mundo inteiro."),
        ("Encerramento", "Deus Imortal, tende piedade de nós e do mundo inteiro. Amem.")
    ],
    "Terco da Libertação": [
        ("Apresentação", "No principio e ação: Se Jesus me liberta, sou verdadeiramente livre! Nas contas grandés e ação: Se Jesus me liberta, liverta-me! Observação: O Terco pode ser rezado por você, sua família, e por outras péssoas."),
        ("Em cada dezena - nas contas grandes", "Chagas abertas, coração férido, o sangue de Cristo esta entre (poe-se a intencao) e o périgo."),
        ("Nas contas péquenas", "Jesus, pélas chagas da Vossa coração férido, o sangue de Cristo esta entre (poe-se a intencao) e o périgo. Jesus, pélas chagas da Vossa coração férido liberte (poe a péssoa ou a intencao)."),
        ("Quinta dezena - Oremos", "Jesus, o Senhor carregou todos as nossas dorés e enférmidades, carregou os nossos sofrimentos, pélo Seu sangue redentor, liberta-nós do mal, liberta-nós do péçado. Amem."),
        ("Encerramento", "Deus da misericórdia, do amor, medo, falta de pérdao, intrigas, brigas, discordias, ciume, divisao e reserva em nós liberta-nos. Saúde desuniao, falta de fé, da espéranca e da caridade. Amem.")
    ],
    "Terco do Sagrado Coração de Jesus": [
        ("Inicio", "No principio: Credo, Pai Nosso, Ave Maria 3x, Gloria ao Pai. Sagrado Coração, fonte do amor, templo de Deus, amado Jesus, Coração amante dos homens, Coração amantissimo de Jesus, Coração obediente, humilde e brando, Coração paciente e misericordioso, Coração delicia de todos os Santos, Coração desejosó da nossa salvação, Coração fonte de toda a santidade."),
        ("Nas contas grandes", "Sagrado Coração de Jesus, tende piedade de nos."),
        ("Nas contas péquenas", "Sagrado Coração de Jesus, eu vos amo."),
        ("Graca a alcancar", "Peca a graça que necessita. Em Vos eu confio. Amem."),
        ("Encerramento", "Sagrado Coração de Jesus, em Vos eu confio. Amem.")
    ],
    "Terco da Vitória pélas Chagas de Jesus": [
        ("Abertura", "Cura-me, Senhor Jesus, Jesus coloca Tuas maos benditas, ensanguentadas, chagadas e abertas sobre mim neste momento. Tu podés curar e foi de Tuas maos que supéramos o mais grande dos malés - foram pregadas na cruz. Maos ensanguentadas de Jesus, maos féridas (poe-se a intencao), vem tocar em mim, vem, Senhor Jesus, vem todas, vem. Reza-se um Pai Nosso, Uma Ave Maria e o Credo."),
        ("Em cada dezena - nas contas grandes", "Chagas abertas, coração férido, o sangue de Cristo esta entre (poe-se a intencao) e o périgo."),
        ("Nas contas péquenas", "Jesus, pélas chagas da Vossa coração férido, o sangue de Cristo esta entre (poe-se a intencao) e o périgo. Jesus, pélas chagas da Vossa coração férido liberte (poe a péssoa ou a intencao)."),
        ("Quinta dezena - Oremos", "Jesus, o Senhor sobre as nossas dorés e enférmidades, carregou os nossos sofrimentos, pélo Seu sangue redentor, liberta-nós do nossó corpo, por todas as chagas do Seu corpo, por todas as chagas dos Seus pés liberte (poe a péssoa ou a intencao)."),
        ("Encerramento", "Jesus, o Senhor carregou todos as nossas dorés e enférmidades, pélo Seu sangue redentor, liberta-nós do mal, liberta-nós do péçado. Amem.")
    ],
    "Terco pélos Filhos": [
        ("Inicio", "Em nome do Pai, do filho, do Espírito Santo, amem! Creio em Deus Pai... Pai Nosso que estais no ceu... Ave Maria (3 vezes)."),
        ("Para iniciar", "Abro meu coração, deixo o Espírito Santo entrar. Peco pra Ele mudar toda a minha situação..."),
        ("Nas Contas Maiores", "Quero de joelhos ver meus filhos de pé! Deus me sustenta e aumenta a minha fé!"),
        ("Nas Contas Pequenas", "Deus, mantenha meu filho de pé! (10 vezes)"),
        ("Para encerrar", "Deus pode tudo, tudo, tudo! (3 vezes)")
    ],
    "Terco do Agradecimento": [
        ("Abertura", "Obrigado Jesus, por mais um dia de vida. Peco-te Senhor que me restaure, me cure, me liberte e me torne um(a) filho(a) obediente e grato e que eu possa a cada minuto Te agradecer por tudo."),
        ("Nas contas", "Obrigado Senhor pélá minha vida. Obrigado Senhor pélá natureza. Obrigado Senhor pélo pao de cada dia. Obrigado Senhor por... (faca seu agradecimento)"),
        ("Encerramento", "Gloria ao Pai, ao Filho e ao Espírito Santo. Como era no principio, agora e sempre. Amem.")
    ]
}

COMO_REZAR_TERCO = """Como rezar o Terco:

1. Comece com o Credo (Creio em Deus Pai)
2. Reze 1 Pai Nosso
3. Reze 3 Ave Marias (pelas virtudes de fé, espéranca e caridade)
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
                  ("aba_chat", "chat"), ("oracao_aberta", None), ("terco_aberto", None), ("terco_misterio", None), ("novena_aberta", None), ("novena_dia", None)]:
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
        if st.button("📖 Liturgia do Dia", use_container_width=True, key="btn_liturgia"):
            st.session_state.aba_chat = "liturgia"
            st.rerun()
        if st.button("📅 Calendario Liturgico", use_container_width=True, key="btn_calendario"):
            st.session_state.aba_chat = "calendario"
            st.rerun()
        if st.button("⭐ Santo do Dia", use_container_width=True, key="btn_santo"):
            st.session_state.aba_chat = "santo"
            st.rerun()
        if st.button("🕯️ Novenas", use_container_width=True, key="btn_novenas"):
            st.session_state.aba_chat = "novenas"
            st.session_state.novena_aberta = None
            st.session_state.novena_dia = None
            st.rerun()
        if st.button("📖 Catecismo", use_container_width=True, key="btn_catecismo"):
            st.session_state.aba_chat = "catecismo"
            st.rerun()

        st.markdown("<hr style='border-color:#3e3e3e;margin:0.8rem 0;'>", unsafe_allow_html=True)

        # ── SOBRE / DOACOES ──
        st.markdown("<p style='color:#c8a96e;font-weight:700;margin:0.3rem 0;'>ℹ️ SOBRE</p>", unsafe_allow_html=True)
        if st.button("⭐ Creditos", use_container_width=True, key="btn_creditos"):
            st.session_state.aba_chat = "creditos"
            st.rerun()
        if st.button("💛 Doações", use_container_width=True, key="btn_doacoes"):
            st.session_state.aba_chat = "doacoes"
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
            for nome_oração in ORACOES:
                if st.button(f"🙏 {nome_oração}", use_container_width=True, key=f"o_{nome_oração}"):
                    st.session_state.oracao_aberta = nome_oração
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
                    if st.button("Proximo ->", use_container_width=True):
                        st.session_state.terco_misterio += 1
                        st.rerun()
                else:
                    if st.button("✅ Concluido", use_container_width=True):
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
            if st.button("▶️ Comecar os Misterios", use_container_width=True):
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

    # ── ABA SANTO DO DIA ──
    if st.session_state.aba_chat == "santo":
        st.markdown("<br>", unsafe_allow_html=True)
        from datetime import date
        import requests as req
        hoje = date.today()
        try:
            r = req.get(f"https://www.santosdomundo.com.br/api/santos?mes={hoje.month}&dia={hoje.day}", timeout=8)
            data = r.json()
            if data and isinstance(data, list):
                santos = data
            else:
                santos = []
        except:
            santos = []

        # Fallback simples por data
        SANTOS_FIXOS = {
            (1,1):"Maria Santíssima, Mãe de Deus",(1,2):"Santos Basilio Magno e Gregório Nazianzeno",(1,3):"Santíssimo Nome de Jesus",(1,4):"Santa Isabel Ana Seton",(1,5):"São João Neumann",(1,6):"Epifania do Senhor",(1,7):"São Raimundo de Peñafort",(1,8):"São Severino",(1,9):"São Adriano",(1,10):"São Guilherme",(1,11):"São Teodósio",(1,12):"São Taciano",(1,13):"Santo Hilário de Poitiers",(1,14):"Santo Eufrasio",(1,15):"Santo Antônio Abade",(1,16):"São Berno",(1,17):"Santo Antonio do Egito",(1,18):"Santa Prisca",(1,19):"São Mario e companheiros",(1,20):"Santos Fabiano e Sebastiao",(1,21):"Santa Inês",(1,22):"Santos Vicente e Anastasio",(1,23):"São Ildefonso",(1,24):"São Francisco de Sales",(1,25):"Conversão de São Paulo",(1,26):"Santos Timóteo e Tito",(1,27):"Santa Angela Merici",(1,28):"Santo Tomás de Aquino",(1,29):"São Gildas",(1,30):"Santa Martina",(1,31):"São João Bosco",
            (2,1):"São Inácio de Antioquia",(2,2):"Apresentação do Senhor",(2,3):"São Biagio",(2,4):"São José de Leonessa",(2,5):"Santa Ágata",(2,6):"Santos Paulo Miki e companheiros",(2,7):"São Colette",(2,8):"Santo Jerônimo Emiliani",(2,9):"Santa Apolônia",(2,10):"Santa Escolástica",(2,11):"Nossa Senhora de Lourdes",(2,12):"São Eulalia",(2,13):"São Benigno",(2,14):"Santos Cirilo e Metodio",(2,15):"São Claudio",(2,16):"São Onesimo",(2,17):"Sete Santos Fundadores dos Servitas",(2,18):"São Simeão",(2,19):"São Barbato",(2,20):"São Eucario",(2,21):"São Damiao",(2,22):"Cátedra de São Pedro",(2,23):"São Policarpo",(2,24):"São Etelberto",(2,25):"São Cesario",(2,26):"Santa Paula Montal",(2,27):"São Gabriel da Virgem das Dores",(2,28):"São Romano",
            (3,1):"São Álvaro",(3,2):"São Carlos o Bom",(3,3):"Santa Cunegundes",(3,4):"São Casimiro",(3,5):"São Adriano",(3,6):"São Colette",(3,7):"Santas Perpétua e Felicidade",(3,8):"São João de Deus",(3,9):"Santa Francisca Romana",(3,10):"São Simplício",(3,11):"São Eulógio",(3,12):"São Gregório Magno",(3,13):"Santa Eufrásia",(3,14):"Santa Matilde",(3,15):"São Lourenço de Brindisi",(3,16):"São Heriberto",(3,17):"Santo Patrício",(3,18):"São Cirilo de Jerusalém",(3,19):"São José, Esposo de Maria",(3,20):"Santa Claudia",(3,21):"Santo Benedito",(3,22):"São Epafrodito",(3,23):"São Turibio de Mogrovejo",(3,24):"São Oscar",(3,25):"Anunciação do Senhor",(3,26):"São Cástulo",(3,27):"São Ruperto",(3,28):"São Sixto III",(3,29):"São Bertoldo",(3,30):"São João Clímaco",(3,31):"São Benjamim",
            (4,1):"São Hugo de Grenoble",(4,2):"São Francisco de Paula",(4,3):"São Ricardo",(4,4):"Santo Isidoro de Sevilha",(4,5):"São Vicente Férrer",(4,6):"Santo Celestino I",(4,7):"São João Batista de La Salle",(4,8):"Santo Alberto",(4,9):"Santa Maria Cleofass",(4,10):"São Miguel de los Santos",(4,11):"São Estanislau",(4,12):"São Julio I",(4,13):"Santo Hermenegildo",(4,14):"Santos Tibúrcio e Valeriano",(4,15):"Santa Anastasia",(4,16):"Santa Bernadete",(4,17):"Santo Aniceto",(4,18):"São Eleutério",(4,19):"São Leao IX",(4,20):"Santa Inês de Montepulciano",(4,21):"Santo Anselmo",(4,22):"São Sótero e Caio",(4,23):"São Jorge",(4,24):"São Fidel de Sigmaringa",(4,25):"São Marcos Evangelista",(4,26):"Nossa Senhora do Bom Conselho",(4,27):"Santo Pedro Canísio",(4,28):"São Pedro Chanel",(4,29):"Santa Catarina de Siena",(4,30):"São Pio V",
            (5,1):"São Jose Operario",(5,2):"São Atanásio",(5,3):"Santos Filipe e Tiago",(5,4):"Santa Mônica",(5,5):"Santo Ângelo",(5,6):"São Domitila",(5,7):"Santa Flavia Domitila",(5,8):"Aparição de São Miguel Arcanjo",(5,9):"São Gregório Nazianzeno",(5,10):"São Antonino",(5,11):"Santos Inacio e Epimaco",(5,12):"Santos Nereu e Aquileu",(5,13):"Nossa Senhora de Fátima",(5,14):"São Matias",(5,15):"São Isidoro Lavrador",(5,16):"São Simão Stock",(5,17):"São Pascoal Bailão",(5,18):"São João I",(5,19):"São Pedro Celestino",(5,20):"São Bernardino de Siena",(5,21):"Santa Crisantema",(5,22):"Santa Rita de Cássia",(5,23):"São Guilherme de Rochester",(5,24):"Santa Maria Auxiliadora",(5,25):"Santo Gregório VII",(5,26):"São Filipe Neri",(5,27):"São Agostinho de Cantuária",(5,28):"Santo Emilio",(5,29):"Santa Bona",(5,30):"Santa Joana d'Arc",(5,31):"Visitação de Nossa Senhora",
            (6,1):"Santo Justino",(6,2):"Santos Marcelino e Pedro",(6,3):"Santos Carlos Lwanga e companheiros",(6,4):"Santa Saturnina",(6,5):"São Bonifácio",(6,6):"São Norberto",(6,7):"Santa Ana dos Anjos",(6,8):"São Medardo",(6,9):"Santos Primo e Feliciano",(6,10):"Santa Oliva",(6,11):"São Barnabe",(6,12):"São Onofre",(6,13):"Santo Antônio de Lisboa",(6,14):"Santo Elias",(6,15):"Santos Vito e Modesto",(6,16):"São Bento José Labre",(6,17):"São Gregório Barbarigo",(6,18):"São Marcos e Marceliano",(6,19):"São Romualdo",(6,20):"Santo Silvério",(6,21):"São Luís Gonzaga",(6,22):"São Paulino de Nola",(6,23):"São José Cafasso",(6,24):"Natividade de São João Batista",(6,25):"São Guilherme",(6,26):"Santos João e Paulo",(6,27):"Nossa Senhora do Perpétuo Socorro",(6,28):"São Ireneu",(6,29):"Santos Pedro e Paulo",(6,30):"Primeiros Martires de Roma",
            (7,1):"São Junipero Serra",(7,2):"Visitação de Nossa Senhora",(7,3):"São Tomás Apóstolo",(7,4):"Santa Isabel de Portugal",(7,5):"Santo Antônio Zaccaria",(7,6):"Santa Maria Goretti",(7,7):"São Panteno",(7,8):"Santa Aquila",(7,9):"Santos Agostinho Zhao Rong e companheiros",(7,10):"Santos Sete Irmaos",(7,11):"São Benedito",(7,12):"São João Gualberto",(7,13):"São Henrique",(7,14):"São Camilo de Lellis",(7,15):"São Boaventura",(7,16):"Nossa Senhora do Carmo",(7,17):"Santo Aleixo",(7,18):"Santa Sinforosa",(7,19):"Santa Macrina",(7,20):"São Elias Profeta",(7,21):"São Lourenço de Brindisi",(7,22):"Santa Maria Madalena",(7,23):"Santa Brígida",(7,24):"São Xisto II",(7,25):"São Tiago Apóstolo",(7,26):"Santos Joaquim e Ana",(7,27):"Santa Natália",(7,28):"Santo Inocêncio I",(7,29):"Santa Marta",(7,30):"Santos Abdon e Sennen",(7,31):"Santo Inácio de Loyola",
            (8,1):"Santo Afonso Maria de Ligório",(8,2):"Santo Eusébio de Vercelli",(8,3):"Santo Estêvão I",(8,4):"Santo João Maria Vianney",(8,5):"Dedicação da Basílica de Santa Maria Maior",(8,6):"Transfiguração do Senhor",(8,7):"São Caetano",(8,8):"São Domingos",(8,9):"São Romano",(8,10):"São Lourenço",(8,11):"Santa Clara de Assis",(8,12):"Santa Joana Francisca de Chantal",(8,13):"Santos Hipólito e Cassiano",(8,14):"São Maximiliano Maria Kolbe",(8,15):"Assunção de Nossa Senhora",(8,16):"Santo Estêvão da Hungria",(8,17):"Santa Joana",(8,18):"Santa Helena",(8,19):"São João Eudes",(8,20):"São Bernardo de Claraval",(8,21):"São Pio X",(8,22):"Maria Rainha",(8,23):"Santa Rosa de Lima",(8,24):"São Bartolomeu Apóstolo",(8,25):"São Luís IX",(8,26):"Santa Teresa de Jesus Jornet",(8,27):"Santa Mônica",(8,28):"Santo Agostinho",(8,29):"Martírio de São João Batista",(8,30):"Santo Félix e Adaucto",(8,31):"Santo Raimundo Nonato",
            (9,1):"Santo Egídio",(9,2):"São Estêvão da Hungria",(9,3):"São Gregório Magno",(9,4):"Santa Rosália",(9,5):"São Lourenço Justiniano",(9,6):"São Eleutário",(9,7):"Santa Regina",(9,8):"Natividade de Nossa Senhora",(9,9):"Santo Pedro Claver",(9,10):"Santos Protásio e Gervásio",(9,11):"São Proto",(9,12):"Santíssimo Nome de Maria",(9,13):"São João Crisóstomo",(9,14):"Exaltação da Santa Cruz",(9,15):"Nossa Senhora das Dores",(9,16):"Santos Cornélio e Cipriano",(9,17):"Santa Hildegarda",(9,18):"Santa Sofia",(9,19):"Santos Januário e companheiros",(9,20):"Santos André Kim e companheiros",(9,21):"São Mateus",(9,22):"São Maurício",(9,23):"São Pio de Pietrelcina - Padre Pio",(9,24):"Nossa Senhora das Mercês",(9,25):"Santo Cleofas",(9,26):"Santos Cosme e Damião",(9,27):"São Vicente de Paulo",(9,28):"São Venceslau",(9,29):"Santos Miguel, Gabriel e Rafael",(9,30):"São Jerônimo",
            (10,1):"Santa Teresinha do Menino Jesus",(10,2):"Santos Anjos da Guarda",(10,3):"São Geraldo",(10,4):"São Francisco de Assis",(10,5):"Santa Faustina Kowalska",(10,6):"São Bruno",(10,7):"Nossa Senhora do Rosário",(10,8):"Santa Brígida",(10,9):"São Dionísio e companheiros",(10,10):"São Luís Bertrão",(10,11):"São Filipe Diacono",(10,12):"Nossa Senhora Aparecida",(10,13):"São Eduardo",(10,14):"São Calisto I",(10,15):"Santa Teresa de Ávila",(10,16):"Santa Edwiges",(10,17):"Santo Inácio de Antioquia",(10,18):"São Lucas Evangelista",(10,19):"Santos João de Brébeuf e companheiros",(10,20):"Santo João Cantius",(10,21):"Santa Úrsula",(10,22):"São João Paulo II",(10,23):"São João de Capestrano",(10,24):"São Antônio Maria Claret",(10,25):"Santos Crispim e Crispiniano",(10,26):"São Evaristo",(10,27):"São Frumentino",(10,28):"Santos Simão e Judas",(10,29):"Santa Ermelinda",(10,30):"São Zenóbio",(10,31):"Santa Lucíola",
            (11,1):"Todos os Santos",(11,2):"Todos os Fiéis Defuntos",(11,3):"São Martinho de Porres",(11,4):"São Carlos Borromeu",(11,5):"São Zacarias",(11,6):"São Leonardo",(11,7):"Santa Ernesta",(11,8):"São Deusdedit",(11,9):"Dedicação da Basílica de São João de Latrão",(11,10):"São Leão Magno",(11,11):"São Martinho de Tours",(11,12):"São Josafá",(11,13):"São Estanislau Kostka",(11,14):"São Lourenço O Iluminador",(11,15):"São Alberto Magno",(11,16):"Santa Gertrudes",(11,17):"Santa Isabel da Hungria",(11,18):"Dedicação das Basílicas de São Pedro e São Paulo",(11,19):"Santa Matilde",(11,20):"São Edmundo",(11,21):"Apresentação de Nossa Senhora",(11,22):"Santa Cecília",(11,23):"São Clemente I",(11,24):"Santos André Dũng-Lạc e companheiros",(11,25):"Santa Catarina de Alexandria",(11,26):"São Silvestre Gozzolini",(11,27):"São Virgílio",(11,28):"Santo Antônio de Amandola",(11,29):"São Saturnino",(11,30):"São André Apóstolo",
            (12,1):"São Elói",(12,2):"Santa Bibiana",(12,3):"São Francisco Xavier",(12,4):"Santa Bárbara",(12,5):"São Sabas",(12,6):"São Nicolau",(12,7):"Santo Ambrósio",(12,8):"Imaculada Conceição de Maria",(12,9):"Santa Leocádia",(12,10):"Nossa Senhora de Loreto",(12,11):"São Dâmasó I",(12,12):"Nossa Senhora de Guadalupe",(12,13):"Santa Lúcia",(12,14):"São João da Cruz",(12,15):"Santo Alberto de Jerusalém",(12,16):"Santa Adelaide",(12,17):"Santo Lázaro",(12,18):"Nossa Senhora da Esperanca",(12,19):"São Urbano V",(12,20):"Santo Domingo de Silos",(12,21):"São Pedro Canísio",(12,22):"Santa Francisca Cabrini",(12,23):"São João de Kety",(12,24):"Vigília do Natal",(12,25):"Natividade de Nosso Senhor Jesus Cristo",(12,26):"Santo Estêvão",(12,27):"São João Apóstolo",(12,28):"Santos Inocentes",(12,29):"Santo Tomás Becket",(12,30):"Santa Sabina",(12,31):"São Silvestre I"
        }
        santo_nome = SANTOS_FIXOS.get((hoje.month, hoje.day), "Santo(a) do dia")
        meses = ["","Janeiro","Fevereiro","Marco","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;text-align:center;">
            <p style="color:#888;font-size:0.8rem;margin:0;">{hoje.day} de {meses[hoje.month]} de {hoje.year}</p>
            <h2 style="color:#c8a96e;margin:0.8rem 0;">⭐ {santo_nome}</h2>
            <p style="color:#1a1a1a;font-size:0.9rem;line-height:1.7;margin-top:1rem;">Que a intercessão deste santo(a) nos alcance as graças de que tanto precisamos. Que sua vida seja inspiracao para nós neste dia. Amem.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"🤖 Saiba mais sobre {santo_nome} com a IA", use_container_width=True, key="btn_ia_santo"):
            # Cria novo chat e manda a pergunta sobre o santo
            import uuid
            novo_id = str(uuid.uuid4())[:8]
            st.session_state.chats[novo_id] = {
                "nome": f"Santo: {santo_nome}",
                "historico": []
            }
            st.session_state.chat_atual = novo_id
            st.session_state.aba_chat = None
            st.session_state.pendente = f"Me conte sobre {santo_nome}: quem foi, sua historia de vida, seus milagres, por que foi canonizado e o que podemos aprender com seu exemplo de fe."
            st.rerun()
        st.stop()

    # ── ABA CALENDARIO LITURGICO ──
    if st.session_state.aba_chat == "calendario":
        st.markdown("<br>", unsafe_allow_html=True)
        from datetime import date, timedelta
        import math
        hoje = date.today()

        def pascoa(ano):
            a = ano % 19
            b = ano // 100
            c = ano % 100
            d = b // 4
            e = b % 4
            f = (b + 8) // 25
            g = (b - f + 1) // 3
            h = (19*a + b - d - g + 15) % 30
            i = c // 4
            k = c % 4
            l = (32 + 2*e + 2*i - h - k) % 7
            m = (a + 11*h + 22*l) // 451
            mes = (h + l - 7*m + 114) // 31
            dia = ((h + l - 7*m + 114) % 31) + 1
            return date(ano, mes, dia)

        p = pascoa(hoje.year)
        quaresma_inicio = p - timedelta(days=46)
        advento_inicio = date(hoje.year, 12, 25) - timedelta(days=22)
        pentecostes = p + timedelta(days=49)
        corpus_christi = p + timedelta(days=60)

        if hoje < quaresma_inicio:
            tempo = "Tempo Comum"
            cor = "#4CAF50"
            emoji = "🟢"
            desc = "Tempo de crescimento na fé e na vida crista."
        elif hoje == quaresma_inicio:
            tempo = "Quarta-feira de Cinzas"
            cor = "#666"
            emoji = "⚫"
            desc = "Inicio da Quaresma. Tempo de penitencia e conversão."
        elif hoje <= p - timedelta(days=1):
            dias = (p - hoje).days
            tempo = "Quaresma"
            cor = "#9C27B0"
            emoji = "🟣"
            desc = f"Tempo de penitencia, oração e jejum. Faltam {dias} dias para a Pascoa."
        elif hoje == p:
            tempo = "Pascoa do Senhor!"
            cor = "#FFD700"
            emoji = "✨"
            desc = "Aleluia! Cristo ressuscitou! O dia mais importante do ano liturgico."
        elif hoje <= pentecostes:
            dias = (hoje - p).days
            tempo = f"Tempo Pascal (Dia {dias})"
            cor = "#FFD700"
            emoji = "🟡"
            desc = "Tempo de alegria e celebração da Ressurreição de Cristo."
        elif hoje >= advento_inicio:
            tempo = "Advento"
            cor = "#9C27B0"
            emoji = "🟣"
            dias = (date(hoje.year, 12, 25) - hoje).days
            desc = f"Tempo de espéra e preparação para o Natal. Faltam {dias} dias."
        elif date(hoje.year, 12, 25) <= hoje <= date(hoje.year, 12, 31):
            tempo = "Tempo do Natal"
            cor = "#FFD700"
            emoji = "⭐"
            desc = "Celebramos o nascimento de Jesus Cristo, nossó Salvador."
        else:
            tempo = "Tempo Comum"
            cor = "#4CAF50"
            emoji = "🟢"
            desc = "Tempo de crescimento na fé e na vida crista."

        meses = ["","Janeiro","Fevereiro","Marco","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        dias_semana = ["Segunda-feira","Terca-feira","Quarta-feira","Quinta-feira","Sexta-feira","Sabado","Domingo"]
        dia_sem = dias_semana[hoje.weekday()]

        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:2px solid {cor};text-align:center;">
            <p style="color:#888;font-size:0.8rem;">{dia_sem}, {hoje.day} de {meses[hoje.month]} de {hoje.year}</p>
            <h2 style="color:{cor};margin:0.5rem 0;">{emoji} {tempo}</h2>
            <p style="color:#1a1a1a;font-size:0.95rem;line-height:1.7;margin-top:0.8rem;">{desc}</p>
        </div>
        <div style="background:rgba(255,255,255,0.85);border-radius:16px;padding:1.2rem;margin-top:1rem;border:1px solid #e8e0d0;">
            <p style="color:#c8a96e;font-weight:700;margin-bottom:0.5rem;">📅 Datas importantes {hoje.year}:</p>
            <p style="color:#1a1a1a;font-size:0.9rem;line-height:2;">
            🟣 Quaresma: {quaresma_inicio.strftime("%d/%m")}<br>
            ✨ Pascoa: {p.strftime("%d/%m")}<br>
            🕊️ Pentecostes: {pentecostes.strftime("%d/%m")}<br>
            🌟 Corpus Christi: {corpus_christi.strftime("%d/%m")}<br>
            🟣 Advento: {advento_inicio.strftime("%d/%m")}<br>
            ⭐ Natal: 25/12
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── ABA LITURGIA DO DIA ──
    if st.session_state.aba_chat == "liturgia":
        st.markdown("<br>", unsafe_allow_html=True)
        from datetime import date
        import requests as req
        hoje = date.today()
        meses = ["","Janeiro","Fevereiro","Marco","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;">
            <h3 style="color:#c8a96e;margin-bottom:0.5rem;">📖 Liturgia do Dia</h3>
            <p style="color:#888;font-size:0.85rem;">{hoje.day} de {meses[hoje.month]} de {hoje.year}</p>
            <hr style="border-color:#e8e0d0;margin:1rem 0;">
            <p style="color:#1a1a1a;font-size:0.95rem;line-height:1.7;">
            Para acompanhar as leituras completas da Missa de hoje, acesse o site oficial da CNBB:
            </p>
        </div>
        """, unsafe_allow_html=True)
        url_cnbb = f"https://liturgiadiaria.site/"
        st.markdown(f'<a href="{url_cnbb}" target="_blank" style="display:block;background:linear-gradient(135deg,#c8a96e,#a07840);color:#fff;text-align:center;padding:1rem;border-radius:12px;font-weight:700;text-decoration:none;margin-top:1rem;">📖 Ver Liturgia de Hoje</a>', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)

        # IA comenta a liturgia
        if st.button("✨ Pedir comentario da IA sobre a liturgia de hoje", use_container_width=True):
            with st.spinner("Gerando reflexao..."):
                import datetime
                data_str = f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"
                resp = st.session_state.cliente.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"user","content":f"Faca uma breve reflexao catolica sobre o espírito da liturgia do dia de hoje, {data_str}, considerando o tempo liturgico atual e o chamado de Jesus para nossa vida. Em portugues, de forma acolhedora e espiritual. Maximo 150 palavras."}]
                )
                reflexao = resp.choices[0].message.content
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;">
                    <p style="color:#c8a96e;font-weight:700;">✨ Reflexao do Dia</p>
                    <p style="color:#1a1a1a;line-height:1.8;font-size:0.95rem;">{reflexao}</p>
                </div>
                """, unsafe_allow_html=True)
        st.stop()

    # ── ABA NOVENAS ──
    if st.session_state.aba_chat == "novenas":
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.novena_aberta and st.session_state.novena_dia is not None:
            nome_n = st.session_state.novena_aberta
            dias_n = NOVENAS[nome_n]
            dia_idx = st.session_state.novena_dia
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;">
                <p style="color:#888;font-size:0.8rem;">{nome_n}</p>
                <h3 style="color:#c8a96e;margin:0.5rem 0;">🕯️ {dia_idx + 1}º Dia</h3>
                <p style="color:#1a1a1a;line-height:2;font-size:1rem;margin-top:1rem;">{dias_n[dia_idx]}</p>
            </div>
            """, unsafe_allow_html=True)
            col_a, col_p = st.columns(2)
            with col_a:
                if dia_idx > 0:
                    if st.button("← Anterior", use_container_width=True):
                        st.session_state.novena_dia -= 1
                        st.rerun()
            with col_p:
                if dia_idx < 8:
                    if st.button("Proximo ->", use_container_width=True):
                        st.session_state.novena_dia += 1
                        st.rerun()
                else:
                    if st.button("✅ Concluida!", use_container_width=True):
                        st.session_state.novena_aberta = None
                        st.session_state.novena_dia = None
                        st.rerun()
            if st.button("← Voltar"):
                st.session_state.novena_dia = None
                st.rerun()
        elif st.session_state.novena_aberta:
            nome_n = st.session_state.novena_aberta
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;">
                <h3 style="color:#c8a96e;">🕯️ {nome_n}</h3>
                <p style="color:#1a1a1a;line-height:1.8;font-size:0.9rem;margin-top:0.8rem;">Uma novena e uma oração de 9 dias consecutivos. Escolha um horario fixo cada dia e reze com fé e perseverança.</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("▶️ Comecar pelo 1o dia", use_container_width=True):
                st.session_state.novena_dia = 0
                st.rerun()
            if st.button("← Voltar"):
                st.session_state.novena_aberta = None
                st.rerun()
        else:
            for nome_n in NOVENAS:
                if st.button(f"🕯️ {nome_n}", use_container_width=True, key=f"nov_{nome_n}"):
                    st.session_state.novena_aberta = nome_n
                    st.rerun()
        st.stop()

    # ── ABA BÍBLIA ──
    if st.session_state.aba_chat == "biblia":
        st.markdown("<br>", unsafe_allow_html=True)
        livros = ["genesis","exodo","levitico","numeros","deuteronomio","josue","juizes","rute","1samuel","2samuel","1reis","2reis","1cronicas","2cronicas","esdras","neemias","ester","jo","salmos","proverbios","eclesiastes","cantares","isaias","jeremias","lamentações","ezequiel","daniel","oseias","joel","amos","abdias","jonas","miqueias","naum","habacuque","sofonias","ageu","zacarias","malaquias","mateus","marcos","lucas","joao","atos","romanos","1corintios","2corintios","galatas","efésios","filipénses","colossenses","1tessalonicenses","2tessalonicenses","1timoteo","2timoteo","tito","filemom","hebreus","tiago","1pédro","2pédro","1joao","2joao","3joao","judas","apocalipse"]
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



    # ── ABA CATECISMO ──
    if st.session_state.aba_chat == "catecismo":
        st.markdown("<br>", unsafe_allow_html=True)

        PILARES = {
            "I. A Profissao da Fe (O Credo)": [
                ("Par. 26", "Deus vem ao encontro do homem. A fé crista não é antes de tudo um conjunto de verdades a crer, mas um encontro com uma Pessoa viva: Jesus Cristo."),
                ("Par. 27", "O desejo de Deus esta inscrito no coracao do homem, porque o homem foi criado por Deus e para Deus. Deus nao cessa de atrair o homem para Si."),
                ("Par. 42", "Deus transcende toda criatura. E preciso purificar continuamente nossa linguagem de tudo o que ela tem de limitado, de figurado, de imperfeito."),
                ("Par. 150", "A fe e antes de tudo uma adesao pessoal do homem a Deus; e ao mesmo tempo, e inseparavel disso, o assentimento livre a toda a verdade que Deus revelou."),
                ("Par. 153", "A fe e um dom de Deus, uma virtude sobrenatural infundida por Ele. Para que esta fe exista, sao necessarios a graca preveniente e a ajuda interior do Espirito Santo."),
                ("Par. 166", "A fe e um ato pessoal: a resposta livre do homem a iniciativa de Deus que se revela. Mas a fe nao e um ato isolado. Ninguem pode crer sozinho."),
                ("Par. 185", "Credo — eu creio. Este simbolo e uma sintese da nossa fe. As primeiras comunidades cristas formularam profissoes de fe breves para exprimir sua adesao a Cristo."),
                ("Par. 198", "Nossa profissao de fe comeca por Deus, pois Deus e o Primeiro e o Ultimo, o Principio e o Fim de tudo. O Credo comeca com Deus Pai, pois o Pai e a primeira Pessoa divina da Santissima Trindade."),
                ("Par. 232", "Os cristaos sao batizados em nome do Pai e do Filho e do Espirito Santo. Antes de receber o Batismo, respondem tres vezes: Creio, as tres perguntas sobre sua crença no Pai, no Filho e no Espirito Santo."),
                ("Par. 234", "O misterio da Santissima Trindade e o misterio central da fe e da vida crista. E o misterio de Deus em Si mesmo."),
                ("Par. 422", "O Filho de Deus se fez homem para nos salvar. A Encarnacao — o fato de o Filho de Deus ter assumido uma natureza humana para realizar nela a salvacao de todos os homens — e a verdade central da fe crista."),
                ("Par. 456", "Com a Palavra feita carne, a luz da Sua gloria brilhou de modo novo nos olhos do nosso espirito, de modo que, contemplando a Deus visivelmente, sejamos por Ele arrebatados ao amor das coisas invisiveis."),
                ("Par. 484", "A Anunciacao a Maria inaugura a plenitude dos tempos, ou seja, o cumprimento das promessas e das preparacoes. Maria foi convidada a conceber Aquele em quem habitaria corporalmente toda a plenitude da divindade."),
                ("Par. 638", "A Ressurreicao de Cristo e a verdade culminante da nossa fe em Cristo. Ela e crida e vivida pela comunidade crista como verdade central."),
                ("Par. 668", "Cristo morreu e voltou a vida para ser Senhor tanto dos mortos como dos vivos. Sua ascensao ao Ceu significa Sua participacao, em Sua humanidade, no poder e na autoridade do proprio Deus."),
                ("Par. 683", "O Espirito Santo e enviado para santificar e vivificar a Igreja. O Espirito e o doador da vida; por Ele todos os fieis nascem de novo pela agua e pelo Espirito."),
                ("Par. 748", "Cristo e a luz das nacoes. Esta luz de Cristo brilha no rosto da Igreja. A Igreja e, em Cristo, como que o sacramento, ou seja, o sinal e o instrumento da uniao intima com Deus e da unidade de todo o genero humano."),
                ("Par. 988", "O dogma crista da ressurreicao dos mortos e uma verdade essencial da fe. A ressurreicao dos mortos e a ressurreicao de pessoas reais, que sao reconhecidas como tais."),
                ("Par. 1020", "O cristao que une sua propria morte a de Jesus encarece nela a plenitude do misterio pascal. Haja vista o que Cristo nos disse: Quem cre em Mim, mesmo que morra, viverá."),
                ("Par. 1023", "Os que morrem na graca e na amizade de Deus e estao perfeitamente purificados vivem para sempre com Cristo. Sao semelhantes a Deus, pois O veem tal como Ele e, face a face."),
            ],
            "II. A Celebracao do Misterio Crista (Os Sacramentos)": [
                ("Par. 1066", "Na liturgia da Igreja, Cristo significa e realiza principalmente Seu misterio pascal. Durante Sua vida terrena, Jesus anunciava Sua Pascoa e a ela se preparava. Ao morrer, ressuscitar e ser glorificado, Ele a realizou uma vez por todas."),
                ("Par. 1113", "Toda a vida liturgica da Igreja gira em torno do sacrificio eucaristico e dos sacramentos. Ha na Igreja sete sacramentos: o Batismo, a Crisma, a Eucaristia, a Penitencia, a Uncao dos Enfermos, a Ordem e o Matrimonio."),
                ("Par. 1127", "Os sacramentos sao eficazes porque neles age o proprio Cristo. Cristo batiza, Cristo age nos sacramentos para comunicar a graca que o sacramento significa."),
                ("Par. 1213", "O santo Batismo e o fundamento de toda a vida crista, o portico da vida no Espirito e a porta que abre o acesso aos outros sacramentos. Pelo Batismo somos libertados do pecado e regenerados como filhos de Deus."),
                ("Par. 1244", "A imersaão na agua simboliza o sepultamento com Cristo. Sair da agua e como a ressurreicao com Cristo: nascer para uma vida nova. O Batismo e o sacramento da regeneracao pela agua e no Espirito."),
                ("Par. 1285", "Com o Batismo e a Eucaristia, o sacramento da Crisma constitui o conjunto dos sacramentos da inicacao crista. Fortalece a graca batismal: e o sacramento que da o Espirito Santo para nos inserir mais plenamente na Igreja."),
                ("Par. 1322", "A sagrada Eucaristia conclui a inicacao crista. Os que foram elevados a dignidade do sacerdocio real pelo Batismo e configurados mais profundamente a Cristo pela Crisma, participam por intermedio da Eucaristia com toda a comunidade no proprio sacrificio do Senhor."),
                ("Par. 1324", "A Eucaristia e a fonte e o apice de toda a vida crista. Os outros sacramentos e todos os ministerios eclesiais estao ligados a Eucaristia e a ela se ordenam."),
                ("Par. 1339", "Jesus escolheu o momento da Pascoa para realizar o que havia anunciado em Cafarnau: dar a Seus discipulos Seu Corpo e Seu Sangue. Na vespera de Sua Paixao, estando sentado a mesa com Seus Apostolos, Jesus instituiu a Eucaristia."),
                ("Par. 1422", "Os que se aproximam do sacramento da Penitencia obtem da misericordia de Deus o perdoão das ofensas feitas a Ele; ao mesmo tempo, reconciliam-se com a Igreja, a qual feriram com seus pecados."),
                ("Par. 1446", "Cristo instituiu o sacramento da Penitencia para todos os membros pecadores de Sua Igreja; antes de tudo para os que, depois do Batismo, caem no pecado grave e assim perdem a graca batismal."),
                ("Par. 1499", "Pela santa Uncao dos Enfermos e pela oracao dos sacerdotes, a Igreja toda confia os doentes ao Senhor sofredor e glorificado para que Ele os alivie e os salve."),
                ("Par. 1601", "A alianca matrimonial, pela qual o homem e a mulher constituem entre si uma intima comunhao de vida e de amor, foi fundada e dotada de suas leis proprias pelo Criador. Por sua natureza, e ordenada ao bem dos conjuges e a geracao e educacao dos filhos."),
            ],
            "III. A Vida em Cristo (Os Mandamentos)": [
                ("Par. 1691", "Cristao, conhece tua dignidade. Tornaste-te participe da natureza divina; nao voltes a baixeza da tua antiga conduta. Lembra quem e tua Cabeca e de qual Corpo eres membro."),
                ("Par. 1700", "A dignidade da pessoa humana tem seu fundamento na sua criacao a imagem e semelhanca de Deus. Dotada de alma espiritual e imortal, de inteligencia e de livre-arbitrio, a pessoa humana e ordenada a Deus e chamada a Ele."),
                ("Par. 1730", "Deus criou o homem racional e, por conseguinte, livre. A liberdade e o poder, radicado na razao e na vontade, de agir ou nao agir, de fazer isto ou aquilo, de executar assim por si mesmo acoes deliberadas."),
                ("Par. 1776", "A consciencia moral e um juizo da razao pelo qual a pessoa humana reconhece a qualidade moral de um ato concreto que vai praticar, esta praticando ou praticou."),
                ("Par. 1803", "Uma virtude e uma disposicao habitual e firme para fazer o bem. A virtude permite a pessoa nao somente praticar atos bons, mas dar o melhor de si mesma."),
                ("Par. 1822", "A caridade e a virtude teologal pela qual amamos a Deus sobre todas as coisas, por amor d'Ele mesmo, e o nosso proximo como a nos mesmos por amor de Deus."),
                ("Par. 1849", "O pecado e uma falta contra a razao, a verdade, a consciencia reta; e uma transgressao em relacao ao amor verdadeiro para com Deus e para com o proximo. Ofende Deus e rompe a amizade com Ele."),
                ("Par. 1855", "O pecado mortal destroi a caridade no coracao do homem pelo grave desprezo de Deus, afasta o homem de Deus, que e seu fim ultimo e sua beatitude. O pecado venial deixa subsistir a caridade, mas a ofende e a machuca."),
                ("Par. 1968", "A lei evangelica cumpre, purifica, supera e eleva a lei antiga. As Bem-aventurancas revelam uma ordem de santidade. Prometem as bencaos e as recompensas ja entrevistas por Abraham. Realizam-nas e superam-nas."),
                ("Par. 2052", "Jesus resume os mandamentos dizendo: Deves amar ao Senhor teu Deus com todo o teu coracao, com toda a tua alma e com todo o teu espirito. Este e o maior e o primeiro mandamento. O segundo e semelhante a este: Deves amar ao teu proximo como a ti mesmo."),
                ("Par. 2083", "Jesus resumiu as obrigacoes do homem para com Deus no mandamento de amar a Deus de todo o coracao, com toda a alma e com toda a mente. Ao mesmo tempo, dirigiu a atencao para a autenticidade do culto divino."),
                ("Par. 2196", "Em resposta a pergunta sobre o primeiro dos mandamentos, Jesus diz: O primeiro e: Ouve, Israel! O Senhor nosso Deus e o unico Senhor; e tu amaras o Senhor teu Deus de todo o teu coracao, de toda a tua alma, de todo o teu espirito e de todas as tuas forcas."),
                ("Par. 2258", "A vida humana e sagrada porque, desde a sua origem, importa a acao criadora de Deus e permanece para sempre em relacao especial com o Criador, seu unico fim. So Deus e o Senhor da vida do seu inicio ate ao seu termo."),
                ("Par. 2302", "O Senhor diz: Todo aquele que se encoleriza com seu irmao sera submetido ao juizo. A ira e o desejo de vinganca contra aquele que se considera responsavel por um dano sofrido. Jesus exige a reconciliacao."),
                ("Par. 2401", "O setimo mandamento proibe tirar ou reter injustamente os bens do proximo e prejudica-lo de qualquer forma em seus bens. Prescreve a justica e a caridade na gestao dos bens terrestres."),
            ],
            "IV. A Oracao Crista": [
                ("Par. 2558", "O grande drama da oracao e perseverarmos nela ate o fim e acreditarmos na eficacia da oracao. A oracao e um dom de Deus que transborda para o coracao do homem."),
                ("Par. 2559", "A oracao e a elevacao da alma a Deus ou o pedido a Deus de bens conformes com a Sua vontade. Ela e sempre dom de Deus que vem ao encontro do homem."),
                ("Par. 2566", "Deus chama o homem primeiro. Quer o homem se esqueca do seu Criador ou se esconda d'Ele, quer corra atras de seus idolos ou acuse a divindade de o ter abandonado, o Deus vivo e verdadeiro nao cessa de chamar cada pessoa ao encontro misterioso da oracao."),
                ("Par. 2590", "O profeta eleva sua oracao a Deus e intercede por ele. A oracao prophetica e intercessao. E um dom especial de Deus, uma graca que Ele concede a quem escolhe."),
                ("Par. 2607", "Jesus ora diante dos momentos decisivos de Sua missao: antes do Seu batismo e da Sua transfiguracao, na agonia do Getsemani, e ainda na Cruz."),
                ("Par. 2623", "A Igreja comunica a seus filhos as formas de oracao: a bencao e a adoracao, a peticao, a intercessao, a acao de gracas e o louvor."),
                ("Par. 2650", "A oracao nao se reduz ao jorro espontaneo de um impulso interior: para orar, e preciso querer orar. Tambem nao basta saber o que as Escrituras revelam sobre a oracao; e preciso aprender a orar."),
                ("Par. 2697", "A oracao e a vida do coracao novo. Deve animar-nos em todo momento. Contudo, esquecemos d'Aquele que e nossa vida e nosso tudo. Por isso os Padres espirituais insistem na oracao como dever primeiro do cristao."),
                ("Par. 2759", "Jesus nos ensinou a orar, respondendo ao pedido de um de Seus discipulos: Senhor, ensina-nos a orar, como Joao ensinou a seus discipulos. Ele nos disse entao o Pai Nosso, a mais perfeita das oracoes."),
                ("Par. 2765", "A oracao dominical e verdadeiramente a sintese de todo o Evangelho. Desde que o Senhor a formulou, ela passou a ser o resumo de toda a fe e toda a esperanca do povo de Deus."),
                ("Par. 2777", "Na liturgia judaica, este titulo e reservado ao Deus de Israel. Ao dizer Pai Nosso, Jesus nos revela que Deus e verdadeiramente Pai e que somos verdadeiramente Seus filhos."),
                ("Par. 2803", "Depois de nos colocarmos sob a presenca de Deus e de o adorarmos, o Espirito de adocao suscita em nossos coracoes sete pedidos, sete bencaos. Os tres primeiros, mais teologicos, nos atraem para a gloria do Pai; os quatro ultimos oferecem ao Pai nossos miserias e nossas expectativas."),
                ("Par. 2827", "Seja feita a Tua vontade assim na terra como no Ceu. Com Jesus, sabemos que Sua vontade e que todos os homens sejam salvos. E nossa oracao que tudo aquilo que queremos esteja conforme a Sua vontade."),
                ("Par. 2850", "O ultimo pedido do Pai Nosso e tambem levado na oracao de Jesus ao Pai. Livrai-nos do Mal. O mal de que nos pede para ser libertados nao e uma abstracao, mas uma pessoa: Satanas, o Maligno, o anjo que se ops a Deus."),
                ("Par. 2856", "No fim da oracao dominical, ha uma doxologia: Teu e o reino, o poder e a gloria, para sempre. A Igreja acrescenta Amem, que ratifica tudo o que esta contido na oracao ensinada por Deus."),
            ],
        }

        if "cat_pilar" not in st.session_state:
            st.session_state.cat_pilar = None

        if st.session_state.cat_pilar is None:
            st.markdown("""
            <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;text-align:center;">
                <h2 style="color:#c8a96e;margin:0 0 0.3rem 0;">📖 Catecismo da Igreja Catolica</h2>
                <p style="color:#888;font-size:0.85rem;margin:0;">Artigos selecionados — Escolha um dos 4 pilares</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            for pilar in PILARES.keys():
                num = pilar.split(".")[0].strip()
                nome = pilar.split("(")[0].split(".")[1].strip() if "(" in pilar else pilar
                desc = pilar.split("(")[1].replace(")", "") if "(" in pilar else ""
                if st.button(f"{pilar}", use_container_width=True, key=f"pilar_{num}"):
                    st.session_state.cat_pilar = pilar
                    st.rerun()
        else:
            pilar_atual = st.session_state.cat_pilar
            artigos = PILARES[pilar_atual]
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.2rem;margin-top:1rem;border:1px solid #e8e0d0;text-align:center;">
                <h3 style="color:#c8a96e;margin:0;">📖 {pilar_atual}</h3>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            for num, texto in artigos:
                with st.expander(f"📜 {num}"):
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.9);border-radius:12px;padding:1rem;border-left:4px solid #c8a96e;">
                        <p style="color:#1a1a1a;line-height:1.8;margin:0;font-size:0.95rem;">{texto}</p>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Voltar aos Pilares", use_container_width=True):
                st.session_state.cat_pilar = None
                st.rerun()
        st.stop()

    # ── ABA CREDITOS ──
    if st.session_state.aba_chat == "creditos":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:2rem;margin-top:1rem;border:1px solid #e8e0d0;text-align:center;">
            <h2 style="color:#c8a96e;margin:0 0 0.5rem 0;">✝️ Virtual Catholics</h2>
            <p style="color:#888;font-size:0.85rem;margin:0 0 1.5rem 0;">Assistente Catolico Digital</p>
            <div style="background:#f9f5ee;border-radius:12px;padding:1.2rem;margin-bottom:1rem;border:1px solid #e8e0d0;">
                <p style="color:#c8a96e;font-weight:700;margin:0 0 0.3rem 0;">👨‍💻 Criador</p>
                <p style="color:#1a1a1a;margin:0;font-size:1rem;font-weight:600;">Pedro</p>
                <p style="color:#666;margin:0;font-size:0.85rem;">Desenvolvedor e idealizador do Virtual Catholics,<br>movido pela fe catolica e pelo desejo de levar<br>a fé digital a todos os cristaos.</p>
            </div>
            <div style="background:#f9f5ee;border-radius:12px;padding:1.2rem;margin-bottom:1rem;border:1px solid #e8e0d0;">
                <p style="color:#c8a96e;font-weight:700;margin:0 0 0.3rem 0;">💡 Agradecimento Especial</p>
                <p style="color:#1a1a1a;margin:0;font-size:1rem;font-weight:600;">Joao Lucas</p>
                <p style="color:#666;margin:0;font-size:0.85rem;">Amigo e colaborador que contribuiu com ideias<br>fundamentais para o desenvolvimento do projeto.</p>
            </div>
            <div style="background:#f9f5ee;border-radius:12px;padding:1.2rem;margin-bottom:1.5rem;border:1px solid #e8e0d0;">
                <p style="color:#c8a96e;font-weight:700;margin:0 0 0.3rem 0;">🙏 Dedicado a</p>
                <p style="color:#1a1a1a;margin:0;font-size:0.9rem;">A Deus, a Nossa Senhora e a todos os cristaos<br>que buscam fortalecer sua fe no mundo digital.</p>
            </div>
            <p style="color:#aaa;font-size:0.75rem;margin:0;">Virtual Catholics © 2025 — Feito com fe e amor ✝️</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── ABA DOACOES ──
    if st.session_state.aba_chat == "doacoes":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:rgba(255,255,255,0.92);border-radius:16px;padding:2rem;"
            "margin-top:1rem;border:1px solid #e8e0d0;text-align:center;'>"
            "<h2 style='color:#c8a96e;margin:0 0 0.5rem 0;'>&#128155; Apoie o Virtual Catholics</h2>"
            "<p style='color:#666;font-size:0.9rem;margin:0 0 1.5rem 0;'>"
            "Sua doa&#231;&#227;o ajuda a manter e expandir este minist&#233;rio digital</p>"
            "<div style='background:#fffbf0;border-radius:12px;padding:1.2rem;"
            "margin-bottom:1rem;border:1px solid #f0e0a0;text-align:left;'>"
            "<p style='color:#c8a96e;font-weight:700;margin:0 0 0.8rem 0;text-align:center;'>"
            "Para que v&#227;o as doa&#231;&#245;es?</p>"
            "<p style='color:#1a1a1a;margin:0 0 0.5rem 0;'>&#127760; <b>Manter o site no ar</b> &#8212; servidores e hospedagem</p>"
            "<p style='color:#1a1a1a;margin:0 0 0.5rem 0;'>&#128279; <b>Dom&#237;nio pr&#243;prio</b> &#8212; um endere&#231;o exclusivo para o app</p>"
            "<p style='color:#1a1a1a;margin:0 0 0.5rem 0;'>&#9881;&#65039; <b>Desenvolvimento</b> &#8212; novas funcionalidades e melhorias</p>"
            "<p style='color:#1a1a1a;margin:0 0 0.5rem 0;'>&#128241; <b>Desenvolvimento do aplicativo</b> &#8212; para que o app cres&#231;a</p>"
            "<p style='color:#1a1a1a;margin:0;'>&#127371; <b>Expans&#227;o</b> &#8212; para que mais crist&#227;os possam ser alcan&#231;ados</p>"
            "</div>"
            "<div style='background:#f0fff4;border-radius:12px;padding:1.5rem;"
            "margin-bottom:1rem;border:2px solid #c8a96e;'>"
            "<p style='color:#c8a96e;font-weight:700;margin:0 0 0.5rem 0;font-size:1.1rem;'>&#128241; Chave Pix</p>"
            "<p style='color:#1a1a1a;font-size:1.3rem;font-weight:700;margin:0 0 0.5rem 0;letter-spacing:1px;'>61 98510-1908</p>"
            "<p style='color:#888;font-size:0.8rem;margin:0;'>Qualquer valor &#233; uma b&#234;n&#231;&#227;o enorme! &#128591;</p>"
            "</div>"
            "<p style='color:#aaa;font-size:0.8rem;margin:0;'>"
            "Que Deus aben&#231;oe imensamente cada pessoa que contribui<br>"
            "com este minist&#233;rio. Obrigado de cora&#231;&#227;o! &#10015;&#65039;"
            "</p>"
            "</div>",
            unsafe_allow_html=True
        )
        st.stop()


    if not st.session_state.chat_atual or st.session_state.chat_atual not in st.session_state.chats:
        st.markdown(f"""
        <div class="welcome">
            <div style="margin-bottom:1rem;">{logo_html}</div>
            <h2 style="color:#1a1a1a !important;-webkit-text-fill-color:#1a1a1a;">Olá, {nome}! 🙏</h2>
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
            chat_html = '<div class="welcome"><h2 style="color:#1a1a1a !important;">Nova conversa 🙏</h2><p style="color:#333!important;">Como possó te ajudar?</p></div>'
        else:
            for msg in historico:
                if msg["role"] == "user":
                    chat_html += f'<div class="msg-user"><div class="bubble-user">{msg["content"]}</div></div>'
                else:
                    chat_html += f'<div class="msg-bot"><div style="flex-shrink:0;margin-top:2px;">{logo_html}</div><div class="bubble-bot" style="color:#1a1a1a !important;background:rgba(255,255,255,0.85);padding:0.7rem 1rem;border-radius:0 16px 16px 16px;">{msg["content"]}</div></div>'

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

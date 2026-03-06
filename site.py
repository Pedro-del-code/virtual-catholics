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

        # Fallback simplés por data
        SANTOS_FIXOS = {
            (1,1):"Maria Santíssima, Mãe de Deus",(1,2):"Santos Basilio Magno e Gregório Nazianzeno",(1,3):"Santíssimo Nome de Jesus",(1,4):"Santa Isabel Ana Seton",(1,5):"São João Neumann",(1,6):"Epifania do Senhor",(1,7):"São Raimundo de Peñafort",(1,8):"São Severino",(1,9):"São Adriano",(1,10):"São Guilherme",(1,11):"São Teodósio",(1,12):"São Taciano",(1,13):"Santo Hilário de Poitiers",(1,14):"Santo Eufrasio",(1,15):"Santo Antônio Abade",(1,16):"São Berno",(1,17):"Santo Antonio do Egito",(1,18):"Santa Prisca",(1,19):"São Mario e companheiros",(1,20):"Santos Fabiano e Sebastiao",(1,21):"Santa Inês",(1,22):"Santos Vicente e Anastasio",(1,23):"São Ildefonso",(1,24):"São Francisco de Sales",(1,25):"Conversão de São Paulo",(1,26):"Santos Timóteo e Tito",(1,27):"Santa Ângelá Merici",(1,28):"Santo Tomás de Aquino",(1,29):"São Gildas",(1,30):"Santa Martina",(1,31):"São João Bosco",
            (2,1):"São Inácio de Antioquia",(2,2):"Apresentação do Senhor",(2,3):"São Biagio",(2,4):"São José de Leonessa",(2,5):"Santa Ágata",(2,6):"Santos Paulo Miki e companheiros",(2,7):"São Colette",(2,8):"Santo Jerônimo Emiliani",(2,9):"Santa Apolônia",(2,10):"Santa Escolástica",(2,11):"Nossa Senhora de Lourdes",(2,12):"São Eulalia",(2,13):"São Benigno",(2,14):"Santos Cirilo e Metodio",(2,15):"São Claudio",(2,16):"São Onesimo",(2,17):"Sete Santos Fundadorés dos Servitas",(2,18):"São Simeão",(2,19):"São Barbato",(2,20):"São Eucario",(2,21):"São Damiao",(2,22):"Cátedra de São Pedro",(2,23):"São Policarpo",(2,24):"São Etelberto",(2,25):"São Cesario",(2,26):"Santa Paulá Montal",(2,27):"São Gabriel da Virgem das Dores",(2,28):"São Romano",
            (3,1):"São Álvaro",(3,2):"São Carlos o Bom",(3,3):"Santa Cunegundes",(3,4):"São Casimiro",(3,5):"São Adriano",(3,6):"São Colette",(3,7):"Santas Perpétua e Félicidade",(3,8):"São João de Deus",(3,9):"Santa Francisca Romana",(3,10):"São Simplício",(3,11):"São Eulógio",(3,12):"São Gregório Magno",(3,13):"Santa Eufrásia",(3,14):"Santa Matilde",(3,15):"São Lourenço de Brindisi",(3,16):"São Heriberto",(3,17):"Santo Patrício",(3,18):"São Cirilo de Jerusalém",(3,19):"São José, Esposó de Maria",(3,20):"Santa Claudia",(3,21):"Santo Benedito",(3,22):"São Epafrodito",(3,23):"São Turibio de Mogrovejo",(3,24):"São Oscar",(3,25):"Anunciação do Senhor",(3,26):"São Cástulo",(3,27):"São Rupérto",(3,28):"São Sixto III",(3,29):"São Bertoldo",(3,30):"São João Clímaco",(3,31):"São Benjamim",
            (4,1):"São Hugo de Grenoble",(4,2):"São Francisco de Paula",(4,3):"São Ricardo",(4,4):"Santo Isidoro de Sevilha",(4,5):"São Vicente Férrer",(4,6):"Santo Celestino I",(4,7):"São João Batista de La Salle",(4,8):"Santo Alberto",(4,9):"Santa Maria Cleofass",(4,10):"São Miguel de los Santos",(4,11):"São Estanislau",(4,12):"São Julio I",(4,13):"Santo Hermenegildo",(4,14):"Santos Tibúrcio e Valeriano",(4,15):"Santa Anastasia",(4,16):"Santa Bernadete",(4,17):"Santo Aniceto",(4,18):"São Eleutério",(4,19):"São Leao IX",(4,20):"Santa Inês de Montepulciano",(4,21):"Santo Anselmo",(4,22):"São Sótero e Caio",(4,23):"São Jorge",(4,24):"São Fidel de Sigmaringa",(4,25):"São Marcos Evangelista",(4,26):"Nossa Senhora do Bom Conselho",(4,27):"Santo Pedro Canísio",(4,28):"São Pedro Chanel",(4,29):"Santa Catarina de Siena",(4,30):"São Pio V",
            (5,1):"São José Opérário",(5,2):"São Atanásio",(5,3):"Santos Filipé e Tiago",(5,4):"Santa Mônica",(5,5):"Santo Ângelo",(5,6):"São Domitila",(5,7):"Santa Flavia Domitila",(5,8):"Aparição de São Miguel Arcanjo",(5,9):"São Gregório Nazianzeno",(5,10):"São Antonino",(5,11):"Santos Inacio e Epimaco",(5,12):"Santos Nereu e Aquileu",(5,13):"Nossa Senhora de Fátima",(5,14):"São Matias",(5,15):"São Isidoro Lavrador",(5,16):"São Simão Stock",(5,17):"São Pascoal Bailão",(5,18):"São João I",(5,19):"São Pedro Celestino",(5,20):"São Bernardino de Siena",(5,21):"Santa Crisantema",(5,22):"Santa Rita de Cássia",(5,23):"São Guilherme de Rochester",(5,24):"Santa Maria Auxiliadora",(5,25):"Santo Gregório VII",(5,26):"São Filipé Néri",(5,27):"São Agostinho de Cantuária",(5,28):"Santo Emilio",(5,29):"Santa Bona",(5,30):"Santa Joana d'Arc",(5,31):"Visitação de Nossa Senhora",
            (6,1):"Santo Justino",(6,2):"Santos Marcelino e Pedro",(6,3):"Santos Carlos Lwanga e companheiros",(6,4):"Santa Saturnina",(6,5):"São Bonifácio",(6,6):"São Norberto",(6,7):"Santa Ana dos Anjos",(6,8):"São Medardo",(6,9):"Santos Primo e Féliciano",(6,10):"Santa Oliva",(6,11):"São Barnabe",(6,12):"São Onofre",(6,13):"Santo Antônio de Lisboa",(6,14):"Santo Elias",(6,15):"Santos Vito e Modesto",(6,16):"São Bento José Labre",(6,17):"São Gregório Barbarigo",(6,18):"São Marcos e Marceliano",(6,19):"São Romualdo",(6,20):"Santo Silvério",(6,21):"São Luís Gonzaga",(6,22):"São Paulino de Nola",(6,23):"São José Cafasso",(6,24):"Natividade de São João Batista",(6,25):"São Guilherme",(6,26):"Santos João e Paulo",(6,27):"Nossa Senhora do Perpétuo Socorro",(6,28):"São Ireneu",(6,29):"Santos Pedro e Paulo",(6,30):"Primeiros Mártirés de Roma",
            (7,1):"São Junípéro Serra",(7,2):"Visitação de Nossa Senhora",(7,3):"São Tomás Apóstolo",(7,4):"Santa Isabel de Portugal",(7,5):"Santo Antônio Zaccaria",(7,6):"Santa Maria Goretti",(7,7):"São Panteno",(7,8):"Santa Aquila",(7,9):"Santos Agostinho Zhao Rong e companheiros",(7,10):"Santos Sete Irmaos",(7,11):"São Benedito",(7,12):"São João Gualberto",(7,13):"São Henrique",(7,14):"São Camilo de Lellis",(7,15):"São Boaventura",(7,16):"Nossa Senhora do Carmo",(7,17):"Santo Aleixo",(7,18):"Santa Sinforosa",(7,19):"Santa Macrina",(7,20):"São Elias Proféta",(7,21):"São Lourenço de Brindisi",(7,22):"Santa Maria Madalena",(7,23):"Santa Brígida",(7,24):"São Xisto II",(7,25):"São Tiago Apóstolo",(7,26):"Santos Joaquim e Ana",(7,27):"Santa Natália",(7,28):"Santo Inocêncio I",(7,29):"Santa Marta",(7,30):"Santos Abdon e Sennen",(7,31):"Santo Inácio de Loyola",
            (8,1):"Santo Afonsó Maria de Ligório",(8,2):"Santo Eusébio de Vercelli",(8,3):"Santo Estêvão I",(8,4):"Santo João Maria Vianney",(8,5):"Dedicação da Basílica de Santa Maria Maior",(8,6):"Transfiguração do Senhor",(8,7):"São Caetano",(8,8):"São Domingos",(8,9):"São Romano",(8,10):"São Lourenço",(8,11):"Santa Clara de Assis",(8,12):"Santa Joana Francisca de Chantal",(8,13):"Santos Hipólito e Cassiano",(8,14):"São Maximiliano Maria Kolbe",(8,15):"Assunção de Nossa Senhora",(8,16):"Santo Estêvão da Hungria",(8,17):"Santa Joana",(8,18):"Santa Helena",(8,19):"São João Eudes",(8,20):"São Bernardo de Claraval",(8,21):"São Pio X",(8,22):"Maria Rainha",(8,23):"Santa Rosa de Lima",(8,24):"São Bartolomeu Apóstolo",(8,25):"São Luís IX",(8,26):"Santa Teresa de Jesus Jornet",(8,27):"Santa Mônica",(8,28):"Santo Agostinho",(8,29):"Martírio de São João Batista",(8,30):"Santo Félix e Adaucto",(8,31):"Santo Raimundo Nonato",
            (9,1):"Santo Egídio",(9,2):"São Estêvão da Hungria",(9,3):"São Gregório Magno",(9,4):"Santa Rosália",(9,5):"São Lourenço Justiniano",(9,6):"São Eleutário",(9,7):"Santa Regina",(9,8):"Natividade de Nossa Senhora",(9,9):"Santo Pedro Claver",(9,10):"Santos Protásio e Gervásio",(9,11):"São Proto",(9,12):"Santíssimo Nome de Maria",(9,13):"São João Crisóstomo",(9,14):"Exaltação da Santa Cruz",(9,15):"Nossa Senhora das Dores",(9,16):"Santos Cornélio e Cipriano",(9,17):"Santa Hildegarda",(9,18):"Santa Sofia",(9,19):"Santos Januário e companheiros",(9,20):"Santos André Kim e companheiros",(9,21):"São Mateus",(9,22):"São Maurício",(9,23):"São Pio de Pietrelcina - Padre Pio",(9,24):"Nossa Senhora das Mercês",(9,25):"Santo Cleofas",(9,26):"Santos Cosme e Damião",(9,27):"São Vicente de Paulo",(9,28):"São Venceslau",(9,29):"Santos Miguel, Gabriel e Rafael",(9,30):"São Jerônimo",
            (10,1):"Santa Teresinha do Menino Jesus",(10,2):"Santos Anjos da Guarda",(10,3):"São Geraldo",(10,4):"São Francisco de Assis",(10,5):"Santa Faustina Kowalska",(10,6):"São Bruno",(10,7):"Nossa Senhora do Rosário",(10,8):"Santa Brígida",(10,9):"São Dionísio e companheiros",(10,10):"São Luís Bertrão",(10,11):"São Filipé Diácono",(10,12):"Nossa Senhora Aparecida",(10,13):"São Eduardo",(10,14):"São Calisto I",(10,15):"Santa Teresa de Ávila",(10,16):"Santa Edwiges",(10,17):"Santo Inácio de Antioquia",(10,18):"São Lucas Evangelista",(10,19):"Santos João de Brébeuf e companheiros",(10,20):"Santo João Cantius",(10,21):"Santa Úrsula",(10,22):"São João Paulo II",(10,23):"São João de Capéstrano",(10,24):"São Antônio Maria Claret",(10,25):"Santos Crispim e Crispiniano",(10,26):"São Evaristo",(10,27):"São Frumentino",(10,28):"Santos Simão e Judas",(10,29):"Santa Ermelinda",(10,30):"São Zenóbio",(10,31):"Santa Lucíola",
            (11,1):"Todos os Santos",(11,2):"Todos os Fiéis Defuntos",(11,3):"São Martinho de Porres",(11,4):"São Carlos Borromeu",(11,5):"São Zacarias",(11,6):"São Leonardo",(11,7):"Santa Ernesta",(11,8):"São Deusdedit",(11,9):"Dedicação da Basílica de São João de Latrão",(11,10):"São Leão Magno",(11,11):"São Martinho de Tours",(11,12):"São Josafá",(11,13):"São Estanislau Kostka",(11,14):"São Lourenço O Iluminador",(11,15):"São Alberto Magno",(11,16):"Santa Gertrudes",(11,17):"Santa Isabel da Hungria",(11,18):"Dedicação das Basílicas de São Pedro e São Paulo",(11,19):"Santa Matilde",(11,20):"São Edmundo",(11,21):"Apresentação de Nossa Senhora",(11,22):"Santa Cecília",(11,23):"São Clemente I",(11,24):"Santos André Dũng-Lạc e companheiros",(11,25):"Santa Catarina de Alexandria",(11,26):"São Silvestre Gozzolini",(11,27):"São Virgílio",(11,28):"Santo Antônio de Amandola",(11,29):"São Saturnino",(11,30):"São André Apóstolo",
            (12,1):"São Elói",(12,2):"Santa Bibiana",(12,3):"São Francisco Xavier",(12,4):"Santa Bárbara",(12,5):"São Sabas",(12,6):"São Nicolau",(12,7):"Santo Ambrósio",(12,8):"Imaculada Conceição de Maria",(12,9):"Santa Leocádia",(12,10):"Nossa Senhora de Loreto",(12,11):"São Dâmasó I",(12,12):"Nossa Senhora de Guadalupé",(12,13):"Santa Lúcia",(12,14):"São João da Cruz",(12,15):"Santo Alberto de Jerusalém",(12,16):"Santa Adelaide",(12,17):"Santo Lázaro",(12,18):"Nossa Senhora da Espérança",(12,19):"São Urbano V",(12,20):"Santo Domingo de Silos",(12,21):"São Pedro Canísio",(12,22):"Santa Francisca Cabrini",(12,23):"São João de Kety",(12,24):"Vigília do Natal",(12,25):"Natividade de Nossó Senhor Jesus Cristo",(12,26):"Santo Estêvão",(12,27):"São João Apóstolo",(12,28):"Santos Inocentes",(12,29):"Santo Tomás Becket",(12,30):"Santa Sabina",(12,31):"São Silvestre I"
        }
        santo_nome = SANTOS_FIXOS.get((hoje.month, hoje.day), "Santo(a) do dia")
        meses = ["","Janeiro","Fevereiro","Marco","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.92);border-radius:16px;padding:1.5rem;margin-top:1rem;border:1px solid #e8e0d0;text-align:center;">
            <p style="color:#888;font-size:0.8rem;margin:0;">{hoje.day} de {meses[hoje.month]} de {hoje.year}</p>
            <h2 style="color:#c8a96e;margin:0.8rem 0;">⭐ {santo_nome}</h2>
            <p style="color:#1a1a1a;font-size:0.9rem;line-height:1.7;margin-top:1rem;">Que a intercessão deste santo(a) nós alcance as graças de que tanto precisamos. Que sua vida sejá inspiração para nós neste dia. Amem.</p>
        </div>
        """, unsafe_allow_html=True)
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
            més = (h + l - 7*m + 114) // 31
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
        elif hoje <= péntecostes:
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
            🕊️ Pentecostes: {péntecostes.strftime("%d/%m")}<br>
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

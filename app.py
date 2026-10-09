import streamlit as st
import streamlit.components.v1 as components
import json
import re
from groq import Groq
import io
import numpy as np
import soundfile as sf

try:
    from kokoro import KPipeline
except Exception:
    KPipeline = None
from supabase import create_client
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="JARVIS AI",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# 2. CONEXÃO COM A GROQ
# ============================================================

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)


# ============================================================
# 2.0. KOKORO TTS - VOZ LOCAL E GRATUITA
# ============================================================

@st.cache_resource(show_spinner=False)
def carregar_pipeline_kokoro():

    if KPipeline is None:
        return None

    return KPipeline(lang_code="p")


def limpar_texto_para_voz(texto):
    """Remove marcações Markdown que não devem ser pronunciadas."""
    if not texto:
        return ""

    texto = str(texto)

    # Mantém o texto de links Markdown, removendo a URL.
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)

    # Remove blocos de código e marcações comuns de Markdown.
    texto = re.sub(r"```[\s\S]*?```", " ", texto)
    texto = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", texto)
    texto = re.sub(r"[*_~`#]", "", texto)

    # Em números isolados de dois dígitos, remove o zero à esquerda:
    # "09" vira "9" para o Kokoro dizer "nove", não "zero nove".
    # Não altera números maiores nem valores ligados a datas/horários/códigos.
    texto = re.sub(r"(?<![\d/:-])0([1-9])(?![\d/:-])", r"\1", texto)

    # Normaliza espaços para uma fala mais natural.
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def separar_frases_para_voz(texto):
    """Divide o texto em frases para inserir pausas naturais no áudio."""
    frases = re.split(r"(?<=[.!?])\s+", texto.strip())
    return [frase.strip() for frase in frases if frase.strip()]


def falar_texto(texto, persona="🤖 JARVIS"):

    """Converte a resposta em áudio com pausas entre frases usando Kokoro."""

    texto = limpar_texto_para_voz(texto)
    if not texto:
        return

    if KPipeline is None:
        st.error(
            "Kokoro não está instalado. Adicione 'kokoro' e 'soundfile' "
            "ao requirements.txt e 'espeak-ng' ao packages.txt."
        )
        return

    try:
        pipeline = carregar_pipeline_kokoro()
        voz = PERSONAS.get(
            persona,
            PERSONAS["🤖 JARVIS"]
        )["voice"]

        partes_audio = []
        frases = separar_frases_para_voz(texto)
        pausa_curta = np.zeros(int(24000 * 0.20), dtype=np.float32)

        # Sintetiza cada frase separadamente para que as pausas sejam audíveis.
        for indice, frase in enumerate(frases):
            generator = pipeline(frase, voice=voz)
            audio_frase = []

            for _, _, audio in generator:
                audio_frase.append(np.asarray(audio, dtype=np.float32))

            if audio_frase:
                partes_audio.append(np.concatenate(audio_frase))
                if indice < len(frases) - 1:
                    partes_audio.append(pausa_curta)

        if not partes_audio:
            st.warning("O Kokoro não gerou áudio para esta resposta.")
            return

        audio_completo = np.concatenate(partes_audio)

        buffer = io.BytesIO()
        sf.write(
            buffer,
            audio_completo,
            24000,
            format="WAV"
        )

        audio_bytes = buffer.getvalue()

        st.caption(
            f"🔊 Voz: {voz} • Persona: "
            f"{PERSONAS.get(persona, PERSONAS['🤖 JARVIS'])['description']}"
        )

        st.audio(
            audio_bytes,
            format="audio/wav"
        )

    except Exception as e:
        st.error(
            f"Erro ao gerar a voz com o Kokoro: {e}"
        )


# ============================================================
# 3. CONEXÃO COM O SUPABASE
# ============================================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


# ============================================================
# 4. MODELO
# ============================================================

MODEL_NAME = "openai/gpt-oss-20b"


# ============================================================
# 4.1. PERSONAS - VOZ + PERSONALIDADE
# ============================================================

PERSONAS = {
    "🤖 JARVIS": {
        "description": "Elegante, profissional e analítico",
        "voice": "pm_alex",
        "prompt": (
            "Você é JARVIS. Mantenha uma personalidade elegante, "
            "profissional, analítica e extremamente prestativa. "
            "Fale com calma, precisão e confiança. Seja sofisticado "
            "sem parecer artificial ou excessivamente formal."
        )
    },
    "😎 FRIDAY": {
        "description": "Amigável, descontraída e inteligente",
        "voice": "pf_dora",
        "prompt": (
            "Você é FRIDAY, uma assistente inteligente, amigável e "
            "descontraída. Converse de forma natural, simpática e "
            "confiante. Pode usar um pouco mais de leveza e humor "
            "quando for apropriado, sem perder a utilidade."
        )
    },
    "💪 KRATOS": {
        "description": "Sério, disciplinado e determinado",
        "voice": "pm_santa",
        "prompt": (
            "Você possui uma personalidade inspirada em um guerreiro "
            "sério, disciplinado e determinado. Responda de forma "
            "direta, firme e controlada. Evite exageros, piadas e "
            "frases desnecessariamente longas. Transmita força, "
            "experiência e determinação, mantendo respeito pelo usuário."
        )
    }
}


# ============================================================
# 5. DATA E HORA DO BRASIL
# ============================================================

def obter_data_hora():

    agora = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    )

    data = agora.strftime("%d/%m/%Y")
    hora = agora.strftime("%H:%M")

    return data, hora


# ============================================================
# 6. FUNÇÕES DE AUTENTICAÇÃO
# ============================================================

def limpar_login():

    st.session_state.pop("access_token", None)
    st.session_state.pop("refresh_token", None)
    st.session_state.pop("user", None)


def fazer_login(email, senha):

    try:

        resposta = supabase.auth.sign_in_with_password({
            "email": email,
            "password": senha
        })

        if resposta.session is None:

            return False, "Não foi possível iniciar a sessão."

        st.session_state.access_token = (
            resposta.session.access_token
        )

        st.session_state.refresh_token = (
            resposta.session.refresh_token
        )

        if resposta.user:

            st.session_state.user = resposta.user

        return True, "Login realizado com sucesso!"

    except Exception as e:

        return False, str(e)


def criar_conta(email, senha):

    try:

        resposta = supabase.auth.sign_up({
            "email": email,
            "password": senha
        })

        # ----------------------------------------------------
        # Se o Supabase exigir confirmação de e-mail
        # ----------------------------------------------------

        if resposta.session is None:

            return (
                True,
                "Conta criada! Verifique seu e-mail "
                "para confirmar a conta."
            )

        # ----------------------------------------------------
        # Se a confirmação não for necessária
        # ----------------------------------------------------

        if resposta.session:

            st.session_state.access_token = (
                resposta.session.access_token
            )

            st.session_state.refresh_token = (
                resposta.session.refresh_token
            )

            st.session_state.user = resposta.user

            return True, "Conta criada com sucesso!"

    except Exception as e:

        return False, str(e)

    return False, "Não foi possível criar a conta."


# ============================================================
# 7. RECUPERAR SESSÃO
# ============================================================

if (
    "access_token" in st.session_state
    and "refresh_token" in st.session_state
):

    try:

        resposta = supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )

        if resposta.session:

            st.session_state.access_token = (
                resposta.session.access_token
            )

            st.session_state.refresh_token = (
                resposta.session.refresh_token
            )

        usuario_resposta = supabase.auth.get_user()

        if usuario_resposta.user:

            st.session_state.user = (
                usuario_resposta.user
            )

    except Exception:

        limpar_login()


# ============================================================
# 8. TELA DE LOGIN
# ============================================================

if "user" not in st.session_state:

    st.title("🤖 JARVIS AI")

    st.subheader("🔐 Acesso ao JARVIS")

    aba_login, aba_cadastro = st.tabs([
        "Entrar",
        "Criar conta"
    ])


    # ========================================================
    # LOGIN
    # ========================================================

    with aba_login:

        with st.form("login_form"):

            email = st.text_input(
                "E-mail",
                placeholder="seu@email.com"
            )

            senha = st.text_input(
                "Senha",
                type="password"
            )

            entrar = st.form_submit_button(
                "🔐 Entrar",
                use_container_width=True
            )


        if entrar:

            if not email or not senha:

                st.warning(
                    "Digite seu e-mail e sua senha."
                )

            else:

                sucesso, mensagem = fazer_login(
                    email,
                    senha
                )

                if sucesso:

                    st.success(mensagem)

                    st.rerun()

                else:

                    st.error(
                        f"Erro ao entrar: {mensagem}"
                    )


    # ========================================================
    # CADASTRO
    # ========================================================

    with aba_cadastro:

        with st.form("cadastro_form"):

            novo_email = st.text_input(
                "E-mail",
                placeholder="seu@email.com"
            )

            nova_senha = st.text_input(
                "Senha",
                type="password"
            )

            confirmar_senha = st.text_input(
                "Confirmar senha",
                type="password"
            )

            cadastrar = st.form_submit_button(
                "🆕 Criar conta",
                use_container_width=True
            )


        if cadastrar:

            if not novo_email or not nova_senha:

                st.warning(
                    "Preencha todos os campos."
                )

            elif nova_senha != confirmar_senha:

                st.error(
                    "As senhas não são iguais."
                )

            elif len(nova_senha) < 6:

                st.error(
                    "A senha precisa ter pelo menos 6 caracteres."
                )

            else:

                sucesso, mensagem = criar_conta(
                    novo_email,
                    nova_senha
                )

                if sucesso:

                    st.success(mensagem)

                    if "user" in st.session_state:

                        st.rerun()

                else:

                    st.error(
                        f"Erro ao criar conta: {mensagem}"
                    )


    # ========================================================
    # PARAR O PROGRAMA
    # ========================================================

    st.stop()


# ============================================================
# 9. USUÁRIO LOGADO
# ============================================================

usuario = st.session_state.user

user_id = str(usuario.id)

user_email = usuario.email


# ============================================================
# 9.1. CONFIGURAÇÃO DA PERSONA DO USUÁRIO
# ============================================================

def carregar_persona():

    try:
        resultado = (
            supabase
            .table("user_settings")
            .select("persona")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        if resultado.data and resultado.data.get("persona") in PERSONAS:
            return resultado.data["persona"]

    except Exception:
        # Se a tabela ainda não existir, o JARVIS continua funcionando
        # usando a configuração desta sessão.
        pass

    return "🤖 JARVIS"


def salvar_persona(persona):

    try:
        supabase.table("user_settings").upsert({
            "user_id": user_id,
            "persona": persona,
            "updated_at": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
        }).execute()
        return True
    except Exception:
        # A persona continua funcionando mesmo sem a tabela opcional.
        return False


if "persona" not in st.session_state:
    st.session_state.persona = carregar_persona()


# ============================================================
# 10. MEMÓRIA PERMANENTE
# ============================================================

def salvar_memoria(categoria, conteudo):

    try:

        supabase.table("memories").insert({

            "user_id": user_id,

            "category": categoria,

            "content": conteudo

        }).execute()

        return True

    except Exception as e:

        print(
            f"Erro ao salvar memória: {e}"
        )

        return False


def carregar_memorias():

    try:

        resultado = (
            supabase
            .table("memories")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )

        return resultado.data

    except Exception as e:

        print(
            f"Erro ao carregar memórias: {e}"
        )

        return []


def criar_contexto_memoria():

    memorias = carregar_memorias()

    if not memorias:

        return (
            "O usuário ainda não possui "
            "memórias salvas."
        )

    contexto = """
Estas são informações que você deve lembrar
sobre o usuário atual.

Use essas informações quando forem relevantes
para responder.

"""

    for memoria in memorias:

        contexto += (
            f"- {memoria['category']}: "
            f"{memoria['content']}\n"
        )

    return contexto


# ============================================================
# 11. CONVERSAS
# ============================================================

if "chats" not in st.session_state:

    st.session_state.chats = {

        "Conversa 1": [

            {
                "role": "system",

                "content": (
                    "Você é o JARVIS, um assistente virtual "
                    "inteligente, prestativo e amigável."
                )
            }

        ]

    }


# ============================================================
# 12. CONVERSA ATIVA
# ============================================================

if "active_chat_id" not in st.session_state:

    st.session_state.active_chat_id = "Conversa 1"


# ============================================================
# 13. BARRA LATERAL
# ============================================================

with st.sidebar:

    st.title("🤖 JARVIS AI")

    st.caption(
        f"Modelo: {MODEL_NAME}"
    )

    st.markdown("---")


    # ========================================================
    # PERSONA
    # ========================================================

    st.subheader("🎭 Persona")

    persona_selecionada = st.selectbox(
        "Escolha quem vai falar com você:",
        list(PERSONAS.keys()),
        index=list(PERSONAS.keys()).index(st.session_state.persona),
        format_func=lambda nome: f"{nome} — {PERSONAS[nome]['description']}"
    )

    if persona_selecionada != st.session_state.persona:
        st.session_state.persona = persona_selecionada
        salvar_persona(persona_selecionada)
        st.rerun()

    st.caption(
        f"🧠 Personalidade: {PERSONAS[st.session_state.persona]['description']}"
    )

    if st.button("🔊 Testar voz", use_container_width=True):
        texto_teste = {
            "🤖 JARVIS": "Olá. Sou JARVIS. Sistemas operacionais e prontos.",
            "😎 FRIDAY": "Oi! Sou FRIDAY. Tudo pronto por aqui.",
            "💪 KRATOS": "Estou pronto. Diga o que precisa ser feito."
        }[st.session_state.persona]
        falar_texto(texto_teste, st.session_state.persona)

    st.markdown("---")

    # ========================================================
    # CONTA
    # ========================================================

    st.subheader("👤 Conta")

    st.write(user_email)


    # ========================================================
    # LOGOUT
    # ========================================================

    if st.button(
        "🚪 Sair",
        use_container_width=True
    ):

        try:

            supabase.auth.sign_out({
                "scope": "local"
            })

        except Exception:

            pass

        limpar_login()

        st.rerun()


    st.markdown("---")


    # ========================================================
    # NOVA CONVERSA
    # ========================================================

    if st.button(
        "➕ Nova conversa",
        use_container_width=True
    ):

        new_id = (
            f"Conversa "
            f"{len(st.session_state.chats) + 1}"
        )

        st.session_state.chats[new_id] = [

            {
                "role": "system",

                "content": (
                    "Você é o JARVIS, um assistente virtual "
                    "inteligente, prestativo e amigável."
                )
            }

        ]

        st.session_state.active_chat_id = new_id

        st.rerun()


    st.markdown("---")

    st.subheader("💬 Conversas")


    # ========================================================
    # LISTA DE CONVERSAS
    # ========================================================

    for chat_id in list(
        st.session_state.chats.keys()
    ):

        if st.button(
            f"💬 {chat_id}",
            key=chat_id,
            use_container_width=True
        ):

            st.session_state.active_chat_id = chat_id

            st.rerun()


    st.markdown("---")

    st.subheader("🧠 Memória")


    # ========================================================
    # MOSTRAR MEMÓRIAS
    # ========================================================

    memorias = carregar_memorias()


    if memorias:

        st.write(
            f"{len(memorias)} memória(s) "
            f"armazenada(s)"
        )

    else:

        st.write(
            "Nenhuma memória armazenada."
        )


# ============================================================
# 14. CONVERSA ATUAL
# ============================================================

current_chat_id = (
    st.session_state.active_chat_id
)

messages = (
    st.session_state.chats[current_chat_id]
)


# ============================================================
# 15. TÍTULO
# ============================================================

st.title(
    f"🤖 JARVIS AI - {current_chat_id}"
)


# ============================================================
# 16. MOSTRAR HISTÓRICO
# ============================================================

for message in messages:

    if message["role"] != "system":

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


# ============================================================
# 17. ENTRADA DO USUÁRIO
# ============================================================

col1, col2 = st.columns([4, 1])

with col1:

    prompt_texto = st.chat_input(
        "Digite sua mensagem para o JARVIS..."
    )

with col2:

    audio_input = st.audio_input(
        "🎤 Falar",
        sample_rate=16000
    )


# ============================================================
# TRANSFORMAR VOZ EM TEXTO
# ============================================================

prompt = prompt_texto


if audio_input is not None:

    with st.spinner(
        "🎧 JARVIS está ouvindo..."
    ):

        texto_transcrito = transcrever_audio(
            audio_input
        )

    if texto_transcrito:

        prompt = texto_transcrito

        st.info(
            f"🎤 Você disse: **{texto_transcrito}**"
        )


# ============================================================
# 18. PROCESSAR MENSAGEM
# ============================================================

if prompt:

    # ========================================================
    # MOSTRAR MENSAGEM DO USUÁRIO
    # ========================================================

    with st.chat_message("user"):

        st.markdown(prompt)


    # ========================================================
    # SALVAR MENSAGEM
    # ========================================================

    messages.append({

        "role": "user",

        "content": prompt

    })


    # ========================================================
    # 19. DETECTAR O NOME DO USUÁRIO
    # ========================================================

    prompt_lower = prompt.lower()

    frases_nome = [

        "meu nome é",
        "meu nome e",
        "me chamo",
        "eu me chamo",
        "pode me chamar de"

    ]


    for frase in frases_nome:

        if frase in prompt_lower:

            try:

                inicio = (
                    prompt_lower.find(frase)
                    + len(frase)
                )

                parte = (
                    prompt[inicio:]
                    .strip()
                )

                nome = (
                    parte
                    .split(".")[0]
                    .split(",")[0]
                    .strip()
                )

                if nome:

                    salvar_memoria(
                        "nome",
                        nome
                    )

            except Exception:

                pass

            break


    # ========================================================
    # 20. DATA E HORA ATUAIS
    # ========================================================

    data_atual, hora_atual = (
        obter_data_hora()
    )


    # ========================================================
    # 21. CARREGAR MEMÓRIA
    # ========================================================

    memoria = criar_contexto_memoria()


    # ========================================================
    # 22. PREPARAR MENSAGENS
    # ========================================================

    mensagens_para_ia = [

        {
            "role": "system",

            "content": (

                PERSONAS[st.session_state.persona]["prompt"] + " "

                "Você é um assistente virtual avançado, "
                "inteligente, prestativo, educado e natural. "

                "Seu objetivo é conversar com o usuário "
                "de maneira semelhante a um assistente "
                "pessoal sofisticado. "

                "Responda sempre em português do Brasil, "
                "a menos que o usuário peça outro idioma. "

                f"A data atual no Brasil é {data_atual}. "
                f"O horário atual no Brasil é {hora_atual}. "

                "Nunca invente a data ou o horário atual. "

                "Você possui acesso à ferramenta "
                "browser_search. "

                "Quando uma pergunta depender de "
                "informações atuais, recentes ou que "
                "possam ter mudado desde seu treinamento, "
                "pesquise na internet antes de responder. "

                "Isso inclui notícias, política atual, "
                "presidentes, governadores, prefeitos, "
                "eleições, resultados de jogos, preços, "
                "cotações, clima, lançamentos, versões "
                "de software, acontecimentos recentes "
                "e informações sobre pessoas ou empresas "
                "que possam ter mudado. "

                "Perguntas de acompanhamento também "
                "devem ser interpretadas considerando "
                "o contexto da conversa anterior. "

                "Por exemplo, se o usuário perguntar "
                "'quem é o atual presidente?' e depois "
                "perguntar 'qual a chance dele ser "
                "reeleito?', entenda que 'dele' se refere "
                "à pessoa mencionada anteriormente. "

                "Quando a pergunta envolver uma previsão "
                "ou probabilidade sobre um acontecimento "
                "futuro, não invente uma porcentagem. "
                "Explique os fatores relevantes e, quando "
                "existirem pesquisas ou estimativas atuais, "
                "consulte fontes recentes. "

                "Não invente fontes, fatos, números ou "
                "resultados de pesquisas. "

                "Se a informação encontrada na internet "
                "for insuficiente ou conflitante, deixe "
                "isso claro para o usuário. "

                "Se a pergunta não precisar de informações "
                "atuais, responda normalmente sem realizar "
                "uma pesquisa desnecessária."

            )
        },

        {
            "role": "system",

            "content": memoria

        }

    ]


    # ========================================================
    # 23. ADICIONAR HISTÓRICO
    # ========================================================

    mensagens_para_ia.extend(
        messages[1:]
    )


    # ========================================================
    # 24. CONFIGURAÇÃO DA GROQ
    # ========================================================

    parametros = {

        "model": MODEL_NAME,

        "messages": mensagens_para_ia,

        "temperature": 0.7,

        "tools": [

            {
                "type": "browser_search"
            }

        ],

        "tool_choice": "auto"

    }


    # ========================================================
    # 25. GERAR RESPOSTA
    # ========================================================

    with st.chat_message("assistant"):

        try:

            completion = (
                client
                .chat
                .completions
                .create(
                    **parametros
                )
            )


            # =================================================
            # PEGAR RESPOSTA
            # =================================================

            response = (
                completion
                .choices[0]
                .message
                .content
            )


            # =================================================
            # VERIFICAR RESPOSTA VAZIA
            # =================================================

            if not response:

                response = (
                    "Desculpe, não consegui gerar "
                    "uma resposta agora."
                )


            # =================================================
            # MOSTRAR RESPOSTA
            # =================================================

            st.markdown(response)


            # =================================================
            # BOTÕES DE VOZ
            # =================================================

            falar_texto(response, st.session_state.persona)


            # =================================================
            # SALVAR RESPOSTA NA CONVERSA
            # =================================================

            messages.append({

                "role": "assistant",

                "content": response

            })


        except Exception as e:

            st.error(
                f"Erro ao gerar resposta: {e}"
            )

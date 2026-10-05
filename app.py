import streamlit as st
import streamlit.components.v1 as components
import json
from groq import Groq
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
# 2.1. VOZ - TRANSCRIÇÃO E FALA
# ============================================================

VOICE_MODEL = "whisper-large-v3-turbo"


def transcrever_audio(audio_file):

    try:

        audio_bytes = audio_file.getvalue()

        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model=VOICE_MODEL,
            language="pt",
            response_format="json",
            temperature=0
        )

        texto = transcription.text.strip()

        return texto

    except Exception as e:

        st.error(
            f"Erro ao transcrever o áudio: {e}"
        )

        return ""


def falar_texto(texto):

    """
    Usa a voz disponível no navegador para falar em português.
    Não precisa de uma API de TTS separada.
    """

    try:

        texto_seguro = json.dumps(texto, ensure_ascii=False)

        html = f"""
        <script>
        const texto = {texto_seguro};

        function falar() {{
            if (!('speechSynthesis' in window)) {{
                return;
            }}

            window.speechSynthesis.cancel();

            const fala = new SpeechSynthesisUtterance(texto);
            fala.lang = 'pt-BR';
            fala.rate = 1.0;
            fala.pitch = 0.95;
            fala.volume = 1.0;

            const vozes = window.speechSynthesis.getVoices();
            const vozPortugues = vozes.find(voz =>
                voz.lang && voz.lang.toLowerCase().startsWith('pt-br')
            ) || vozes.find(voz =>
                voz.lang && voz.lang.toLowerCase().startsWith('pt')
            );

            if (vozPortugues) {{
                fala.voice = vozPortugues;
            }}

            window.speechSynthesis.speak(fala);
        }}

        if (window.speechSynthesis.getVoices().length === 0) {{
            window.speechSynthesis.addEventListener(
                'voiceschanged', falar, {{ once: true }}
            );
        }} else {{
            falar();
        }}
        </script>
        """

        components.html(
            html,
            height=1,
            scrolling=False
        )

    except Exception as e:

        st.warning(
            f"Não foi possível reproduzir a voz: {e}"
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

                "Você é JARVIS, um assistente virtual "
                "avançado, inteligente, prestativo, "
                "educado e natural. "

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
            # FALAR RESPOSTA EM VOZ ALTA
            # =================================================

            falar_texto(response)


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

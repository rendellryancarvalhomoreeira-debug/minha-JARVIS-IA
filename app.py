import streamlit as st
from groq import Groq
from supabase import create_client


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
# 3. MODELO
# ============================================================

MODEL_NAME = "openai/gpt-oss-20b"


# ============================================================
# 4. MEMÓRIA GLOBAL DO JARVIS
# ============================================================

if "memory" not in st.session_state:

    st.session_state.memory = {
        "nome": "",
        "preferencias": [],
        "informacoes": []
    }


# ============================================================
# 5. CONVERSAS
# ============================================================

if "chats" not in st.session_state:

    st.session_state.chats = {

        "Conversa 1": [

            {
                "role": "system",
                "content": (
                    "Você é o JARVIS, um assistente virtual "
                    "prestativo, inteligente e amigável. "
                    "Responda sempre em português do Brasil, "
                    "a menos que o usuário peça outro idioma."
                )
            }

        ]
    }


# ============================================================
# 6. CONVERSA ATIVA
# ============================================================

if "active_chat_id" not in st.session_state:

    st.session_state.active_chat_id = "Conversa 1"


# ============================================================
# 7. FUNÇÃO PARA CRIAR O CONTEXTO DE MEMÓRIA
# ============================================================

def criar_memoria():

    memoria = st.session_state.memory

    texto = """
Você é o JARVIS.

Estas são informações que você deve lembrar sobre o usuário:

"""

    # Nome
    if memoria["nome"]:

        texto += f"\nNome do usuário: {memoria['nome']}"


    # Preferências
    if memoria["preferencias"]:

        texto += "\n\nPreferências do usuário:"

        for item in memoria["preferencias"]:

            texto += f"\n- {item}"


    # Outras informações
    if memoria["informacoes"]:

        texto += "\n\nOutras informações importantes:"

        for item in memoria["informacoes"]:

            texto += f"\n- {item}"


    return texto


# ============================================================
# 8. BARRA LATERAL
# ============================================================

with st.sidebar:

    st.title("🤖 JARVIS AI")

    st.caption(f"Modelo: {MODEL_NAME}")


    # --------------------------------------------------------
    # NOVA CONVERSA
    # --------------------------------------------------------

    if st.button(
        "➕ Nova conversa",
        use_container_width=True
    ):

        new_id = f"Conversa {len(st.session_state.chats) + 1}"


        st.session_state.chats[new_id] = [

            {
                "role": "system",
                "content": (
                    "Você é o JARVIS, um assistente virtual "
                    "prestativo, inteligente e amigável. "
                    "Responda sempre em português do Brasil, "
                    "a menos que o usuário peça outro idioma."
                )
            }

        ]


        st.session_state.active_chat_id = new_id

        st.rerun()


    st.markdown("---")

    st.subheader("Recentes")


    # --------------------------------------------------------
    # LISTA DE CONVERSAS
    # --------------------------------------------------------

    for chat_id in list(st.session_state.chats.keys()):

        button_label = f"💬 {chat_id}"


        if st.button(
            button_label,
            key=chat_id,
            use_container_width=True
        ):

            st.session_state.active_chat_id = chat_id

            st.rerun()


    # --------------------------------------------------------
    # MOSTRAR MEMÓRIA
    # --------------------------------------------------------

    st.markdown("---")

    st.subheader("🧠 Memória")


    if st.session_state.memory["nome"]:

        st.write(
            f"👤 Nome: {st.session_state.memory['nome']}"
        )

    else:

        st.write("👤 Nome: não informado")


    if st.session_state.memory["preferencias"]:

        st.write(
            f"⭐ Preferências: "
            f"{len(st.session_state.memory['preferencias'])}"
        )


# ============================================================
# 9. CONVERSA ATUAL
# ============================================================

current_chat_id = st.session_state.active_chat_id


st.title(
    f"🤖 JARVIS AI - ({current_chat_id})"
)


messages = st.session_state.chats[current_chat_id]


# ============================================================
# 10. MOSTRAR HISTÓRICO
# ============================================================

for message in messages:

    if message["role"] != "system":

        with st.chat_message(message["role"]):

            st.markdown(message["content"])


# ============================================================
# 11. ENTRADA DO USUÁRIO
# ============================================================

prompt = st.chat_input(
    "Pergunte qualquer coisa ao JARVIS..."
)


# ============================================================
# 12. PROCESSAMENTO
# ============================================================

if prompt:


    # --------------------------------------------------------
    # MOSTRA MENSAGEM
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(prompt)


    # --------------------------------------------------------
    # SALVA MENSAGEM
    # --------------------------------------------------------

    messages.append({

        "role": "user",

        "content": prompt

    })


    # ========================================================
    # 13. DETECTAR NOME
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

                nome = prompt_lower.split(frase, 1)[1]

                nome = nome.strip()

                nome = nome.split(".")[0]

                nome = nome.split(",")[0]

                nome = nome.strip()


                if nome:

                    # Recupera o texto original
                    parte_original = prompt.split(
                        frase,
                        1
                    )[1].strip()


                    nome_original = parte_original.split(
                        "."
                    )[0].split(",")[0].strip()


                    st.session_state.memory["nome"] = (
                        nome_original
                    )

            except:

                pass


    # ========================================================
    # 14. CONSTRUIR CONTEXTO COM MEMÓRIA
    # ========================================================

    memoria = criar_memoria()


    # Criamos uma cópia das mensagens
    mensagens_para_ia = list(messages)


    # Inserimos a memória antes da conversa
    mensagens_para_ia.insert(

        1,

        {
            "role": "system",
            "content": memoria
        }

    )


    # ========================================================
    # 15. GERAR RESPOSTA
    # ========================================================

    with st.chat_message("assistant"):

        try:

            completion = client.chat.completions.create(

                model=MODEL_NAME,

                messages=mensagens_para_ia,

                temperature=0.7

            )


            response = (
                completion
                .choices[0]
                .message
                .content
            )


            st.markdown(response)


            # ------------------------------------------------
            # SALVA RESPOSTA
            # ------------------------------------------------

            messages.append({

                "role": "assistant",

                "content": response

            })


        except Exception as e:

            st.error(
                f"Erro ao gerar resposta: {e}"
            )

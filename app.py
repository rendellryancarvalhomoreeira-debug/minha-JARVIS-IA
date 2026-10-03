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
# 5. MEMÓRIA PERMANENTE
# ============================================================

def salvar_memoria(categoria, conteudo):

    try:

        supabase.table("memories").insert({
            "category": categoria,
            "content": conteudo
        }).execute()

        return True

    except Exception as e:

        print(f"Erro ao salvar memória: {e}")

        return False


def carregar_memorias():

    try:

        resultado = (
            supabase
            .table("memories")
            .select("*")
            .order("created_at", desc=False)
            .execute()
        )

        return resultado.data

    except Exception as e:

        print(f"Erro ao carregar memórias: {e}")

        return []


def criar_contexto_memoria():

    memorias = carregar_memorias()

    if not memorias:

        return "O usuário ainda não possui memórias salvas."

    contexto = """
Estas são informações que você deve lembrar sobre o usuário.

Use essas informações quando forem relevantes para responder.

"""

    for memoria in memorias:

        contexto += (
            f"- {memoria['category']}: "
            f"{memoria['content']}\n"
        )

    return contexto


# ============================================================
# 6. CONVERSAS
# ============================================================

if "chats" not in st.session_state:

    st.session_state.chats = {

        "Conversa 1": [

            {
                "role": "system",
                "content": (
                    "Você é o JARVIS, um assistente virtual "
                    "inteligente, prestativo e amigável. "
                    "Responda sempre em português do Brasil, "
                    "a menos que o usuário peça outro idioma."
                )
            }

        ]
    }


# ============================================================
# 7. CONVERSA ATIVA
# ============================================================

if "active_chat_id" not in st.session_state:

    st.session_state.active_chat_id = "Conversa 1"


# ============================================================
# 8. BARRA LATERAL
# ============================================================

with st.sidebar:

    st.title("🤖 JARVIS AI")

    st.caption(f"Modelo: {MODEL_NAME}")

    st.markdown("---")


    # --------------------------------------------------------
    # NOVA CONVERSA
    # --------------------------------------------------------

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
                    "inteligente, prestativo e amigável. "
                    "Responda sempre em português do Brasil, "
                    "a menos que o usuário peça outro idioma."
                )
            }

        ]

        st.session_state.active_chat_id = new_id

        st.rerun()


    st.markdown("---")

    st.subheader("💬 Conversas")


    # --------------------------------------------------------
    # LISTA DE CONVERSAS
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # MOSTRAR MEMÓRIAS
    # --------------------------------------------------------

    memorias = carregar_memorias()


    if memorias:

        st.write(
            f"{len(memorias)} memória(s) armazenada(s)"
        )

    else:

        st.write("Nenhuma memória armazenada.")


# ============================================================
# 9. CONVERSA ATUAL
# ============================================================

current_chat_id = st.session_state.active_chat_id

messages = st.session_state.chats[current_chat_id]


# ============================================================
# 10. TÍTULO
# ============================================================

st.title(
    f"🤖 JARVIS AI - {current_chat_id}"
)


# ============================================================
# 11. MOSTRAR HISTÓRICO
# ============================================================

for message in messages:

    if message["role"] != "system":

        with st.chat_message(message["role"]):

            st.markdown(
                message["content"]
            )


# ============================================================
# 12. ENTRADA DO USUÁRIO
# ============================================================

prompt = st.chat_input(
    "Pergunte qualquer coisa ao JARVIS..."
)


# ============================================================
# 13. PROCESSAR MENSAGEM
# ============================================================

if prompt:

    # --------------------------------------------------------
    # MOSTRA A MENSAGEM DO USUÁRIO
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(prompt)


    # --------------------------------------------------------
    # SALVA A MENSAGEM NA CONVERSA
    # --------------------------------------------------------

    messages.append({

        "role": "user",

        "content": prompt

    })


    # ========================================================
    # 14. DETECTAR O NOME DO USUÁRIO
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

                # Pega a parte depois da frase
                parte = prompt.split(
                    frase,
                    1
                )[1].strip()


                # Remove pontuação básica
                nome = (
                    parte
                    .split(".")[0]
                    .split(",")[0]
                    .strip()
                )


                if nome:

                    # Salva permanentemente no Supabase
                    salvar_memoria(
                        "nome",
                        nome
                    )

            except Exception:

                pass


    # ========================================================
    # 15. CARREGAR MEMÓRIA
    # ========================================================

    memoria = criar_contexto_memoria()


    # ========================================================
    # 16. PREPARAR MENSAGENS PARA A GROQ
    # ========================================================

    mensagens_para_ia = [

        {
            "role": "system",
            "content": (
                "Você é o JARVIS, um assistente virtual "
                "inteligente, prestativo e amigável. "
                "Responda sempre em português do Brasil, "
                "a menos que o usuário peça outro idioma."
            )
        },

        {
            "role": "system",
            "content": memoria
        }

    ]


    # Adiciona o histórico da conversa atual
    mensagens_para_ia.extend(
        messages[1:]
    )


    # ========================================================
    # 17. GERAR RESPOSTA
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


            # Mostra resposta
            st.markdown(response)


            # ------------------------------------------------
            # SALVA RESPOSTA NA CONVERSA
            # ------------------------------------------------

            messages.append({

                "role": "assistant",

                "content": response

            })


        except Exception as e:

            st.error(
                f"Erro ao gerar resposta: {e}"
            )

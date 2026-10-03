import streamlit as st
from groq import Groq

# ============================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="JARVIS AI",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# 2. INICIALIZAÇÃO DA GROQ
# ============================================================

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)


# ============================================================
# 3. MODELO
# ============================================================

MODEL_NAME = "openai/gpt-oss-20b"


# ============================================================
# 4. GERENCIAMENTO DAS CONVERSAS
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


if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = "Conversa 1"


# ============================================================
# 5. BARRA LATERAL
# ============================================================

with st.sidebar:

    st.title("🤖 JARVIS AI")

    st.caption(f"Modelo: {MODEL_NAME}")

    # --------------------------------------------------------
    # NOVA CONVERSA
    # --------------------------------------------------------

    if st.button("➕ Nova conversa", use_container_width=True):

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


# ============================================================
# 6. ÁREA PRINCIPAL DO CHAT
# ============================================================

current_chat_id = st.session_state.active_chat_id

st.title(f"🤖 JARVIS AI - ({current_chat_id})")


# Recupera as mensagens da conversa atual
messages = st.session_state.chats[current_chat_id]


# ============================================================
# 7. MOSTRAR HISTÓRICO DA CONVERSA
# ============================================================

for message in messages:

    if message["role"] != "system":

        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# ============================================================
# 8. ENTRADA DO USUÁRIO
# ============================================================

prompt = st.chat_input(
    "Pergunte sobre notícias, jogos ou qualquer assunto..."
)


# ============================================================
# 9. PROCESSAMENTO DA MENSAGEM
# ============================================================

if prompt:

    # --------------------------------------------------------
    # MOSTRA A MENSAGEM DO USUÁRIO
    # --------------------------------------------------------

    with st.chat_message("user"):
        st.markdown(prompt)


    # --------------------------------------------------------
    # SALVA A MENSAGEM
    # --------------------------------------------------------

    messages.append({
        "role": "user",
        "content": prompt
    })


    # --------------------------------------------------------
    # GERA A RESPOSTA DO JARVIS
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        try:

            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.7
            )

            response = completion.choices[0].message.content

            st.markdown(response)


            # ------------------------------------------------
            # SALVA A RESPOSTA
            # ------------------------------------------------

            messages.append({
                "role": "assistant",
                "content": response
            })


        except Exception as e:

            st.error(
                f"Erro ao gerar resposta: {e}"
            )

import streamlit as st
from groq import Groq

# Configuração da página
st.set_page_config(page_title="JARVIS AI", page_icon="🤖", layout="wide")

# Inicializa o cliente da Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# OBTÉM APENAS MODELOS DE TEXTO (Filtra modelos de áudio como Whisper)
@st.cache_data(ttl=3600)
def get_working_text_model():
    try:
        models = client.models.list()
        # Filtra apenas modelos que contêm 'llama' ou 'gemma' e ignoram 'whisper'
        for model in models.data:
            model_id = model.id.lower()
            if ("llama" in model_id or "gemma" in model_id) and "whisper" not in model_id:
                return model.id
        # Fallback para o modelo padrão caso não encontre na lista
        return "llama-3.3-70b-versatile"
    except Exception:
        return "llama-3.3-70b-versatile"

MODEL_NAME = get_working_text_model()

# 1. GERENCIAMENTO DE CONVERSAS NO SESSION STATE
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = "Conversa 1"
    st.session_state.chats["Conversa 1"] = [
        {"role": "system", "content": "Você é o JARVIS, um assistente virtual prestativo, inteligente e amigável."}
    ]

# 2. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    st.title("🤖 JARVIS AI")
    st.caption(f"Modelo de texto: `{MODEL_NAME}`")
    
    if st.button("➕ Nova conversa", use_container_width=True):
        new_id = f"Conversa {len(st.session_state.chats) + 1}"
        st.session_state.chats[new_id] = [
            {"role": "system", "content": "Você é o JARVIS, um assistente virtual prestativo, inteligente e amigável."}
        ]
        st.session_state.active_chat_id = new_id
        st.rerun()

    st.markdown("---")
    st.subheader("Recentes")
    
    for chat_id in list(st.session_state.chats.keys()):
        button_label = f"💬 {chat_id}"
        if st.button(button_label, key=chat_id, use_container_width=True):
            st.session_state.active_chat_id = chat_id
            st.rerun()

# 3. ÁREA PRINCIPAL DO CHAT
current_chat_id = st.session_state.active_chat_id
st.title(f"🤖 JARVIS AI - ({current_chat_id})")

messages = st.session_state.chats[current_chat_id]

for message in messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 4. ENTRADA E PROCESSAMENTO
if prompt := st.chat_input("Pergunte sobre notícias, jogos ou qualquer assunto..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.7
            )
            response = completion.choices[0].message.content
            st.markdown(response)
            
            messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            st.error(f"Erro ao gerar resposta: {e}")

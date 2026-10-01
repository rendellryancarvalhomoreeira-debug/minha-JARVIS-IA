import streamlit as st
from groq import Groq

# Configuração da página
st.set_page_config(page_title="JARVIS AI", page_icon="🤖")
st.title("🤖 JARVIS AI")

# Inicializa o cliente da Groq usando a chave dos Secrets
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 1. INICIALIZAÇÃO DA MEMÓRIA
# Se o histórico de mensagens ainda não existir na sessão, cria uma lista vazia
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "Você é o JARVIS, um assistente virtual prestativo, inteligente e amigável."
        }
    ]

# 2. EXIBIÇÃO DO HISTÓRICO NO CHAT
# Exibe todas as mensagens trocadas anteriormente (ignorando a instrução interna do sistema)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 3. ENTRADA DO USUÁRIO E PROCESSAMENTO
if prompt := st.chat_input("Pergunte sobre notícias, jogos ou qualquer assunto..."):
    # Exibe a mensagem do usuário na interface
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Salva a mensagem do usuário no histórico de memória
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Gera a resposta enviando TODO o histórico de conversa acumulado
    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages,
                temperature=0.7,
            )
            response = completion.choices[0].message.content
            st.markdown(response)
            
            # Salva a resposta do JARVIS no histórico de memória
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            st.error(f"Erro ao gerar resposta: {e}")

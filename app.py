import streamlit as st
from groq import Groq
from datetime import datetime
from zoneinfo import ZoneInfo
from gnews import GNews
import os

st.set_page_config(page_title="JARVIS - Assistente IA", page_icon="🤖")
st.title("🤖 JARVIS AI")

# Tenta ler a chave dos Secrets (Streamlit Cloud). Se não encontrar, usa a chave direta
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

# Leitor de notícias focado em conteúdo do Brasil
google_news = GNews(language='pt', country='BR', period='1d', max_results=5)

# Seleção automática do modelo ativo na Groq
try:
    modelos_disponiveis = [m.id for m in client.models.list().data]
    modelos_validos = [
        m for m in modelos_disponiveis
        if not any(termo in m.lower() for termo in ["guard", "whisper", "vision", "embed", "orpheus", "safetensors"])
    ]
    MODELO = next((m for m in modelos_validos if "llama-3.3" in m.lower() or "llama3" in m.lower()), modelos_validos[0])
except Exception:
    MODELO = "llama-3.3-70b-versatile"

def buscar_na_web(query):
    try:
        if any(palavra in query.lower() for palavra in ["noticia", "notícias", "hoje", "manchete", "acontecendo"]):
            noticias = google_news.get_top_news()
        else:
            noticias = google_news.get_news(query)

        if not noticias:
            return "Nenhuma notícia recente foi encontrada para esta busca."

        resultados = []
        for n in noticias[:4]:
            titulo = n.get('title', '')
            descricao = n.get('description', '')
            fonte = n.get('publisher', {}).get('title', 'Fonte')
            resultados.append(f"- [{fonte}] {titulo}: {descricao}")

        return "\n".join(resultados)
    except Exception as e:
        return f"Erro ao buscar notícias: {e}"

fuso_br = ZoneInfo("America/Sao_Paulo")
agora = datetime.now(fuso_br).strftime("%d/%m/%Y às %H:%M:%S")

prompt_sistema = (
    "Você é o JARVIS, um assistente pessoal inteligente, prestativo e bem-humorado. "
    f"A data e hora atuais exatas no Brasil são: {agora}. "
    "Sempre que receber dados de notícias e jogos no contexto, resuma-os com clareza para o usuário."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": prompt_sistema}]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

if prompt := st.chat_input("Pergunte sobre notícias, jogos ou qualquer assunto..."):
    with st.chat_message("user"):
        st.write(prompt)
    
    mensagens_para_envio = list(st.session_state.messages)
    
    with st.chat_message("assistant"):
        with st.spinner("Buscando informações em tempo real..."):
            dados_web = buscar_na_web(prompt)
            prompt_com_contexto = f"Pergunta do usuário: {prompt}\n\nNotícias e dados em tempo real:\n{dados_web}"
            mensagens_para_envio.append({"role": "user", "content": prompt_com_contexto})

            try:
                response = client.chat.completions.create(
                    model=MODELO,
                    messages=mensagens_para_envio,
                    max_tokens=600
                )
                resposta_texto = response.choices[0].message.content
                st.write(resposta_texto)
                
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
            except Exception as e:
                st.error(f"⚠️ Erro ao gerar resposta: {e}")

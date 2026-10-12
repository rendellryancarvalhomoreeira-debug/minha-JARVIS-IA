"""
JARVIS - interface Streamlit

Reaproveita o cérebro e as ferramentas do jarvis.py (precisa estar na mesma pasta).

Uso:
    streamlit run app.py

Requer a variável de ambiente ANTHROPIC_API_KEY.
"""

import hashlib
import io
import os
import tempfile

import anthropic
import speech_recognition as sr
import streamlit as st

from jarvis import IDIOMA, pensar

# ----------------------------------------------------------------------------
# Página e visual
# ----------------------------------------------------------------------------
st.set_page_config(page_title="J.A.R.V.I.S.", page_icon="🤖", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background: radial-gradient(circle at 50% 0%, #0b1d2e 0%, #05080d 70%); }
    h1.jarvis-titulo {
        text-align: center; letter-spacing: 0.5em; font-weight: 300;
        color: #6fe7ff; text-shadow: 0 0 18px rgba(111, 231, 255, 0.55);
        margin-bottom: 0;
    }
    p.jarvis-sub { text-align: center; color: #3d7f8f; letter-spacing: 0.25em; font-size: 0.8rem; }
    [data-testid="stChatMessage"] {
        border: 1px solid rgba(111, 231, 255, 0.18);
        background: rgba(10, 30, 45, 0.55);
        border-radius: 10px;
    }
    </style>
    <h1 class="jarvis-titulo">J.A.R.V.I.S.</h1>
    <p class="jarvis-sub">SISTEMAS ONLINE</p>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Estado e cliente
# ----------------------------------------------------------------------------
if not os.environ.get("ANTHROPIC_API_KEY"):
    st.error("Defina a variável de ambiente ANTHROPIC_API_KEY antes de iniciar o Streamlit.")
    st.stop()


@st.cache_resource
def obter_cliente() -> anthropic.Anthropic:
    return anthropic.Anthropic()


cliente = obter_cliente()

if "historico" not in st.session_state:
    st.session_state.historico = []  # formato da API (inclui tool_use / tool_result)
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []  # só o que aparece na tela: (papel, texto)
if "ultimo_audio" not in st.session_state:
    st.session_state.ultimo_audio = None


# ----------------------------------------------------------------------------
# Voz
# ----------------------------------------------------------------------------
def transcrever(audio_bytes: bytes) -> str:
    """Converte o áudio gravado no navegador (WAV) em texto."""
    reconhecedor = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_bytes)) as fonte:
        dados = reconhecedor.record(fonte)
    try:
        return reconhecedor.recognize_google(dados, language=IDIOMA)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as erro:
        st.sidebar.warning(f"Erro no reconhecimento de voz: {erro}")
        return ""


def gerar_audio(texto: str):
    """Gera a fala em um arquivo WAV e devolve os bytes (ou None se falhar)."""
    try:
        import pyttsx3

        motor = pyttsx3.init()
        for voz in motor.getProperty("voices"):
            info = f"{voz.id} {voz.name} {getattr(voz, 'languages', '')}".lower()
            if "pt" in info or "portug" in info or "brazil" in info:
                motor.setProperty("voice", voz.id)
                break
        motor.setProperty("rate", 175)

        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "fala.wav")
            motor.save_to_file(texto, caminho)
            motor.runAndWait()
            with open(caminho, "rb") as arquivo:
                dados = arquivo.read()
        return dados or None
    except Exception as erro:  # noqa: BLE001
        print(f"(sem voz: {erro})")
        return None


# ----------------------------------------------------------------------------
# Barra lateral
# ----------------------------------------------------------------------------
with st.sidebar:
    st.header("Controles")
    resposta_falada = st.toggle("Resposta falada", value=True)
    audio_gravado = st.audio_input("🎙️ Falar com o JARVIS")
    if st.button("Limpar conversa"):
        st.session_state.historico = []
        st.session_state.mensagens = []
        st.session_state.ultimo_audio = None
        st.rerun()
    st.caption(
        "As ações (abrir sites e programas) acontecem no computador onde o Streamlit está rodando."
    )

# ----------------------------------------------------------------------------
# Histórico na tela
# ----------------------------------------------------------------------------
for papel, texto in st.session_state.mensagens:
    with st.chat_message(papel, avatar="🤖" if papel == "assistant" else None):
        st.markdown(texto)

# ----------------------------------------------------------------------------
# Entrada: microfone ou teclado
# ----------------------------------------------------------------------------
entrada = None

if audio_gravado is not None:
    bytes_audio = audio_gravado.getvalue()
    assinatura = hashlib.md5(bytes_audio).hexdigest()
    if assinatura != st.session_state.ultimo_audio:  # evita reprocessar a mesma gravação
        st.session_state.ultimo_audio = assinatura
        with st.spinner("Transcrevendo..."):
            entrada = transcrever(bytes_audio)
        if not entrada:
            st.sidebar.warning("Não consegui entender o áudio. Tente de novo.")

texto_digitado = st.chat_input("Digite ou use o microfone na barra lateral...")
if texto_digitado:
    entrada = texto_digitado

# ----------------------------------------------------------------------------
# Processamento
# ----------------------------------------------------------------------------
if entrada:
    st.session_state.mensagens.append(("user", entrada))
    with st.chat_message("user"):
        st.markdown(entrada)

    copia_historico = list(st.session_state.historico)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Processando..."):
            try:
                resposta = pensar(cliente, st.session_state.historico, entrada)
            except anthropic.APIError as erro:
                st.session_state.historico[:] = copia_historico  # desfaz a rodada com erro
                resposta = f"Houve um problema ao falar com a API, senhor: {erro}"
        st.markdown(resposta)

        if resposta_falada and resposta:
            audio_resposta = gerar_audio(resposta)
            if audio_resposta:
                st.audio(audio_resposta, format="audio/wav", autoplay=True)

    st.session_state.mensagens.append(("assistant", resposta))

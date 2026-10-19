import streamlit as st
import re
import os
import tempfile
from groq import Groq
from cartesia import Cartesia
from supabase import create_client
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="ORION AI",
    page_icon="🤖",
    layout="wide"
)




def renderizar_resposta(texto):
    """Corrige delimitadores matemáticos comuns antes de renderizar Markdown."""
    if not texto:
        st.markdown("")
        return

    texto = str(texto)
    linhas = texto.splitlines()

    # Fórmulas isoladas entre colchetes: [x^2 - 5x + 6 = 0]
    for i, linha in enumerate(linhas):
        limpa = linha.strip()
        if (
            len(limpa) >= 3
            and limpa.startswith("[")
            and limpa.endswith("]")
            and any(sinal in limpa for sinal in ("=", "^", "\\", "√", "∑", "∫"))
            and not limpa.startswith("[http")
        ):
            linhas[i] = "$$" + limpa[1:-1].strip() + "$$"

    texto = "\n".join(linhas)

    # Expressões entre parênteses que contêm comandos LaTeX viram matemática inline.
    padrao = r"\(([^()\n]*\\(?:Rightarrow|rightarrow|times|cdot|frac|sqrt|neq|leq|geq|approx|pm)[^()\n]*)\)"
    texto = re.sub(padrao, lambda m: "$" + m.group(1).strip() + "$", texto)

    st.markdown(texto)


# ============================================================
# 2. CONEXÃO COM A GROQ
# ============================================================

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)


# ============================================================
# 2.0. VOZ DO ORION COM CARTESIA
# ============================================================


def limpar_texto_para_voz(texto):
    """Remove marcações Markdown que não devem ser pronunciadas."""
    if not texto:
        return ""

    texto = str(texto)
    texto = re.sub(r"```[\s\S]*?```", " trecho de código omitido. ", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)
    texto = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", texto)
    texto = re.sub(r"[*_~`#]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def falar_texto(texto, persona="🔭 ORION"):
    """Gera voz com a Cartesia e exibe o áudio no Streamlit."""
    texto_limpo = limpar_texto_para_voz(texto)
    if not texto_limpo:
        return

    api_key = st.secrets.get("CARTESIA_API_KEY", "")
    voice_id = st.secrets.get("CARTESIA_VOICE_ID", "")

    if not api_key:
        st.warning("Configure CARTESIA_API_KEY nos Secrets do Streamlit para ativar a voz do ORION.")
        return

    if not voice_id:

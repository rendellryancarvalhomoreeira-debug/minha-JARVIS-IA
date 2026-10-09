pip install streamlit

import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="JARVIS GLASS",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #050a0e;
    color: #8df7df;
}
h1, h2, h3, p, div {
    color: #8df7df;
}
.hud {
    border: 1px solid #28a995;
    border-radius: 12px;
    padding: 18px;
    background: #071519;
    margin-bottom: 14px;
}
</style>
""", unsafe_allow_html=True)

agora = datetime.now()

st.title("J.A.R.V.I.S. // GLASS")
st.caption("INTERFACE EXPERIMENTAL DE VISOR")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f'<div class="hud"><h3>HORÁRIO</h3>'
        f'<h2>{agora.strftime("%H:%M:%S")}</h2>'
        f'{agora.strftime("%d/%m/%Y")}</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown("""
    <div class="hud">
    <h3>SISTEMA</h3>
    INTERFACE: ONLINE<br>
    MODO: DEMONSTRAÇÃO<br>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="hud">
<h3>JARVIS</h3>
Sistema iniciado. Aguardando integração com o assistente.
</div>
""", unsafe_allow_html=True)

st.caption("Protótipo de software — ainda não conectado a um visor físico.")

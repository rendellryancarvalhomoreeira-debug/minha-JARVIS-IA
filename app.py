import streamlit as st
from groq import Groq

st.set_page_config(page_title="JARVIS AI", page_icon="🤖")
st.title("🤖 JARVIS AI")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if prompt := st.chat_input("Pergunte sobre notícias, jogos ou qualquer assunto..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Você é o JARVIS, um assistente virtual prestativo."},
                    {"role": "user", "content": prompt}
                ]
            )
            st.markdown(completion.choices[0].message.content)
        except Exception as e:
            st.error(f"Erro ao gerar resposta: {e}")

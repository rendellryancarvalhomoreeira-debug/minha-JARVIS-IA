        }

    ]


    # ========================================================
    # 23. ADICIONAR HISTÓRICO
    # ========================================================

    mensagens_para_ia.extend(
        messages[1:]
    )


    # ========================================================
    # 24. CONFIGURAÇÃO DA GROQ
    # ========================================================

    parametros = {

        "model": MODEL_NAME,

        "messages": mensagens_para_ia,

        "temperature": 0.7,

        "tools": [

            {
                "type": "browser_search"
            }

        ],

        "tool_choice": "auto"

    }


    # ========================================================
    # 25. GERAR RESPOSTA
    # ========================================================

    with st.chat_message("assistant"):

        try:

            completion = (
                client
                .chat
                .completions
                .create(
                    **parametros
                )
            )


            # =================================================
            # PEGAR RESPOSTA
            # =================================================

            response = (
                completion
                .choices[0]
                .message
                .content
            )


            # =================================================
            # VERIFICAR RESPOSTA VAZIA
            # =================================================

            if not response:

                response = (
                    "Desculpe, não consegui gerar "
                    "uma resposta agora."
                )


            # =================================================
            # MOSTRAR RESPOSTA
            # =================================================

            st.markdown(response)


            # =================================================
            # BOTÕES DE VOZ
            # =================================================

            falar_texto(response, st.session_state.persona)


            # =================================================
            # SALVAR RESPOSTA NA CONVERSA
            # =================================================

            messages.append({

                "role": "assistant",

                "content": response

            })


        except Exception as e:

            st.error(
                f"Erro ao gerar resposta: {e}"
            )

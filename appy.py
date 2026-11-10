        + "\n\nMATEMÁTICA: use LaTeX com \\( ... \\) em linha e $$ ... $$ em bloco. "
          "Não deixe comandos LaTeX soltos nem envolva fórmulas apenas em colchetes comuns."
    )

    mensagens_para_ia = [
        {"role": "system", "content": prompt_sistema},
        {"role": "system", "content": memoria},
    ]


    # ========================================================
    # 23. ADICIONAR HISTÓRICO
    # ========================================================

    # O histórico visual pode conter metadados internos do ORION, como
    # action_url/action_label. A API da Groq aceita apenas campos válidos
    # de mensagem, então enviamos somente role/content para evitar HTTP 400.
    historico_para_ia = preparar_historico_para_ia(messages[1:])
    mensagens_para_ia.extend(historico_para_ia)


    # ========================================================
    # 24. CONFIGURAÇÃO E ROTEAMENTO MULTI-BRAIN
    # ========================================================

    provedores_disponiveis = provedores_multi_brain_disponiveis()
    multi_brain_ativo = bool(st.session_state.get("multi_brain_ativo", True))
    preferencia_cerebro = st.session_state.get("multi_brain_preferencia", "Automático")
    revisao_paralela = bool(st.session_state.get("multi_brain_revisao", False))
    if not multi_brain_ativo:
        provedores_disponiveis = ["Groq"] if "Groq" in provedores_disponiveis else provedores_disponiveis
        preferencia_cerebro = "Groq"
        revisao_paralela = False

    if not provedores_disponiveis:
        st.error("Nenhum provedor está disponível. Confira GROQ_API_KEY e as configurações dos provedores.")
        st.stop()

    # Pesquisa explícita/obrigatória permanece no pipeline Groq para preservar browser_search.
    if pesquisa_obrigatoria and preferencia_cerebro not in ("Automático", "Groq"):
        st.caption("🌐 Esta solicitação precisa da pesquisa integrada; o ORION usará a Groq nesta resposta.")

    # ========================================================
    # 25. GERAR RESPOSTA COM ROTEAMENTO, FALLBACK OU REVISÃO
    # ========================================================

    with st.chat_message("assistant"):
        try:
            inicio_chamada_ia = time.perf_counter()
            resultado_ia = gerar_resposta_multi_brain(
                prompt=prompt,
                mensagens=mensagens_para_ia,
                disponiveis=provedores_disponiveis,
                preferencia=preferencia_cerebro,
                modo=st.session_state.get("modo_resposta", "Automático"),
                pesquisa_ativada=pesquisa_ativada,
                pesquisa_obrigatoria=pesquisa_obrigatoria or pesquisa_explicitamente_solicitada,
                consulta_pessoal=consulta_pessoal,
                revisao_paralela=revisao_paralela,
            )
            response = resultado_ia["text"]
            duracao_ia = time.perf_counter() - inicio_chamada_ia

            if not response:
                response = "Desculpe, não consegui gerar uma resposta agora."

            # Métricas unificadas entre provedores. O valor de tokens depende do que cada API informa.
            partes_metricas = [
                f"🧠 Cérebro: {resultado_ia.get('route', resultado_ia.get('provider', 'IA'))}",
                f"Modelo: {resultado_ia.get('model', 'não informado')}",
                f"⏱️ {duracao_ia:.2f}s",
            ]
            tokens_total = (resultado_ia.get("usage") or {}).get("total")
            if tokens_total is not None:
                partes_metricas.append(f"tokens: {tokens_total}")
            st.caption(" • ".join(partes_metricas))

            if resultado_ia.get("fallback"):
                st.info("O cérebro preferido não respondeu; o ORION utilizou um provedor alternativo.")
            if resultado_ia.get("reviewed"):
                st.caption("🔎 Revisão híbrida concluída: duas propostas foram comparadas e sintetizadas.")

            if pesquisa_obrigatoria or pesquisa_explicitamente_solicitada:
                st.caption("🌐 Pesquisa solicitada/necessária: a busca integrada da Groq foi priorizada.")
            elif pesquisa_ativada:
                st.caption("🌐 Pesquisa avançada disponível no fluxo Groq quando necessária.")

            renderizar_resposta(response)

            # =================================================
            # VOZ OPCIONAL — CARTESIA PRESERVADA
            # =================================================
            if st.session_state.get("ler_respostas", True):
                falar_texto(response, st.session_state.persona)

            # Salva apenas conteúdo conversacional; metadados não são enviados aos modelos.
            messages.append({
                "role": "assistant",
                "content": response,
                "provider": resultado_ia.get("provider"),
                "model": resultado_ia.get("model"),
            })

        except Exception as e:
            st.error(f"Erro ao gerar resposta: {e}")

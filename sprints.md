# Regras de Entrega e Qualidade da Sprint

1. **Testes como Documentação Viva:** Toda nova funcionalidade deve ser acompanhada de testes com descrições em linguagem natural, claras e semânticas. O teste deve explicar o comportamento esperado da regra de negócio. Nenhuma alteração de código é aceita se quebrar a suíte de testes existente. O uso de dados simulados (mocks) é obrigatório para isolar o escopo do teste.

2. **Documentação Integrada ao Código:** É proibida a criação de arquivos de documentação avulsos para detalhar implementações. Todo o contexto técnico, explicação de regras complexas ou parâmetros deve ser feito através de comentários no próprio bloco de código (Docstrings/JSDoc), mantendo a leitura centralizada.

3. **Garantia de Desacoplamento do Monolito:** Apesar de o projeto estar em um repositório único (monorepo), os módulos devem permanecer independentes. Nenhuma alteração criada pela IA pode gerar acoplamento rígido ou dependências cruzadas ocultas entre domínios diferentes da aplicação.

4. **Barreira de Segurança:** O código entregue deve tratar e validar ativamente as entradas de dados para evitar vulnerabilidades. É estritamente proibida a inserção de chaves de API, senhas ou tokens diretamente no código-fonte.

5. **Refatoração e Histórico de Alterações:** Assim que os testes passarem no ciclo verde, o código deve passar por uma revisão de limpeza para garantir legibilidade, sem alterar o funcionamento. O encerramento da sprint exige um commit com um resumo claro e direto dos arquivos criados e modificados.

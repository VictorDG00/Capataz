# 🚀 PULL REQUEST: [TÍTULO DA SPRINT]

## 🛠️ INFORMAÇÕES DO AGENTE

- **IA Responsável:** (Gemini-Pro / Claude-3.5 / Stitch)
- **Branch de Origem:** `sprint-[nome]-[ia]`
- **Branch de Destino:** (develop / main)
- **Ticket/Issue Relacionada:** #

---

## 📝 RESUMO DA ATUAÇÃO

(Descreva aqui, de forma técnica e concisa, quais arquivos foram alterados e qual lógica foi implementada. Use o ACTLOG.md como base para este resumo.)

- **Funcionalidade X:** Implementada seguindo o padrão Clean Code.
- **Refatoração Y:** Melhoria de performance na camada de dados.
- **Segurança Z:** Sanitização aplicada conforme orientações do Auditor.

---

## 🛡️ CHECKLIST DE QUALIDADE (DOST)

- [ ] **D**esenvolvimento: O código segue o `CODING_STANDARDS.md`.
- [ ] **O**timização: Não há redundâncias ou imports desnecessários.
- [ ] **S**egurança: O `Bandit` e `Safety` retornaram 0 vulnerabilidades.
- [ ] **T**estes: Testes unitários e de regressão passaram com sucesso.

---

## 🧪 EVIDÊNCIAS DE TESTE

```bash
# Cole aqui o output resumido do Pytest ou do comando de validação
```

---

### Por que esse template é vital para você?

1.  **Auditoria Humana Rápida:** Mesmo que o merge seja automático para a `develop`, quando você (Victor) abrir o GitHub, verá um histórico limpo e profissional de tudo que as IAs fizeram.
2.  **Cultura DevOps:** Você está forçando a IA a declarar que rodou os testes (`Checklist DOST`). Se ela mentir, o log do GitHub Actions (que configuraremos nos workflows) vai pegá-la.
3.  **Rastreabilidade:** Você saberá exatamente qual IA (Gemini ou Stitch) foi responsável por cada alteração, facilitando o ajuste de prompts no futuro.

### Próximos Passos:

Agora a estrutura de arquivos, regras, agentes e templates está **100% pronta**. A "Forja" tem tudo para começar a fundir código.

Para encerrarmos essa fase de configuração e irmos para a ação, o que você prefere?

1.  **Configurar o primeiro Workflow do GitHub (`lint_and_test.yml`)** para automatizar o que definimos no Coding Standards?
2.  **Fazer um "Dry Run" (Teste Real)**: Dar uma tarefa simples para o `main.py` e ver se ele cria o primeiro arquivo e atualiza o `ACTLOG.md` corretamente?

**O que o Mestre de Obras decide?**

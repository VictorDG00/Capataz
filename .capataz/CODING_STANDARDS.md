# 📜 CODING STANDARDS & BRANCHING POLICY

## 1. ARQUITETURA DE BRANCHES

O Capataz opera sob um modelo de promoção de código rigoroso para garantir a estabilidade do ambiente.

### 🔴 Main (Produção)

- **Status:** Protegida. Jamais recebe commits diretos.
- **Requisito de Entrada:** 100% de aprovação em Testes Unitários, E2E, SAST (Bandit), e Smoke Tests.
- **Objetivo:** Garantir que o software esteja sempre em estado de "Deploy Imediato".

### 🟡 Develop (Integração)

- **Status:** Base para novas Sprints.
- **Requisito de Entrada:** Testes de regressão e verificações de integridade funcional.
- **Objetivo:** Integrar as novas funcionalidades e garantir que não haja quebra de recursos existentes.

### 🔵 Sprint Branches (Trabalho)

- **Nomenclatura Obrigatória:** `sprint-[NOME-DECLARATIVO]-[NOME-DA-IA]`
- **Exemplo:** `sprint-auth-refactor-gemini` ou `sprint-fix-ui-stitch`.
- **Origem:** Sempre criada a partir da `develop`.

## 2. FLUXO DE PROMOÇÃO (CI/CD)

1. **Início:** O Arquiteto define a tarefa e a branch é criada com o padrão de nomenclatura.
2. **Desenvolvimento:** O Developer (Gemini) ou Designer (Stitch) trabalha na branch de Sprint.
3. **Submissão:** Ao concluir, a IA abre um Pull Request (PR) para a `develop`.
4. **Validação:**
   - **Passou nos testes?** Merge automático via script de orquestração.
   - **Falhou?** O código entra em esteira de refatoração imediata. O erro é logado no `ACTLOG.md` e o Developer deve corrigir até a validação ser positiva.

## 3. PADRÕES DE CÓDIGO (STYLE GUIDE)

- **Linguagem:** Inglês para nomes de variáveis, funções e classes (Padrão de Mercado).
- **Comentários:** Apenas quando a lógica for complexa. O código deve ser autoexplicativo (Clean Code).
- **Commits:** Mensagens claras seguindo o padrão [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (ex: `feat: add login validation`).

## 4. DEFINITION OF DONE (DoD)

Uma tarefa só é considerada concluída pelo Capataz quando:

1. O código foi auditado pelo Security Auditor.
2. O `ACTLOG.md` foi atualizado com o status de Sucesso.
3. O PR para `develop` foi aprovado pelos testes automatizados.

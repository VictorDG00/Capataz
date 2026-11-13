> **Capataz** is a LangGraph-based multi-agent orchestrator (Python, FastAPI) that turns a task description into tested code under a DevSecOps, "shift left" workflow.
> Three LLM roles cooperate in a loop: the **Architect** plans the sprints and the API contract, the **Developer** writes the code, and the **Integrator** checks the output against the contract; a non-LLM **Validator** then runs pytest and Bandit (SAST) and can open a GitHub PR.
> LLM providers are configurable per role (DeepSeek by default; Claude, Gemini and OpenAI also supported). Stack: Python, LangGraph, LangChain, FastAPI, SQLite checkpoints. The documentation below is in Portuguese.

# Capataz: Forja de Software Autônoma & DevSecOps

"DevOps é um esforço colaborativo e multidisciplinar que ocorre em uma organização visando a automação da entrega contínua de novas versões de software, sem deixar de garantir a corretude e confiabilidade dessas versões." (LEITE et al, 2019)

O Capataz é um orquestrador de agentes de Inteligência Artificial projetado para operar como um membro sênior da equipe de engenharia. Ele não apenas escreve código; ele gerencia o ciclo de vida do software sob a ótica DevSecOps, priorizando a segurança desde a primeira linha de instrução (Shift Left).

## Objetivo

Criar um fluxo de trabalho autônomo onde IAs colaboram para transformar requisitos brutos em software seguro, testado e implantado. O Capataz garante que a agilidade da IA não comprometa a corretude e a confiabilidade do sistema, tratando segurança e infraestrutura como cidadãos de primeira classe.

## Arquitetura da "Forja" (Orquestração)

O Capataz utiliza uma abordagem de Multi-Agent Systems (MAS) baseada em FastAPI e LangGraph, dividindo responsabilidades entre diferentes modelos de linguagem para otimizar custo, contexto e raciocínio:

Os papéis que existem hoje no grafo (`src/agents/graph.py`):

O Arquiteto: Atua como o Tech Lead. Recebe a demanda, analisa o contexto e desenha o Plano de Execução (ciclo de sprints) e o contrato de API.

O Desenvolvedor: Executor. Aplica o plano do Arquiteto e escreve o código, uma sprint por vez.

O Integrador: Compara o output do Desenvolvedor com o contrato (responde apenas PASS ou FAIL). Em violação, devolve ao Desenvolvedor; em falha repetida, escala ao Arquiteto.

O Validador (sem LLM): Roda `pytest` e o Bandit (SAST). Se falhar, o erro volta ao Desenvolvedor. Se houver `GITHUB_TOKEN`, abre um PR ao fim da sprint.

Provedores de LLM (`src/core/factory.py`): configuráveis por papel via `AGENT_PROVIDER_*` no `.env`. Suportados: `deepseek` (padrão, modelo `deepseek-chat`), `claude` (`claude-3-5-sonnet-20240620`), `gemini` (`gemini-1.5-pro`) e `openai` (`gpt-4o`).

Planejado (ainda não implementado): Esteticista de UI/UX (`src/agents/designer.py` existe vazio), executor com janela de contexto longa (Gemini/Jules) e ajuste de front-end (Stitch).

## Mentalidade DevSecOps (Shift Left)

No Capataz, a segurança não é a última etapa, é a primeira:

Segurança do Ambiente: `.env` fora do Git (`.env.example` documenta as variáveis). O isolamento via Docker é planejado (ver Limitações conhecidas).

Segurança do Código: Análise estática automática integrada ao fluxo de escrita.

Hardening: Configuração de servidores e infraestrutura (IaC) focada em redução de superfície de ataque.

## O Fluxo de Trabalho (The Pipeline)

Planejamento: O Arquiteto gera o plano de ação (sprints) e o contrato.

Execução: O Desenvolvedor aplica as mudanças no código.

Integração: O Integrador valida o código contra o contrato.

Validação: O Validador roda testes e Bandit. Se falhar, o erro volta ao Desenvolvedor.

Entrega: Com `GITHUB_TOKEN`, o código vai para uma branch e um PR é aberto.

Planejado: Trigger por Issue/comentário no GitHub (webhooks) e deploy/preview na Vercel.

## Tecnologias Base

Linguagem: Python (Backend / Orquestração)

Framework de Agentes: LangGraph (Open Source)

API: FastAPI

Infraestrutura: Docker (planejado; `Dockerfile` e `docker-compose.yml` estão vazios hoje)

Stack Alvo: Next.js, TypeScript, Python, Tailwind CSS

## Citação

LEITE, M. et al. DevOps: Uma abordagem colaborativa para a entrega de software. 2019.

## Limitações conhecidas e notas de segurança

- O Inspetor (`src/core/security.py`) roda Bandit e demais comandos com allowlist (`pytest`, `npm`, `npx`, `ruff`, `bandit`, `next`, `jest`) e `shlex.split` (sem shell), mas **não em um container isolado**: executa como subprocesso no mesmo host/usuário do Capataz. Execute apenas em máquina ou VM descartável.
- A API (`src/api`) **não tem autenticação**. Rode-a somente em `127.0.0.1` ou em rede confiável, nunca exposta à internet. O repositório não define binding: o `docker-compose.yml` está vazio e o `uvicorn` é iniciado manualmente (padrão `127.0.0.1`; evite `--host 0.0.0.0`).

## Próximos Passos (To-Do)

[x] Ambiente FastAPI inicial (`src/api`).

[x] Grafo de decisão no LangGraph (Arquiteto -> Desenvolvedor -> Integrador -> Validador).

[ ] Dockerfile e docker-compose (arquivos existem, mas vazios).

[ ] Isolamento em container Docker para execução de testes e SAST.

[ ] Integração de Webhooks com GitHub.

[ ] Autenticação na API.

"Onde há fumaça, há forja. Onde há código, há o Capataz."

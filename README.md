# Capataz: Forja de Software Autônoma & DevSecOps

"DevOps é um esforço colaborativo e multidisciplinar que ocorre em uma organização visando a automação da entrega contínua de novas versões de software, sem deixar de garantir a corretude e confiabilidade dessas versões." (LEITE et al, 2019)

O Capataz é um orquestrador de agentes de Inteligência Artificial projetado para operar como um membro sênior da equipe de engenharia. Ele não apenas escreve código; ele gerencia o ciclo de vida do software sob a ótica DevSecOps, priorizando a segurança desde a primeira linha de instrução (Shift Left).

## Objetivo

Criar um fluxo de trabalho autônomo onde IAs colaboram para transformar requisitos brutos em software seguro, testado e implantado. O Capataz garante que a agilidade da IA não comprometa a corretude e a confiabilidade do sistema, tratando segurança e infraestrutura como cidadãos de primeira classe.

## Arquitetura da "Forja" (Orquestração)

O Capataz utiliza uma abordagem de Multi-Agent Systems (MAS) baseada em FastAPI e LangGraph, dividindo responsabilidades entre diferentes modelos de linguagem para otimizar custo, contexto e raciocínio:

O Arquiteto (Claude 3.5 Sonnet): Atua como o Tech Lead. Recebe a demanda (GitHub Issue), analisa o contexto e desenha o Plano de Execução. Define os contratos, a arquitetura de segurança e os critérios de aceitação.

O Operário (Gemini Pro/Jules): O executor de alta performance. Com sua janela de contexto de 2M de tokens, ele lê todo o repositório, aplica o plano do Arquiteto, escreve o código (Next.js/Python) e realiza o Server Hardening.

O Esteticista (Gemini Stitch): Focado na camada de UI/UX, garantindo que as interfaces sejam consistentes e sigam os padrões de design do projeto.

O Inspetor (Automated Scripts): Roda localmente no container (Docker) para validar linting, testes unitários e varreduras de segurança (SAST) antes de qualquer push.

## Mentalidade DevSecOps (Shift Left)

No Capataz, a segurança não é a última etapa, é a primeira:

Segurança do Ambiente: Orquestração via Docker isolado para evitar vazamento de segredos.

Segurança do Código: Análise estática automática integrada ao fluxo de escrita.

Hardening: Configuração de servidores e infraestrutura (IaC) focada em redução de superfície de ataque.

## O Fluxo de Trabalho (The Pipeline)

Trigger: Uma Issue é aberta ou um comentário é feito no GitHub.

Planejamento: O Claude gera um plano de ação e os testes necessários.

Execução: O Gemini aplica as mudanças no código dentro de um ambiente isolado.

Validação: O sistema roda o ciclo de testes. Se falhar, o erro volta para o Claude refinar o plano.

Interface: O Stitch ajusta o front-end necessário.

Deploy: O código é enviado para o GitHub, acionando o build e preview da Vercel.

## Tecnologias Base

Linguagem: Python (Backend / Orquestração)

Framework de Agentes: LangGraph (Open Source)

API: FastAPI

Infraestrutura: Docker (Isolamento de execução)

Stack Alvo: Next.js, TypeScript, Python, Tailwind CSS

## Citação

LEITE, M. et al. DevOps: Uma abordagem colaborativa para a entrega de software. 2019.

Próximos Passos (To-Do):
[ ] Configurar ambiente FastAPI inicial.

[ ] Implementar integração de Webhooks com GitHub.

[ ] Definir o primeiro grafo de decisão no LangGraph (Arquiteto -> Executor).

[ ] Configurar isolamento em Docker para execução de testes locais.

"Onde há fumaça, há forja. Onde há código, há o Capataz."

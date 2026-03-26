capataz-engine/
├── .github/ # 🏛️ Governança e Automação do Repositório
│ ├── workflows/ # Pipelines CI/CD
│ │ ├── lint_and_test.yml # GitHub Actions para testes de segurança (SAST)
│ │ └── capataz_trigger.yml # Action que acorda o Capataz quando uma Issue é aberta
│ ├── ISSUE_TEMPLATE/ # O formulário de entrada para o Claude ler
│ │ ├── bug_report.yml # Template de erro detalhado
│ │ └── feature_request.yml # Template para novas funcionalidades
│ ├── PULL_REQUEST_TEMPLATE.md # O molde que o Gemini vai usar para abrir PRs
│ ├── dependabot.yml # Bot nativo para manter dependências seguras
│ └── CODEOWNERS # Define quem (ou qual IA) aprova mudanças em quais pastas
│
├── .capataz/ # 🧠 Regras de Comportamento das IAs (Contextual Steering)
│ ├── GLOBAL.md # Diretrizes universais (Persona, Idioma, Stack)
│ ├── SECURITY.md # Regras rígidas de DevSecOps e Hardening
│ ├── TESTING.md # Exigência de cobertura (Pytest/Jest)
│ └── CODING_STANDARDS.md # Regras de Next.js, TypeScript e Python
│
├── src/ # ⚙️ Código Fonte do Orquestrador
│ ├── agents/ # Nós do LangGraph
│ │ ├── architect.py # Tech Lead (Claude 3.5 Sonnet)
│ │ ├── executor.py # Operário (Gemini Pro)
│ │ ├── designer.py # Esteticista UI/UX (Stitch)
│ │ └── graph.py # O motor cíclico de orquestração
│ ├── api/ # Onde o Capataz "escuta" o mundo exterior
│ │ ├── routes.py # Endpoints FastAPI para receber Webhooks
│ │ └── schemas.py # Validação rigorosa de dados (Pydantic)
│ └── core/ # Lógica Base de Infra
│ ├── security.py # Sandbox e isolamento
│ └── config.py # Gestão de credenciais
│
├── tests/ # 🧪 Testes da própria infraestrutura do Capataz
├── .gitignore
├── docker-compose.yml # Orquestração do container do Capataz
├── Dockerfile # Imagem leve e segura para rodar a aplicação
├── requirements.txt
└── README.md # O manifesto da "Forja"

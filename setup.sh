#!/bin/bash
set -e

echo "🏗️  [CAPATAZ] Iniciando a fundação e decolagem..."

# 1. Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Ambiente virtual criado."
fi

# 2. Ativar ambiente
source venv/bin/activate

# 3. Atualizar pip e instalar dependências silenciosamente
echo "📦 Verificando dependências..."
pip install --upgrade pip > /dev/null
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null
    echo "✅ Dependências sincronizadas."
else
    echo "❌ Erro: requirements.txt não encontrado."
    exit 1
fi

# 4. Garantir arquivo .env sem sobrescrever segredos existentes
if [ -f ".env" ]; then
    echo "✅ .env já existe. Nenhuma alteração foi feita nas variáveis atuais."
else
    if [ -f ".env.exemple" ]; then
        cp .env.exemple .env
        echo "⚠️  .env criado a partir de .env.exemple. Revise e preencha suas chaves de API antes de rodar."
    else
        cat > .env <<'EOF'
# --- API KEYS ---
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com

# --- DATABASE CONFIG ---
DATABASE_URL=sqlite:///./src/core/checkpoints.db

# --- ROLES PROVIDERS ---
AGENT_PROVIDER_ARCHITECT=deepseek
AGENT_PROVIDER_DEVELOPER=deepseek
AGENT_PROVIDER_DESIGNER=deepseek
AGENT_PROVIDER_SECURITY_AUDITOR=deepseek
EOF
        echo "⚠️  .env criado com valores padrão. Preencha suas chaves de API antes de rodar."
    fi
fi

# 5. Executar a Interface de Configuração
echo "🚀 Abrindo Painel de Controle..."
python config_ui.py

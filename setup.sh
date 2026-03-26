#!/bin/bash
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

# 4. Garantir arquivo .env
if [ ! -f ".env" ]; then
    echo "DEEPSEEK_API_KEY=seu_token_aqui" > .env
    echo "DEEPSEEK_BASE_URL=https://api.deepseek.com" >> .env
    echo "DATABASE_URL=sqlite:///./src/core/checkpoints.db" >> .env
    echo "⚠️  Arquivo .env criado. PREENCHA AS CHAVES antes de rodar novamente."
    exit 1
fi

# 5. Executar a Interface de Configuração
echo "🚀 Abrindo Painel de Controle..."
python config_ui.py
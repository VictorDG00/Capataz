#!/bin/bash
echo "🏗️ Iniciando a fundação do Capataz..."

# 1. Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Ambiente virtual criado."
fi

# 2. Ativar e atualizar pip
source venv/bin/activate
pip install --upgrade pip

# 3. Instalar dependências
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependências instaladas."
else
    echo "❌ Erro: requirements.txt não encontrado."
fi

# 4. Criar arquivo .env base (Segurança!)
if [ ! -f ".env" ]; then
    echo "ANTHROPIC_API_KEY=seu_token_aqui" > .env
    echo "GOOGLE_API_KEY=seu_token_aqui" >> .env
    echo "DATABASE_URL=sqlite:///./src/core/checkpoints.db" >> .env
    echo "✅ Arquivo .env criado (Não esqueça de preencher as chaves)."
fi

echo "🚀 Fundação concluída. Ative o ambiente com: source venv/bin/activate"

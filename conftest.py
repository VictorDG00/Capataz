import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# Variáveis de ambiente para testes — evita erros de API key ausente nos singletons
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("AGENT_PROVIDER_ARCHITECT", "deepseek")
os.environ.setdefault("AGENT_PROVIDER_DEVELOPER", "deepseek")
os.environ.setdefault("AGENT_PROVIDER_INTEGRATOR", "deepseek")
os.environ.setdefault("AGENT_PROVIDER_DESIGNER", "deepseek")
os.environ.setdefault("AGENT_PROVIDER_SECURITY_AUDITOR", "deepseek")

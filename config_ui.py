# config_ui.py
import os
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from dotenv import set_key, load_dotenv

# Caminho para o seu arquivo de segredos
ENV_PATH = ".env"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def update_env_provider(role: str, provider: str):
    """Atualiza o provedor de uma IA específica no arquivo .env"""
    # Formato: AGENT_PROVIDER_ARCHITECT=deepseek
    key_name = f"AGENT_PROVIDER_{role.upper()}"
    set_key(ENV_PATH, key_name, provider)
    # Recarrega para garantir que o sistema interno veja a mudança
    load_dotenv(ENV_PATH, override=True)

def main_menu():
    clear_screen()
    print("🏗️  FORJA DE CÓDIGOS - PAINEL DE CONTROLE")
    print("------------------------------------------")
    
    action = inquirer.select(
        message="Selecione uma ação:",
        choices=[
            Choice("config_ai", "🤖 Configurar Provedores de IA"),
            Choice("start_forge", "🚀 Iniciar a Forja (Executar main.py)"),
            Choice("exit", "❌ Sair"),
        ],
        default="config_ai",
    ).execute()

    if action == "config_ai":
        configure_agents()
    elif action == "start_forge":
        print("\n🔥 Aquecendo a forja... O Capataz vai assumir o turno.")
        os.system("python main.py")
    elif action == "exit":
        print("Até a próxima, Victor.")
        return

def configure_agents():
    clear_screen()
    print("🛠️  MAPEAMENTO DE CARGOS")
    
    role = inquirer.select(
        message="Qual papel você deseja configurar?",
        choices=[
            Choice("architect", "Arquiteto (Tech Lead)"),
            Choice("developer", "Desenvolvedor (Coding)"),
            Choice("designer", "Designer (UI/UX)"),
            Choice("security_auditor", "Auditor (SecOps)"),
            Choice("back", "⬅️ Voltar"),
        ],
    ).execute()

    if role == "back":
        main_menu()
        return

    provider = inquirer.select(
        message=f"Selecione a IA para o papel de {role}:",
        choices=[
            Choice("deepseek", "DeepSeek (Recomendado para Testes)"),
            Choice("gemini", "Google Gemini"),
            Choice("claude", "Anthropic Claude"),
            Choice("openai", "OpenAI GPT-4o"),
        ],
    ).execute()

    update_env_provider(role, provider)
    print(f"\n✅ Configuração salva no .env: {role.upper()} -> {provider.upper()}")
    input("\nPressione Enter para continuar...")
    configure_agents()

if __name__ == "__main__":
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, "w") as f:
            f.write("# Configurações do Capataz\n")
            
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
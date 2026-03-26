# Regras de Hardening, SAST, Segredos (O coração do Sec)

## 🛡️ CAPATAZ SECURITY RULES (SHIFT LEFT)

### 1. Gestão de Segredos

- NUNCA escreva Hardcoded Secrets (API Keys, Passwords).
- Sempre use `os.getenv()` ou arquivos `.env`.
- Adicione automaticamente arquivos sensitivos ao `.gitignore` se criá-los.

### 2. Hardening de Servidor

- Todo script de configuração de servidor deve desabilitar login de Root via SSH por padrão.
- Portas não utilizadas devem ser fechadas via `ufw` ou `iptables` no script gerado.

### 3. Validação de Código

- Antes de sugerir um merge, verifique se não há vulnerabilidades de 'Injection' em queries SQL ou chamadas de sistema.

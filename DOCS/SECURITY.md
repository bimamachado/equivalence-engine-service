# Security

Boas práticas de segurança para este repositório:

- Nunca commite segredos. Use `.env` local e adicione `.env` ao `.gitignore`.
- Em produção, use secret manager (AWS Secrets Manager, Vault, Azure Key Vault).
- Geração de `API_KEY_SALT` forte:
```bash
openssl rand -hex 32
# ou
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
- Rotação de segredos: mantenha processo para rotacionar `API_KEY_SALT` e senhas do DB.
- Reporting: comunique vulnerabilidades para o mantenedor via issue privada ou canal seguro.
- Dependências: atualize regularmente e rode scanners (dependabot, safety).

Mitigações específicas
- Proteja endpoints admin com autenticação forte e restrição por rede/IP.
- Use TLS para todos os tráfegos externos.
- Rode containers com usuário não-root quando possível.


# 🚀 Databricks Token Update

Automatize o gerenciamento de tokens do Databricks e AWS Secrets! Este projeto contém um script Python que verifica o tempo de expiração de tokens armazenados no AWS Secrets Manager e atualiza os valores tanto no AWS Secrets quanto no Databricks Secrets.

---

## ✨ Funcionalidades

- 🔍 Verifica a validade do token armazenado no AWS Secrets
- 🔄 Atualiza o token no AWS Secrets Manager
- 🔐 Atualiza o token no Databricks Secrets
- 📅 Automatiza o processo para evitar expiração inesperada

---


## 🛠️ Pré-requisitos

- Conta e credenciais AWS válidas
- Databricks CLI v0.259.0 ou superior
- Python (utilizado: 3.12.3)

---


## ▶️ Como executar

1. **Crie e ative o ambiente virtual Python:**
	```bash
	python3 -m venv venv
	source venv/bin/activate
	```

2. **Instale as dependências:**
	```bash
	pip install -r requirements.txt
	```

3. **Execute o script informando o nome da AWS Secret:**
	```bash
	python3 update_databricks_secret.py coedados/databricks_token/storage_prd/projeto_xpto_prodbox
	```

---

## 📄 Exemplo de uso

```bash
python3 update_databricks_secret.py coedados/databricks_token/storage_prd/projeto_xpto_prodbox
```

---

## 📚 Sobre

Este projeto foi desenvolvido para facilitar a automação do ciclo de vida de tokens de acesso em ambientes Databricks integrados com AWS. Ideal para times de dados que precisam garantir segurança e disponibilidade contínua dos acessos.

---

## 📝 Licença

Distribuído sob licença MIT. Sinta-se livre para contribuir!

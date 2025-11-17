import subprocess
import json
import sys
import datetime
import boto3

def run_command(command):
    """
    Executa um comando no shell e retorna a saída.
    Lança uma exceção em caso de erro.
    """
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(f"Erro ao executar comando:\n{command}\n{result.stderr}")
    return result.stdout

def update_databricks_secret(scope, secret_name, token_value, workspace):
    """
    Atualiza uma secret no Databricks via CLI usando:
    databricks secrets put-secret <scope> <secret> --string-value '<token>' -p <workspace>
    """
    print(f"🔐 Atualizando secret '{secret_name}' no scope '{scope}' do Databricks workspace {workspace} ...")
    command = f"databricks secrets put-secret {scope} {secret_name} --string-value '{token_value}' -p {workspace}"
    run_command(command)
    print("✅ Secret atualizada no Databricks com sucesso.")

def update_aws_secret(secret_id, secret_dict):
    """
    Atualiza a secret no AWS Secrets Manager com o novo dicionário completo.
    """
    print("📦 Atualizando secret no AWS Secrets Manager...")
    client = boto3.client("secretsmanager")
    client.update_secret(
        SecretId=secret_id,
        SecretString=json.dumps(secret_dict)
    )
    print(f"✅ Secret '{secret_id}' atualizada com sucesso na AWS.")

def process_secret(secret_id):
    """
    Processo principal que:
    1. Busca a secret existente.
    2. Gera novo token via Databricks.
    3. Atualiza os dados locais e no AWS Secrets Manager.
    4. Atualiza secret no Databricks se aplicável.
    """

    client = boto3.client("secretsmanager")

    # 1. Busca secret existente
    print(f"🔎 Buscando secret no AWS Secrets Manager: {secret_id}")
    secret_value = client.get_secret_value(SecretId=secret_id)
    secret_dict = json.loads(secret_value["SecretString"])

    # Salva valores antigos (se existirem)
    old_token = secret_dict.get("token")
    old_expiration = secret_dict.get("expiration_time")

    # --- VALIDAÇÃO DA EXPIRAÇÃO DE TOKEN ---
    if old_token and old_expiration:
        try:
            # Converte a string YYYY-MM-DD para um objeto date
            expiration_date_obj = datetime.datetime.strptime(old_expiration, "%Y-%m-%d").date()
            # Pega a data de hoje (em UTC, para consistência)
            today = datetime.datetime.now(datetime.UTC).date()
            
            days_remaining = (expiration_date_obj - today).days

            if days_remaining > 15:
                print(f"✅ O token ainda é válido por {days_remaining} dias (expira em {old_expiration}). A atualização não é necessária.")
                return # Encerra a função
            elif days_remaining <= 0:
                 print(f"🚨 O token expirou há {-days_remaining} dias (em {old_expiration}). Iniciando renovação urgente...")
            else:
                print(f"⚠️ O token expira em {days_remaining} dias (em {old_expiration}). Iniciando renovação...")
        
        except ValueError:
            # Caso a data esteja em formato inválido, força a renovação
            print(f"⚠️ Não foi possível analisar a data de expiração antiga ('{old_expiration}'). Prosseguindo com a renovação.")
        
    else:
        print("ℹ️ Token ou data de expiração antigos não encontrados. Prosseguindo com a geração de um novo token.")
    # --- FIM DA VALIDAÇÃO DA EXPIRAÇÃO DE TOKEN ---


    # 2. Extrai campos obrigatórios
    application_id = secret_dict["application_id"]
    workspace = secret_dict["workspace"]

    # Campos opcionais
    scope = secret_dict.get("scope")
    secret_name = secret_dict.get("secret")
    workspace_scope = secret_dict.get("workspace_scope")
    email_address = secret_dict.get("email") # Pega o email para Alteração 2

    # 3. Gera novo token via Databricks CLI
    print("🔧 Gerando novo token com Databricks CLI...")
    command = f"databricks token-management create-obo-token {application_id} --lifetime-seconds 7889400 -p {workspace}"
    output = run_command(command)
    token_data = json.loads(output)

    token_value = token_data["token_value"]
    expiry_time_ms = token_data["token_info"]["expiry_time"]

    # 4. Datas formatadas
    expiration_date = datetime.datetime.fromtimestamp(expiry_time_ms / 1000, tz=datetime.UTC).strftime("%Y-%m-%d")
    update_time = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

    # 5. Atualiza valores na secret local
    secret_dict["token"] = token_value
    secret_dict["expiration_time"] = expiration_date
    secret_dict["update_time"] = update_time

    # 6. Atualiza secret na AWS
    update_aws_secret(secret_id, secret_dict)

    # 7. Atualiza secret no Databricks, se aplicável
    if scope and secret_name:
        update_databricks_secret(scope, secret_name, token_value, workspace_scope or workspace)
    else:
        print("ℹ️ Campos 'scope' e/ou 'secret' não encontrados. Databricks não será atualizado.")

    # 8. Resumo
    print(f"\nResumo da atualização:")
    if old_token:
        print(f"🔑 Token antigo: {old_token}")
    if old_expiration:
        print(f"📅 Expiração antiga: {old_expiration}")

    print(f"\n🔑 Novo token: {token_value}")
    print(f"📅 Expira em: {expiration_date}")
    print(f"🕒 Atualizado em: {update_time}")
    print(f"✉️ Email: {email_address or 'N.A'}")
    
    # 9. Texto adicional (Só exibe se o email foi fornecido)
    if email_address:
        sql_warehouse_name = secret_id.split("/")[-1]  # pega só o último trecho após "/"

        print(f"""
[ IMPORTANTE ] Atualização de Token SQL Warehouse Databricks - \033[1m{sql_warehouse_name}\033[0m
Prezado(a),
          
Este email contém o seu novo token de acesso para o SQL Warehouse \033[1m{sql_warehouse_name}\033[0m no Databricks.

Seu token antigo, com vencimento em \033[1m{old_expiration}\033[0m, precisa ser atualizado pelo novo token.

Token Antigo: {old_token}

Token Novo: {token_value}
Validade: \033[1m{expiration_date}\033[0m

Por favor, atualize suas configurações para usar o novo token antes da data de expiração do antigo para evitar interrupções.

Em caso de dúvidas, estamos à disposição.

Atenciosamente,
""")

def main():
    """
    Função principal que apenas chama o processamento da secret.
    """
    if len(sys.argv) != 2:
        print("Uso: python update_databricks_secret.py <nome_da_secret>")
        sys.exit(1)

    secret_id = sys.argv[1]
    process_secret(secret_id)

if __name__ == "__main__":
    main()

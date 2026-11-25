region = "us-east-1"
db_password = "${data.azurerm_key_vault_secret.code_scan_api_key.value}"

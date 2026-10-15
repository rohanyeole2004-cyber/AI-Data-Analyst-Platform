def get_secret(name,vault_url=None):
 from azure.identity import DefaultAzureCredential
 from azure.keyvault.secrets import SecretClient
 if not vault_url: raise ValueError("AZURE_KEY_VAULT_URL is not configured")
 return SecretClient(vault_url=vault_url,credential=DefaultAzureCredential()).get_secret(name).value

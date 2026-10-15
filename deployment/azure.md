# Azure deployment plan

## Resources
Create a Resource Group, Storage Account/Blob Container, Azure SQL Server + Database, Key Vault, App Service, and Application Insights.

## Secrets
Put database/API secrets in Key Vault. Prefer App Service Managed Identity so the application authenticates to Key Vault without storing credentials in source code.

## Cost control
Develop locally first. Provision Azure resources only for the phase being tested. Delete unused resource groups after experiments and monitor spending in the Azure portal.

## Deployment
Build the Docker image or deploy the Python app to App Service. Configure application settings from Key Vault/managed identity rather than committing `.env`.

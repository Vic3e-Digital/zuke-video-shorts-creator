# Azure Deployment Guide

## Complete Azure Infrastructure Setup for Zuke Video Shorts Creator

This guide walks you through deploying the Zuke Video Shorts Creator to Azure with all necessary services.

## Prerequisites

- Azure subscription with sufficient credits
- Azure CLI installed (`az --version` to verify)
- Docker installed locally
- GitHub repository set up
- OpenAI API key

## Step 1: Azure CLI Login

```bash
# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "Your-Subscription-Name"

# Verify current subscription
az account show
```

## Step 2: Create Resource Group

```bash
# Set variables
RESOURCE_GROUP="zuke-video-shorts-rg"
LOCATION="eastus"  # Choose your preferred region
PROJECT_NAME="zuke-video-shorts"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

## Step 3: Deploy Azure Resources Using ARM Template

```bash
# Deploy using the ARM template
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file ./azure/azure-resources.json \
  --parameters projectName=$PROJECT_NAME \
  --parameters openAIApiKey="your-openai-api-key" \
  --parameters containerImage="nginx:latest"
```

This will create:
- Azure Storage Account with Blob Container
- Azure Container Registry (ACR)
- Azure Container Apps Environment
- Azure Container App
- Log Analytics Workspace
- Application Insights
- Azure Key Vault

## Step 4: Configure Azure Container Registry

```bash
# Get ACR name from deployment
ACR_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-resources \
  --query properties.outputs.containerRegistryName.value -o tsv)

# Login to ACR
az acr login --name $ACR_NAME

# Enable admin user (for CI/CD)
az acr update -n $ACR_NAME --admin-enabled true

# Get ACR credentials
ACR_USERNAME=$(az acr credential show -n $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show -n $ACR_NAME --query passwords[0].value -o tsv)
ACR_LOGIN_SERVER=$(az acr show -n $ACR_NAME --query loginServer -o tsv)

echo "ACR Login Server: $ACR_LOGIN_SERVER"
echo "ACR Username: $ACR_USERNAME"
```

## Step 5: Build and Push Docker Image

```bash
# Build the Docker image
docker build -t $ACR_LOGIN_SERVER/zuke-video-shorts-creator:latest .

# Push to ACR
docker push $ACR_LOGIN_SERVER/zuke-video-shorts-creator:latest
```

## Step 6: Update Container App with Your Image

```bash
# Get Container App name
CONTAINER_APP_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-resources \
  --query properties.outputs.containerAppName.value -o tsv)

# Update container app
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_LOGIN_SERVER/zuke-video-shorts-creator:latest
```

## Step 7: Configure GitHub Actions Secrets

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

```bash
# Get values for GitHub secrets
echo "AZURE_CONTAINER_REGISTRY: $ACR_LOGIN_SERVER"
echo "AZURE_REGISTRY_USERNAME: $ACR_USERNAME"
echo "AZURE_REGISTRY_PASSWORD: $ACR_PASSWORD"
echo "AZURE_RESOURCE_GROUP: $RESOURCE_GROUP"

# Create service principal for GitHub Actions
AZURE_CREDENTIALS=$(az ad sp create-for-rbac \
  --name "github-actions-zuke" \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth)

echo "AZURE_CREDENTIALS: $AZURE_CREDENTIALS"

# Get storage account credentials
STORAGE_ACCOUNT_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-resources \
  --query properties.outputs.storageAccountName.value -o tsv)

STORAGE_ACCOUNT_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT_NAME \
  --query [0].value -o tsv)

echo "AZURE_STORAGE_ACCOUNT_NAME: $STORAGE_ACCOUNT_NAME"
echo "AZURE_STORAGE_ACCOUNT_KEY: $STORAGE_ACCOUNT_KEY"
```

**GitHub Secrets to Add:**
- `AZURE_CONTAINER_REGISTRY`
- `AZURE_REGISTRY_USERNAME`
- `AZURE_REGISTRY_PASSWORD`
- `AZURE_RESOURCE_GROUP`
- `AZURE_CREDENTIALS`
- `AZURE_STORAGE_ACCOUNT_NAME`
- `AZURE_STORAGE_ACCOUNT_KEY`
- `OPENAI_API_KEY`

## Step 8: Get Your Application URL

```bash
# Get the Container App FQDN
APP_FQDN=$(az containerapp show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Your application is available at: https://$APP_FQDN"
```

## Step 9: Test Your Deployment

```bash
# Test health endpoint
curl https://$APP_FQDN/health

# Test API with authentication
API_KEY="your-api-key-here"
curl -X GET https://$APP_FQDN/ \
  -H "X-API-Key: $API_KEY"
```

## Step 10: Configure Azure Blob Storage

```bash
# Get storage account connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT_NAME \
  --query connectionString -o tsv)

# Create additional containers if needed
az storage container create \
  --name temp \
  --connection-string $STORAGE_CONNECTION_STRING \
  --public-access blob

az storage container create \
  --name output \
  --connection-string $STORAGE_CONNECTION_STRING \
  --public-access blob
```

## Monitoring and Logging

### View Logs

```bash
# Stream logs from Container App
az containerapp logs show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow
```

### Application Insights

```bash
# Get Application Insights connection string
APP_INSIGHTS_CONNECTION=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name azure-resources \
  --query properties.outputs.applicationInsightsConnectionString.value -o tsv)

echo "Application Insights Connection String: $APP_INSIGHTS_CONNECTION"
```

Access Application Insights in Azure Portal:
1. Go to your resource group
2. Click on Application Insights resource
3. View metrics, logs, and traces

## Scaling Configuration

```bash
# Update scaling rules
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 1 \
  --max-replicas 10
```

## Cost Optimization

### Enable Auto-Scaling to Zero
```bash
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 0 \
  --max-replicas 5
```

### Set Storage Lifecycle Management
```bash
# Create a lifecycle management policy (delete old files after 30 days)
az storage account management-policy create \
  --account-name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --policy @lifecycle-policy.json
```

## Backup and Disaster Recovery

### Backup Configuration
```bash
# Enable blob soft delete (allows recovery of deleted blobs)
az storage blob service-properties delete-policy update \
  --account-name $STORAGE_ACCOUNT_NAME \
  --enable true \
  --days-retained 30
```

## Security Best Practices

1. **Key Vault Integration**
```bash
# Store secrets in Key Vault
KEYVAULT_NAME=$(az keyvault list \
  --resource-group $RESOURCE_GROUP \
  --query [0].name -o tsv)

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name openai-api-key \
  --value "your-openai-api-key"
```

2. **Enable Managed Identity**
```bash
# Enable managed identity for Container App
az containerapp identity assign \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --system-assigned

# Grant access to Key Vault
CONTAINER_APP_IDENTITY=$(az containerapp identity show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

az keyvault set-policy \
  --name $KEYVAULT_NAME \
  --object-id $CONTAINER_APP_IDENTITY \
  --secret-permissions get list
```

3. **Configure CORS**
```bash
# Allow specific origins
az containerapp ingress cors enable \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "https://yourfrontend.com"
```

## Troubleshooting

### View Container App Revisions
```bash
az containerapp revision list \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table
```

### Restart Container App
```bash
az containerapp revision restart \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### Check Resource Status
```bash
# List all resources in the resource group
az resource list \
  --resource-group $RESOURCE_GROUP \
  --output table
```

## Cleanup (When Needed)

```bash
# Delete entire resource group (WARNING: This deletes everything!)
az group delete \
  --name $RESOURCE_GROUP \
  --yes \
  --no-wait
```

## Next Steps

1. ✅ Set up CI/CD pipeline with GitHub Actions
2. ✅ Configure custom domain and SSL certificate
3. ✅ Implement rate limiting and API authentication
4. ✅ Set up monitoring alerts in Application Insights
5. ✅ Configure backup and disaster recovery
6. ✅ Implement cost monitoring and budgets

## Support Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [Azure Storage Documentation](https://docs.microsoft.com/azure/storage/)
- [Application Insights Documentation](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)

---

**Note**: Replace all placeholder values (like `your-openai-api-key`) with your actual values before running commands.
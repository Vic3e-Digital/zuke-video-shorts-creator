#!/bin/bash

# Check Azure Container Processing Status

CONTAINER_NAME="zuke-video-4563"
RESOURCE_GROUP=""  # Add your resource group name here

echo "🔍 Checking Azure Container Status"
echo "===================================="
echo ""

# If no resource group specified, try to find it
if [ -z "$RESOURCE_GROUP" ]; then
    echo "🔎 Looking for resource group..."
    RESOURCE_GROUP=$(az containerapp show --name "$CONTAINER_NAME" --query resourceGroup -o tsv 2>/dev/null | head -1)
    
    if [ -z "$RESOURCE_GROUP" ]; then
        echo "❌ Could not find resource group. Please specify it in the script."
        echo ""
        echo "Find your resource group with:"
        echo "  az containerapp list --query '[].{name:name, rg:resourceGroup}' -o table"
        exit 1
    fi
    
    echo "✓ Found resource group: $RESOURCE_GROUP"
fi

echo ""
echo "📊 Container Status:"
az containerapp show \
  --name "$CONTAINER_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query '{name:name, status:properties.runningStatus, replicas:properties.template.scale.minReplicas}' \
  -o table

echo ""
echo "📝 Recent Logs (last 20 lines):"
echo "---"
az containerapp logs show \
  --name "$CONTAINER_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --tail 20 \
  --format text 2>/dev/null | tail -20

echo ""
echo "---"
echo ""
echo "💡 Tips:"
echo "  Follow logs live: az containerapp logs show --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP --follow"
echo "  Get more logs: az containerapp logs show --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP --tail 100"

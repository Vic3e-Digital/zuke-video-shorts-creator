# HTTPS Setup for Azure Container Instance

Your current deployment runs on HTTP: `http://zuke-video-4563.eastus.azurecontainer.io:8000`

Azure Container Instances doesn't natively support HTTPS. Here are your options:

## Option 1: Cloudflare (Easiest & Free)

1. Sign up at [cloudflare.com](https://cloudflare.com)
2. Add your domain (or get a free subdomain)
3. Point to your container IP: `zuke-video-4563.eastus.azurecontainer.io`
4. Enable "Full" SSL mode
5. Cloudflare automatically provides HTTPS

**Result**: `https://yourdomain.com` → HTTP backend

## Option 2: Azure Application Gateway

```bash
# Create Application Gateway with SSL
az network application-gateway create \
  --name zuke-video-gateway \
  --resource-group zuke-video-shorts-rg \
  --location eastus \
  --sku Standard_v2 \
  --capacity 2 \
  --vnet-name zuke-vnet \
  --subnet gateway-subnet \
  --http-settings-cookie-based-affinity Disabled \
  --frontend-port 443 \
  --http-settings-port 8000 \
  --http-settings-protocol Http \
  --public-ip-address zuke-gateway-ip \
  --cert-file ./certificate.pfx \
  --cert-password "your-password"
```

**Cost**: ~$150-300/month

## Option 3: Azure Front Door

```bash
# Create Front Door
az afd profile create \
  --profile-name zuke-video-fd \
  --resource-group zuke-video-shorts-rg \
  --sku Standard_AzureFrontDoor

# Add endpoint
az afd endpoint create \
  --endpoint-name zuke-video-api \
  --profile-name zuke-video-fd \
  --resource-group zuke-video-shorts-rg

# Origin configuration (point to your container)
az afd origin-group create \
  --origin-group-name container-origin \
  --profile-name zuke-video-fd \
  --resource-group zuke-video-shorts-rg
```

**Cost**: ~$35/month + traffic

## Option 4: nginx-proxy with Let's Encrypt (Free)

Add a second container with nginx:

```yaml
# docker-compose for dual container
services:
  app:
    image: your-acr.azurecr.io/zuke-video-shorts:latest
    
  nginx:
    image: nginxproxy/nginx-proxy
    ports:
      - "443:443"
    volumes:
      - ./certs:/etc/nginx/certs
    environment:
      - DEFAULT_HOST=yourdomain.com
```

## Recommendation

For **quick testing**: Use Cloudflare (free, 5 minutes setup)
For **production**: Use Azure Front Door (built-in DDoS, caching, WAF)

## Current Status

- HTTP URL: `http://zuke-video-4563.eastus.azurecontainer.io:8000`
- No HTTPS configured
- Container is publicly accessible on port 8000

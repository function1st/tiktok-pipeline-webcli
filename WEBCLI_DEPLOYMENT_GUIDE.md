# 🚀 Web CLI Deployment Guide

## Architecture Overview

```
Azure Static Web App ──HTTPS──► Azure Container App
    (Frontend)                    ├── FastAPI (Port 8000)
                                  └── ttyd Terminal (Port 7681)
```

## ✅ What's Changed

### **Before (Broken)**
- Frontend → Azure Functions → Container App
- Complex WebSocket proxy
- Azure CLI subprocess execution

### **After (Working)**
- Frontend → Container App (Direct)
- ttyd handles terminal server
- Real SSH-like experience

## 🔧 Deployment Steps

### **1. Deploy Container App**
```bash
# Build and deploy container with ttyd
cd tiktok-pipeline
az container create --file container-config.yaml

# Verify both ports are accessible
curl http://YOUR_CONTAINER_IP:8000/health  # FastAPI
curl http://YOUR_CONTAINER_IP:7681         # ttyd terminal
```

### **2. Deploy Static Web App**
```bash
cd tiktok-pipeline-webcli
git push origin main  # Triggers GitHub Actions deployment
```

### **3. Update Container IP**
```javascript
// In index.html, update this line:
const CONTAINER_APP_URL = 'https://YOUR_ACTUAL_CONTAINER_IP:7681';
```

## 🔒 Security Features

- **ttyd Authentication**: Uses WEBCLI_ACCESS_CODE
- **HTTPS Only**: Container must have SSL certificate
- **CORS Protection**: Only Static Web App can connect

## 📱 Usage

1. Visit your Static Web App URL
2. Enter access code: `tiktok-secure-2025`
3. Get full terminal access to your container!

## 🧪 Testing

### Test FastAPI
```bash
curl https://your-container.azurecontainerapps.io:8000/health
```

### Test ttyd Terminal
```bash
# Visit in browser:
https://your-container.azurecontainerapps.io:7681
```

## 🚨 Troubleshooting

### "Connection Failed"
- Check container is running
- Verify ports 8000 & 7681 are accessible
- Confirm WEBCLI_ACCESS_CODE matches

### "ttyd not found"
- Rebuild container image
- Check Dockerfile includes ttyd installation

### "Authentication Failed"
- Verify access code in container environment
- Check ttyd startup parameters

## 🔄 Rollback Plan

If ttyd doesn't work, temporary fallback:
1. Remove ttyd from startup script
2. Use FastAPI `/exec` endpoint for basic commands
3. Frontend sends commands via HTTP POST

## ✨ Benefits

- **Real Terminal**: Full bash shell access
- **No Middleware**: Direct connection = faster
- **Battle Tested**: ttyd used by major platforms
- **Simple**: Just add one binary to container 
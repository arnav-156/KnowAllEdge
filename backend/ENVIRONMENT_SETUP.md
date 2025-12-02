# 🔧 Environment Setup Guide

## ✅ Virtual Environment Created Successfully!

Your Python virtual environment has been set up at:
```
c:\Users\arnav\OneDrive\Desktop\KNOWALLEDGE-main\KNOWALLEDGE-main\backend\venv
```

---

## 📦 Installed Packages

The following packages have been installed in your virtual environment:
- ✅ Flask 3.0.2 (Web framework)
- ✅ Flask-Cors 4.0.0 (CORS handling)
- ✅ python-dotenv 1.0.1 (Environment variables)
- ✅ google-cloud-aiplatform 1.45.0 (Vertex AI)
- ✅ langchain-core 0.1.36 (LangChain framework)
- ✅ langchain-google-vertexai 0.1.2 (Gemini integration)
- ✅ Pillow 10.2.0 (Image processing)
- ✅ requests 2.31.0 (HTTP library)

---

## 🔑 IMPORTANT: Configure Your Credentials

### Step 1: Get Your Google Cloud Credentials

You need two values for the `.env` file:

#### 1. PROJECT_NAME (Your GCP Project ID)
```bash
# Find it in Google Cloud Console
# Or run: gcloud config get-value project
```

#### 2. ACCESS_TOKEN (GCP Access Token)
```bash
# Install Google Cloud SDK first: https://cloud.google.com/sdk/docs/install

# Then authenticate:
gcloud auth application-default login

# Generate access token:
gcloud auth application-default print-access-token
```

### Step 2: Edit .env File

The `.env` file should now be open in Notepad. Replace the placeholder values:

```bash
# Before:
PROJECT_NAME=your-gcp-project-id
ACCESS_TOKEN=your-access-token

# After (example):
PROJECT_NAME=KNOWALLEDGE-prod-12345
ACCESS_TOKEN=ya29.c.b0Aaekm1Jz...
```

**Note**: Access tokens expire after 1 hour. You'll need to regenerate them periodically during development.

---

## 🚀 Quick Start Commands

### Activate Virtual Environment (if not already active)
```powershell
# PowerShell
.\venv\Scripts\Activate.ps1

# CMD
venv\Scripts\activate.bat

# You'll see (venv) in your prompt when activated
```

### Run the Server
```bash
python main.py
```

### Test the API
```bash
# In a new terminal
python test_api.py
```

### Deactivate Virtual Environment
```bash
deactivate
```

---

## 🧪 Verify Your Setup

### 1. Check Python Environment
```bash
python --version
# Should show: Python 3.13.x
```

### 2. Check Installed Packages
```bash
pip list
# Should show all installed packages
```

### 3. Test API Health
```bash
# Start server first: python main.py
# Then in browser or curl:
http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T...",
  "cache_size": 0
}
```

---

## 📁 Project Structure

```
backend/
├── venv/                  # ✅ Virtual environment (created)
├── uploads/               # ✅ Image upload directory (created)
├── .env                   # ⚠️  Edit with your credentials
├── .env.example           # Template for environment variables
├── main.py                # Main Flask application
├── requirements.txt       # Python dependencies
├── test_api.py           # Test suite
├── setup.ps1             # PowerShell setup script
├── setup.bat             # Windows CMD setup script
├── Dockerfile            # Docker configuration
├── README.md             # API documentation
├── DEPLOYMENT.md         # Deployment guide
└── IMPROVEMENTS.md       # Changes log
```

---

## 🔧 Troubleshooting

### Issue: "venv\Scripts\Activate.ps1 cannot be loaded"
**Solution**: Enable script execution in PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: "ModuleNotFoundError"
**Solution**: Make sure virtual environment is activated
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue: "gcloud command not found"
**Solution**: Install Google Cloud SDK
- Download from: https://cloud.google.com/sdk/docs/install
- Restart terminal after installation

### Issue: Access token expired
**Solution**: Generate a new token
```bash
gcloud auth application-default print-access-token
# Copy the new token to .env file
```

### Issue: Port 5000 already in use
**Solution**: Stop other services or change port
```python
# In main.py, change the port:
app.run(host='0.0.0.0', port=5001, ...)
```

---

## 🎯 Next Steps

### 1. Configure Credentials (Required)
```
✅ Created virtual environment
✅ Installed dependencies
⏳ Edit .env with GCP credentials  <-- DO THIS NOW
```

### 2. Test Backend (5 minutes)
```bash
python test_api.py
```

### 3. Start Development
```bash
python main.py
```
Then visit: http://localhost:5000/api/docs

### 4. Update Frontend
See: `../FRONTEND_MIGRATION.md`

---

## 💡 Pro Tips

1. **Keep Virtual Environment Activated**: Always activate before working
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Token Refresh**: Create a script to auto-refresh access token
   ```powershell
   # refresh_token.ps1
   $token = gcloud auth application-default print-access-token
   (Get-Content .env) -replace 'ACCESS_TOKEN=.*', "ACCESS_TOKEN=$token" | Set-Content .env
   ```

3. **Quick Start**: Add to your PowerShell profile
   ```powershell
   function Start-KNOWALLEDGE {
       cd "C:\Users\arnav\OneDrive\Desktop\KNOWALLEDGE-main\KNOWALLEDGE-main\backend"
       .\venv\Scripts\Activate.ps1
       python main.py
   }
   ```

4. **Monitor Logs**: Watch the log file in real-time
   ```powershell
   Get-Content app.log -Wait -Tail 50
   ```

5. **View Metrics**: Check system health
   ```
   http://localhost:5000/api/metrics
   ```

---

## 📚 Additional Resources

### Documentation
- **Backend README**: `README.md` - Complete API documentation
- **Deployment Guide**: `DEPLOYMENT.md` - Production deployment
- **Quick Start**: `../QUICK_START.md` - Step-by-step guide

### Google Cloud Resources
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Guide](https://ai.google.dev/docs)
- [Cloud SDK Installation](https://cloud.google.com/sdk/docs/install)

### Flask Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-CORS](https://flask-cors.readthedocs.io/)

---

## ✅ Setup Complete!

Your development environment is ready! Follow these steps:

1. ⚠️  **Edit `.env` file** with your GCP credentials (Notepad should be open)
2. 🧪 **Test**: Run `python test_api.py`
3. 🚀 **Start**: Run `python main.py`
4. 🌐 **Access**: Visit `http://localhost:5000/api/health`

---

**Environment Status**: ✅ Ready for Development
**Python Version**: 3.13.5
**Virtual Environment**: Activated
**Dependencies**: Installed
**Next Action**: Configure GCP credentials in `.env`
